// Partner Dashboard JavaScript

let currentPartner = null;
let deliveryRefreshInterval = null;
let isLive = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
    setupEventListeners();
});

// Check if partner is already logged in
function checkLoginStatus() {
    // In a real app, this would check session/cookies
    // For demo, we'll check localStorage
    const savedPartner = localStorage.getItem('currentPartner');
    if (savedPartner) {
        currentPartner = JSON.parse(savedPartner);
        isLive = currentPartner.status === 'online';
        showDashboard();
    }
}

// Setup event listeners
function setupEventListeners() {
    // Registration form
    document.getElementById('partnerRegisterForm').addEventListener('submit', handleRegister);
    
    // Login form
    document.getElementById('partnerLoginForm').addEventListener('submit', handleLogin);
    
    // Logout button
    document.getElementById('partnerLogoutBtn').addEventListener('click', handleLogout);
    
    // Status toggle
    document.querySelectorAll('input[name="statusToggle"]').forEach(radio => {
        radio.addEventListener('change', handleStatusChange);
    });
}

// Handle partner registration
async function handleRegister(e) {
    e.preventDefault();
    
    const form = e.target;
    const password = document.getElementById('partnerPassword').value;
    const confirmPassword = document.getElementById('partnerConfirmPassword').value;
    
    if (password !== confirmPassword) {
        alert('Passwords do not match!');
        return;
    }
    
    const formData = {
        firstName: document.getElementById('partnerFirstName').value,
        lastName: document.getElementById('partnerLastName').value,
        phone: document.getElementById('partnerPhone').value,
        email: document.getElementById('partnerEmail').value,
        vehicleType: document.getElementById('partnerVehicle').value,
        vehicleNumber: document.getElementById('partnerVehicleNumber').value,
        aadhar: document.getElementById('partnerAadhar').value,
        password: password
    };
    
    try {
        const response = await fetch('/api/partner/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('registerSuccess').classList.remove('d-none');
            form.reset();
            
            // Auto switch to login tab after 2 seconds
            setTimeout(() => {
                document.getElementById('login-tab').click();
            }, 2000);
        } else {
            alert('Registration failed: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('Registration failed. Please try again.');
    }
}

// Handle partner login
async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch('/api/partner/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include', // Include cookies for session
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentPartner = data.partner;
            isLive = data.partner.status === 'online';
            localStorage.setItem('currentPartner', JSON.stringify(currentPartner));
            showDashboard();
            updateGoLiveUI();
        } else {
            document.getElementById('loginError').classList.remove('d-none');
            document.getElementById('loginErrorMsg').textContent = data.message || 'Invalid credentials';
        }
    } catch (error) {
        console.error('Login error:', error);
        document.getElementById('loginError').classList.remove('d-none');
        document.getElementById('loginErrorMsg').textContent = 'Login failed. Please try again.';
    }
}

