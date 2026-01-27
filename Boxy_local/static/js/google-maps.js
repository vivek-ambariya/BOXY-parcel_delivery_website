/**
 * Google Maps Integration for Boxy Parcel Delivery
 * Provides: Address Autocomplete, Map Visualization, Route Display
 */

// Global variables
let googleMapsLoaded = false;
let autocompleteInstances = [];
let mapInstances = [];

// Initialize Google Maps when script loads (called by Google Maps API callback)
window.initGoogleMaps = function() {
    googleMapsLoaded = true;
    console.log('Google Maps API loaded successfully');
    
    // Initialize autocomplete for all address inputs
    initAddressAutocomplete();
    
    // Initialize any existing maps
    initMaps();
};

// Initialize address autocomplete for all address input fields
function initAddressAutocomplete() {
    if (!googleMapsLoaded || typeof google === 'undefined') {
        console.warn('Google Maps API not loaded yet');
        return;
    }
    
    // Find all address input fields
    const addressInputs = document.querySelectorAll('.stop-address, input[type="text"][placeholder*="address" i]');
    
    addressInputs.forEach((input, index) => {
        // Skip if already initialized
        if (input.dataset.autocompleteInitialized === 'true') {
            return;
        }
        
        // Create autocomplete instance
        const autocomplete = new google.maps.places.Autocomplete(input, {
            types: ['address'],
            componentRestrictions: { country: 'in' }, // Restrict to India
            fields: ['formatted_address', 'geometry', 'address_components']
        });
        
        // Store autocomplete instance
        autocompleteInstances.push(autocomplete);
        input.dataset.autocompleteInitialized = 'true';
        
        // Add place changed listener
        autocomplete.addListener('place_changed', function() {
            const place = autocomplete.getPlace();
            if (place.geometry) {
                // Address selected, trigger cost update if needed
                if (typeof updateEstimatedCost === 'function') {
                    updateEstimatedCost();
                }
            }
        });
    });
    
    // Also initialize for dynamically added inputs
    observeNewAddressInputs();
}

// Observe for dynamically added address inputs
function observeNewAddressInputs() {
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) { // Element node
                    const addressInputs = node.querySelectorAll ? 
                        node.querySelectorAll('.stop-address, input[type="text"][placeholder*="address" i]') : [];
                    addressInputs.forEach(input => {
                        if (input.dataset.autocompleteInitialized !== 'true') {
                            initAddressAutocomplete();
                        }
                    });
                }
            });
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

// Initialize maps
function initMaps() {
    if (!googleMapsLoaded || typeof google === 'undefined') {
        return;
    }
    
    // Initialize tracking map if element exists
    const trackingMapElement = document.getElementById('trackingMap');
    if (trackingMapElement && !trackingMapElement.dataset.mapInitialized) {
        initTrackingMap();
    }
    
    // Initialize partner navigation map if element exists
    const partnerMapElement = document.getElementById('partnerNavigationMap');
    if (partnerMapElement && !partnerMapElement.dataset.mapInitialized) {
        initPartnerNavigationMap();
    }
}

// Initialize tracking map
function initTrackingMap() {
    const mapElement = document.getElementById('trackingMap');
    if (!mapElement || mapElement.dataset.mapInitialized === 'true') {
        return;
    }
    
    // Default center (India)
    const defaultCenter = { lat: 20.5937, lng: 78.9629 };
    
    const map = new google.maps.Map(mapElement, {
        zoom: 6,
        center: defaultCenter,
        mapTypeControl: true,
        streetViewControl: false,
        fullscreenControl: true
    });
    
    mapElement.dataset.mapInitialized = 'true';
    mapInstances.push({ id: 'trackingMap', map: map, markers: [], directionsRenderer: null });
    
    // Store map reference for later use
    window.trackingMap = map;
}