// Handle logout
async function handleLogout() {
    try {
        await fetch('/api/partner/logout', {
            method: 'POST',
            credentials: 'include' // Include cookies for session
        });
        
        localStorage.removeItem('currentPartner');
        currentPartner = null;
        
        if (deliveryRefreshInterval) {
            clearInterval(deliveryRefreshInterval);
            deliveryRefreshInterval = null;
        }
        
        hideDashboard();
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Toggle Go Live status
async function toggleGoLive() {
    if (!currentPartner) {
        alert('Please login first');
        return;
    }
    
    const newStatus = isLive ? 'offline' : 'online';
    
    try {
        const response = await fetch('/api/partner/status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include', // Include cookies for session
            body: JSON.stringify({ status: newStatus })
        });
        
        const data = await response.json();
        
        if (data.success) {
            isLive = !isLive;
            currentPartner.status = newStatus;
            localStorage.setItem('currentPartner', JSON.stringify(currentPartner));
            
            // Update UI
            updateGoLiveUI();
            
            // Show modal if going live
            if (isLive) {
                const modalElement = document.getElementById('goLiveModal');
                if (modalElement) {
                    const modal = new bootstrap.Modal(modalElement);
                    modal.show();
                }
            }
            
            // Load deliveries and manage auto-refresh
            if (isLive) {
                loadDeliveries();
                // Start auto-refresh every 5 seconds when online
                if (!deliveryRefreshInterval) {
                    deliveryRefreshInterval = setInterval(loadDeliveries, 5000);
                }
            } else {
                // Stop auto-refresh when offline
                if (deliveryRefreshInterval) {
                    clearInterval(deliveryRefreshInterval);
                    deliveryRefreshInterval = null;
                }
            }
        } else {
            alert('Failed to update status: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Go Live toggle error:', error);
        alert('Failed to update status. Please try again.');
    }
}

// Update Go Live button UI
function updateGoLiveUI() {
    const goLiveBtn = document.getElementById('goLiveBtn');
    const liveStatusBtn = document.getElementById('liveStatusBtn');
    const goLiveArrow = document.getElementById('goLiveArrow');
    const offlineMessage = document.getElementById('offlineMessage');
    const lookingForDeliveries = document.getElementById('lookingForDeliveries');
    const newDeliveryBar = document.getElementById('newDeliveryBar');
    
    if (!goLiveBtn) return;
    
    if (isLive) {
        // Hide "Tap to Go Live" button, show "You are LIVE" button
        goLiveBtn.style.display = 'none';
        if (liveStatusBtn) {
            liveStatusBtn.style.display = 'inline-block';
        }
        if (goLiveArrow) goLiveArrow.style.display = 'inline-block';
        if (offlineMessage) offlineMessage.style.display = 'none';
        if (newDeliveryBar) newDeliveryBar.classList.remove('d-none');
    } else {
        // Show "Tap to Go Live" button, hide "You are LIVE" button
        goLiveBtn.style.display = 'inline-block';
        if (liveStatusBtn) {
            liveStatusBtn.style.display = 'none';
        }
        if (goLiveArrow) goLiveArrow.style.display = 'none';
        if (offlineMessage) offlineMessage.style.display = 'block';
        if (lookingForDeliveries) lookingForDeliveries.classList.add('d-none');
        if (newDeliveryBar) newDeliveryBar.classList.add('d-none');
    }
}

// Show dashboard
function showDashboard() {
    document.getElementById('authSection').classList.add('d-none');
    document.getElementById('benefitsSection').classList.add('d-none');
    document.getElementById('pageHeader').classList.add('d-none');
    document.getElementById('partnerDashboard').classList.remove('d-none');
    
    // Update partner info
    const partnerNameEl = document.getElementById('partnerName');
    const partnerIdEl = document.getElementById('partnerId');
    if (partnerNameEl) {
        partnerNameEl.textContent = currentPartner.first_name ? 
            `${currentPartner.first_name} ${currentPartner.last_name}` : 
            currentPartner.name || 'Demo Partner';
    }
    if (partnerIdEl && currentPartner.id) {
        partnerIdEl.textContent = `ID: ${currentPartner.id}`;
    }
    
    // Set initial live status
    isLive = currentPartner.status === 'online';
    updateGoLiveUI();
    
    loadDeliveries();
}

// Hide dashboard
function hideDashboard() {
    document.getElementById('authSection').classList.remove('d-none');
    document.getElementById('benefitsSection').classList.remove('d-none');
    document.getElementById('pageHeader').classList.remove('d-none');
    document.getElementById('partnerDashboard').classList.add('d-none');
    
    document.getElementById('partnerLoginForm').reset();
    document.getElementById('loginError').classList.add('d-none');
}

// Load deliveries
async function loadDeliveries() {
    if (!currentPartner) return;
    
    try {
        const response = await fetch('/api/partner/deliveries', {
            credentials: 'include' // Include cookies for session
        });
        const data = await response.json();
        
        if (data.success) {
            displayAvailableDeliveries(data.available_deliveries);
            displayMyDeliveries(data.my_deliveries);
            updateStats(data.my_deliveries);
        }
    } catch (error) {
        console.error('Load deliveries error:', error);
    }
}

// Display available deliveries
function displayAvailableDeliveries(deliveries) {
    const container = document.getElementById('availableDeliveriesList');
    const offlineMessage = document.getElementById('offlineMessage');
    const lookingForDeliveries = document.getElementById('lookingForDeliveries');
    const newDeliveryBar = document.getElementById('newDeliveryBar');
    const newDeliveryCount = document.getElementById('newDeliveryCount');
    
    // Update new delivery count
    if (newDeliveryCount && deliveries) {
        newDeliveryCount.textContent = deliveries.length;
    }
    
    // Hide offline message if live
    if (isLive && offlineMessage) {
        offlineMessage.style.display = 'none';
    }
    
    if (!deliveries || deliveries.length === 0) {
        if (isLive) {
            // Show "Looking for deliveries..." message when live but no deliveries
            if (offlineMessage) offlineMessage.style.display = 'none';
            if (lookingForDeliveries) {
                lookingForDeliveries.classList.remove('d-none');
            }
            // Clear container and show looking message
            const existingCards = container.querySelectorAll('.delivery-card');
            existingCards.forEach(card => card.remove());
        } else {
            // Show offline message when not live
            if (offlineMessage) offlineMessage.style.display = 'block';
            if (lookingForDeliveries) lookingForDeliveries.classList.add('d-none');
        }
        return;
    }
    
    // Hide both offline and looking messages when showing deliveries
    if (offlineMessage) offlineMessage.style.display = 'none';
    if (lookingForDeliveries) lookingForDeliveries.classList.add('d-none');
    
    // Remove looking for deliveries message if it exists
    if (lookingForDeliveries) {
        lookingForDeliveries.classList.add('d-none');
    }
    
    // Clear existing delivery cards but keep offline/looking messages
    const existingCards = container.querySelectorAll('.delivery-card');
    existingCards.forEach(card => card.remove());
    
    // Add delivery cards
    deliveries.forEach(delivery => {
        let stopsInfo = '';
        if (delivery.total_stops > 1 && delivery.stops) {
            stopsInfo = `<br><strong>Stops:</strong> ${delivery.total_stops} locations`;
        }
        const deliveryCard = `
        <div class="delivery-card card mb-3">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h6 class="mb-2">
                            <i class="fas fa-box me-2"></i>${delivery.id}
                            ${delivery.total_stops > 1 ? `<span class="badge bg-info ms-2">${delivery.total_stops} Stops</span>` : ''}
                        </h6>
                        <p class="mb-1">
                            <strong>From:</strong> ${delivery.sender_address}<br>
                            ${delivery.total_stops === 1 ? `<strong>To:</strong> ${delivery.receiver_address}` : `<strong>Total Stops:</strong> ${delivery.total_stops}`}
                            ${stopsInfo}
                        </p>
                        <p class="mb-0 text-muted small">
                            <i class="fas fa-weight me-1"></i>${delivery.weight} kg | 
                            <i class="fas fa-tag me-1"></i>${delivery.parcel_type}
                        </p>
                    </div>
                    <div class="col-md-4 text-end">
                        <button class="btn btn-primary btn-sm" onclick="acceptDelivery('${delivery.id}')">
                            <i class="fas fa-check me-1"></i>Accept
                        </button>
                    </div>
                </div>
            </div>
        </div>
        `;
        container.insertAdjacentHTML('beforeend', deliveryCard);
    });
}

// Display my deliveries
function displayMyDeliveries(deliveries) {
    const activeContainer = document.getElementById('activeDeliveriesList');
    const completedContainer = document.getElementById('completedDeliveriesList');
    
    if (!deliveries || deliveries.length === 0) {
        activeContainer.innerHTML = '<p class="text-muted text-center">No active deliveries.</p>';
        completedContainer.innerHTML = '<p class="text-muted text-center">No completed deliveries yet.</p>';
        return;
    }
    
    const active = deliveries.filter(d => d.status !== 'delivered');
    const completed = deliveries.filter(d => d.status === 'delivered');
    
    // Active deliveries
    if (active.length === 0) {
        activeContainer.innerHTML = '<p class="text-muted text-center">No active deliveries.</p>';
    } else {
        activeContainer.innerHTML = active.map(delivery => createDeliveryCard(delivery)).join('');
    }
    
    // Completed deliveries
    if (completed.length === 0) {
        completedContainer.innerHTML = '<p class="text-muted text-center">No completed deliveries yet.</p>';
    } else {
        completedContainer.innerHTML = completed.map(delivery => createDeliveryCard(delivery, true)).join('');
    }
}

// Create delivery card
function createDeliveryCard(delivery, isCompleted = false) {
    const statusBadges = {
        'accepted': '<span class="badge bg-info">Accepted</span>',
        'picked': '<span class="badge bg-primary">Picked Up</span>',
        'on_the_way': '<span class="badge bg-warning">On the Way</span>',
        'delivered': '<span class="badge bg-success">Delivered</span>'
    };
    
    const statusButtons = !isCompleted ? `
        <div class="btn-group btn-group-sm" role="group">
            ${delivery.status === 'accepted' ? `
                <button class="btn btn-primary" onclick="updateDeliveryStatus('${delivery.id}', 'picked')">
                    <i class="fas fa-hand-paper me-1"></i>Mark as Picked
                </button>
            ` : ''}
            ${delivery.status === 'picked' ? `
                <button class="btn btn-warning" onclick="updateDeliveryStatus('${delivery.id}', 'on_the_way')">
                    <i class="fas fa-truck me-1"></i>On the Way
                </button>
            ` : ''}
        </div>
    ` : '';
    
    // Multi-stop display
    let stopsHtml = '';
    if (delivery.total_stops > 1 && delivery.stops) {
        stopsHtml = '<div class="mt-3"><strong>Delivery Stops:</strong><div class="mt-2">';
        delivery.stops.forEach(stop => {
            const stopStatus = stop.status === 'delivered' ? 'success' : 'warning';
            const stopIcon = stop.status === 'delivered' ? 'fa-check-circle' : 'fa-clock';
            stopsHtml += `
                <div class="stop-progress-item ${stop.status === 'delivered' ? 'delivered' : 'pending'} mb-2">
                    <div class="stop-progress-number">${stop.stop_number}</div>
                    <div class="stop-progress-content">
                        <strong>Stop ${stop.stop_number}: ${stop.receiver_name}</strong>
                        <p class="mb-0 text-muted small">${stop.drop_address}</p>
                        <p class="mb-0 text-muted small">Phone: ${stop.receiver_phone}</p>
                    </div>
                    <div class="stop-progress-status">
                        ${stop.status === 'delivered' ? 
                            '<span class="badge bg-success"><i class="fas fa-check me-1"></i>Delivered</span>' :
                            `<button class="btn btn-sm btn-success" onclick="deliverStop('${delivery.id}', ${stop.stop_number})">
                                <i class="fas fa-check me-1"></i>Mark Delivered
                            </button>`
                        }
                    </div>
                </div>
            `;
        });
        stopsHtml += '</div></div>';
    }
    
    return `
        <div class="delivery-card card mb-3">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h6 class="mb-2">
                            <i class="fas fa-box me-2"></i>${delivery.id}
                            ${delivery.total_stops > 1 ? `<span class="badge bg-info ms-2">${delivery.total_stops} Stops</span>` : ''}
                        </h6>
                        <p class="mb-1">
                            <strong>From:</strong> ${delivery.sender_address}<br>
                            ${delivery.total_stops === 1 ? `
                                <strong>To:</strong> ${delivery.receiver_address}<br>
                                <strong>Receiver:</strong> ${delivery.receiver_name} (${delivery.receiver_phone})
                            ` : `<strong>Total Stops:</strong> ${delivery.total_stops}`}
                        </p>
                        <p class="mb-0 text-muted small">
                            <i class="fas fa-weight me-1"></i>${delivery.weight} kg | 
                            <i class="fas fa-tag me-1"></i>${delivery.parcel_type}
                        </p>
                        ${stopsHtml}
                    </div>
                    <div class="col-md-4 text-end">
                        ${statusBadges[delivery.status] || '<span class="badge bg-secondary">' + delivery.status + '</span>'}
                        ${statusButtons}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Deliver a specific stop
async function deliverStop(deliveryId, stopNumber) {
    if (!currentPartner) return;
    
    try {
        const response = await fetch('/api/partner/deliver-stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include', // Include cookies for session
            body: JSON.stringify({ 
                delivery_id: deliveryId,
                stop_number: stopNumber
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`Stop ${stopNumber} marked as delivered!`);
            loadDeliveries();
        } else {
            alert('Failed to mark stop as delivered: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Deliver stop error:', error);
        alert('Failed to mark stop as delivered. Please try again.');
    }
}

// Accept delivery
async function acceptDelivery(deliveryId) {
    if (!currentPartner) return;
    
    try {
        const response = await fetch('/api/partner/accept-delivery', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include', // Include cookies for session
            body: JSON.stringify({ delivery_id: deliveryId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Delivery accepted successfully!');
            loadDeliveries();
        } else {
            alert('Failed to accept delivery: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Accept delivery error:', error);
        alert('Failed to accept delivery. Please try again.');
    }
}

// Update delivery status
async function updateDeliveryStatus(deliveryId, newStatus) {
    if (!currentPartner) return;
    
    try {
        const response = await fetch('/api/partner/update-status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include', // Include cookies for session
            body: JSON.stringify({ 
                delivery_id: deliveryId,
                status: newStatus
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            loadDeliveries();
            
            if (newStatus === 'delivered') {
                alert('Delivery marked as delivered! Great job!');
            }
        } else {
            alert('Failed to update status: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Update status error:', error);
        alert('Failed to update status. Please try again.');
    }
}

// Update stats
function updateStats(deliveries) {
    if (!deliveries) return;
    
    const completed = deliveries.filter(d => d.status === 'delivered').length;
    const inProgress = deliveries.filter(d => d.status !== 'delivered' && d.status !== 'available').length;
    const available = deliveries.filter(d => d.status === 'available').length;
    
    // Update today's earnings (simple calculation: ₹50 per completed delivery)
    const todayEarnings = completed * 50;
    const todayEarningsEl = document.getElementById('todayEarnings');
    if (todayEarningsEl) {
        todayEarningsEl.textContent = `₹${todayEarnings}`;
    }
    
    const completedEl = document.getElementById('completedDeliveries');
    const inProgressEl = document.getElementById('inProgressDeliveries');
    if (completedEl) completedEl.textContent = completed;
    if (inProgressEl) inProgressEl.textContent = inProgress;
    
    const availableCountEl = document.getElementById('availableCount');
    if (availableCountEl) {
        availableCountEl.textContent = available;
    }
    
    // Update badge counts
    const activeCountBadge = document.getElementById('activeCountBadge');
    const completedCountBadge = document.getElementById('completedCountBadge');
    if (activeCountBadge) activeCountBadge.textContent = inProgress;
    if (completedCountBadge) completedCountBadge.textContent = completed;
}

// Make functions globally available
window.acceptDelivery = acceptDelivery;
window.updateDeliveryStatus = updateDeliveryStatus;
window.loadDeliveries = loadDeliveries;
window.deliverStop = deliverStop;
window.toggleGoLive = toggleGoLive;