// Display delivery locations on tracking map
function displayTrackingMap(senderAddress, receiverAddress, stops = []) {
    if (!window.trackingMap) {
        initTrackingMap();
    }
    
    const map = window.trackingMap;
    const mapData = mapInstances.find(m => m.id === 'trackingMap');
    
    if (!mapData) return;
    
    // Clear existing markers
    mapData.markers.forEach(marker => marker.setMap(null));
    mapData.markers = [];
    
    // Geocode addresses and add markers
    const geocoder = new google.maps.Geocoder();
    const bounds = new google.maps.LatLngBounds();
    const locations = [];
    
    // Add sender location
    if (senderAddress) {
        geocoder.geocode({ address: senderAddress }, (results, status) => {
            if (status === 'OK' && results[0]) {
                const position = results[0].geometry.location;
                const marker = new google.maps.Marker({
                    position: position,
                    map: map,
                    title: 'Pickup Location',
                    icon: {
                        url: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
                    },
                    label: 'P'
                });
                
                const infoWindow = new google.maps.InfoWindow({
                    content: `<strong>Pickup Location</strong><br>${senderAddress}`
                });
                
                marker.addListener('click', () => {
                    infoWindow.open(map, marker);
                });
                
                mapData.markers.push(marker);
                bounds.extend(position);
                locations.push({ position, address: senderAddress, type: 'pickup' });
                
                // If single delivery, add receiver
                if (!stops || stops.length === 0) {
                    if (receiverAddress) {
                        geocoder.geocode({ address: receiverAddress }, (results, status) => {
                            if (status === 'OK' && results[0]) {
                                const position = results[0].geometry.location;
                                const marker = new google.maps.Marker({
                                    position: position,
                                    map: map,
                                    title: 'Delivery Location',
                                    icon: {
                                        url: 'http://maps.google.com/mapfiles/ms/icons/green-dot.png'
                                    },
                                    label: 'D'
                                });
                                
                                const infoWindow = new google.maps.InfoWindow({
                                    content: `<strong>Delivery Location</strong><br>${receiverAddress}`
                                });
                                
                                marker.addListener('click', () => {
                                    infoWindow.open(map, marker);
                                });
                                
                                mapData.markers.push(marker);
                                bounds.extend(position);
                                
                                // Draw route
                                drawRoute(map, locations[0].position, position);
                                
                                // Fit bounds
                                map.fitBounds(bounds);
                            }
                        });
                    }
                } else {
                    // Multi-stop delivery
                    let stopIndex = 0;
                    stops.forEach((stop, index) => {
                        if (stop.drop_address) {
                            geocoder.geocode({ address: stop.drop_address }, (results, status) => {
                                if (status === 'OK' && results[0]) {
                                    const position = results[0].geometry.location;
                                    const marker = new google.maps.Marker({
                                        position: position,
                                        map: map,
                                        title: `Stop ${stop.stop_number || index + 1}`,
                                        icon: {
                                            url: 'http://maps.google.com/mapfiles/ms/icons/yellow-dot.png'
                                        },
                                        label: String(stop.stop_number || index + 1)
                                    });
                                    
                                    const infoWindow = new google.maps.InfoWindow({
                                        content: `<strong>Stop ${stop.stop_number || index + 1}</strong><br>${stop.drop_address}<br>Receiver: ${stop.receiver_name || ''}`
                                    });
                                    
                                    marker.addListener('click', () => {
                                        infoWindow.open(map, marker);
                                    });
                                    
                                    mapData.markers.push(marker);
                                    bounds.extend(position);
                                    locations.push({ position, address: stop.drop_address, type: 'stop', stopNumber: stop.stop_number || index + 1 });
                                    
                                    stopIndex++;
                                    
                                    // If all stops loaded, draw route
                                    if (stopIndex === stops.length) {
                                        drawMultiStopRoute(map, locations);
                                        map.fitBounds(bounds);
                                    }
                                }
                            });
                        }
                    });
                }
            }
        });
    }
}

// Draw route between two points
function drawRoute(map, origin, destination) {
    const directionsService = new google.maps.DirectionsService();
    const directionsRenderer = new google.maps.DirectionsRenderer({
        map: map,
        suppressMarkers: true
    });
    
    directionsService.route({
        origin: origin,
        destination: destination,
        travelMode: google.maps.TravelMode.DRIVING
    }, (result, status) => {
        if (status === 'OK') {
            directionsRenderer.setDirections(result);
        }
    });
}

// Draw route for multi-stop delivery
function drawMultiStopRoute(map, locations) {
    if (locations.length < 2) return;
    
    const directionsService = new google.maps.DirectionsService();
    const directionsRenderer = new google.maps.DirectionsRenderer({
        map: map,
        suppressMarkers: true
    });
    
    // Sort locations: pickup first, then stops
    locations.sort((a, b) => {
        if (a.type === 'pickup') return -1;
        if (b.type === 'pickup') return 1;
        return (a.stopNumber || 0) - (b.stopNumber || 0);
    });
    
    const waypoints = locations.slice(1, -1).map(loc => ({
        location: loc.position,
        stopover: true
    }));
    
    directionsService.route({
        origin: locations[0].position,
        destination: locations[locations.length - 1].position,
        waypoints: waypoints,
        travelMode: google.maps.TravelMode.DRIVING,
        optimizeWaypoints: true
    }, (result, status) => {
        if (status === 'OK') {
            directionsRenderer.setDirections(result);
        }
    });
}

// Initialize partner navigation map
function initPartnerNavigationMap() {
    const mapElement = document.getElementById('partnerNavigationMap');
    if (!mapElement || mapElement.dataset.mapInitialized === 'true') {
        return;
    }
    
    // Try to get user's current location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                const map = new google.maps.Map(mapElement, {
                    zoom: 13,
                    center: userLocation,
                    mapTypeControl: true,
                    streetViewControl: false,
                    fullscreenControl: true
                });
                
                // Add user location marker
                const userMarker = new google.maps.Marker({
                    position: userLocation,
                    map: map,
                    title: 'Your Location',
                    icon: {
                        url: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
                    }
                });
                
                mapElement.dataset.mapInitialized = 'true';
                mapInstances.push({ 
                    id: 'partnerNavigationMap', 
                    map: map, 
                    markers: [userMarker], 
                    directionsRenderer: null 
                });
                
                window.partnerNavigationMap = map;
            },
            () => {
                // Default to India center if geolocation fails
                const defaultCenter = { lat: 20.5937, lng: 78.9629 };
                const map = new google.maps.Map(mapElement, {
                    zoom: 6,
                    center: defaultCenter,
                    mapTypeControl: true,
                    streetViewControl: false,
                    fullscreenControl: true
                });
                
                mapElement.dataset.mapInitialized = 'true';
                mapInstances.push({ 
                    id: 'partnerNavigationMap', 
                    map: map, 
                    markers: [], 
                    directionsRenderer: null 
                });
                
                window.partnerNavigationMap = map;
            }
        );
    } else {
        // Default to India center if geolocation not supported
        const defaultCenter = { lat: 20.5937, lng: 78.9629 };
        const map = new google.maps.Map(mapElement, {
            zoom: 6,
            center: defaultCenter,
            mapTypeControl: true,
            streetViewControl: false,
            fullscreenControl: true
        });
        
        mapElement.dataset.mapInitialized = 'true';
        mapInstances.push({ 
            id: 'partnerNavigationMap', 
            map: map, 
            markers: [], 
            directionsRenderer: null 
        });
        
        window.partnerNavigationMap = map;
    }
}

// Display route for partner navigation
function displayPartnerRoute(pickupAddress, deliveryAddresses = []) {
    if (!window.partnerNavigationMap) {
        initPartnerNavigationMap();
        // Wait a bit for map to initialize
        setTimeout(() => displayPartnerRoute(pickupAddress, deliveryAddresses), 500);
        return;
    }
    
    const map = window.partnerNavigationMap;
    const mapData = mapInstances.find(m => m.id === 'partnerNavigationMap');
    
    if (!mapData) return;
    
    // Clear existing markers except user location
    mapData.markers.forEach((marker, index) => {
        if (index > 0) { // Keep first marker (user location)
            marker.setMap(null);
        }
    });
    mapData.markers = mapData.markers.slice(0, 1); // Keep only user location
    
    // Clear existing directions
    if (mapData.directionsRenderer) {
        mapData.directionsRenderer.setMap(null);
    }
    
    const geocoder = new google.maps.Geocoder();
    const bounds = new google.maps.LatLngBounds();
    const locations = [];
    
    // Geocode pickup address
    if (pickupAddress) {
        geocoder.geocode({ address: pickupAddress }, (results, status) => {
            if (status === 'OK' && results[0]) {
                const position = results[0].geometry.location;
                const marker = new google.maps.Marker({
                    position: position,
                    map: map,
                    title: 'Pickup Location',
                    icon: {
                        url: 'http://maps.google.com/mapfiles/ms/icons/red-dot.png'
                    },
                    label: 'P'
                });
                
                mapData.markers.push(marker);
                bounds.extend(position);
                locations.push({ position, address: pickupAddress, type: 'pickup' });
                
                // Geocode delivery addresses
                if (deliveryAddresses.length === 0) {
                    // Single delivery - draw route from user to pickup to delivery
                    // This would need delivery address from the delivery data
                } else {
                    // Multi-stop - geocode all stops
                    let geocodeCount = 0;
                    deliveryAddresses.forEach((address, index) => {
                        geocoder.geocode({ address: address }, (results, status) => {
                            if (status === 'OK' && results[0]) {
                                const position = results[0].geometry.location;
                                const marker = new google.maps.Marker({
                                    position: position,
                                    map: map,
                                    title: `Stop ${index + 1}`,
                                    icon: {
                                        url: 'http://maps.google.com/mapfiles/ms/icons/green-dot.png'
                                    },
                                    label: String(index + 1)
                                });
                                
                                mapData.markers.push(marker);
                                bounds.extend(position);
                                locations.push({ position, address: address, type: 'stop', stopNumber: index + 1 });
                                
                                geocodeCount++;
                                
                                // When all geocoded, draw route
                                if (geocodeCount === deliveryAddresses.length) {
                                    drawMultiStopRoute(map, locations);
                                    map.fitBounds(bounds);
                                }
                            }
                        });
                    });
                }
            }
        });
    }
}

// Export functions for use in other scripts
window.GoogleMapsUtils = {
    init: initGoogleMaps,
    initAutocomplete: initAddressAutocomplete,
    displayTrackingMap: displayTrackingMap,
    displayPartnerRoute: displayPartnerRoute,
    initTrackingMap: initTrackingMap,
    initPartnerNavigationMap: initPartnerNavigationMap
};
