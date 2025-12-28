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
async function checkLoginStatus() {
    // Check localStorage first
    const savedPartner = localStorage.getItem('currentPartner');
    if (savedPartner) {
        currentPartner = JSON.parse(savedPartner);
        // Fetch current status from server to ensure it's up to date
        try {
            const response = await fetch('/api/partner/status', {
                method: 'GET',
                credentials: 'include'
            });
            const data = await response.json();
            if (data.success) {
                // Update status from server
                isLive = data.status === 'online';
                currentPartner.status = data.status;
                localStorage.setItem('currentPartner', JSON.stringify(currentPartner));
            }
        } catch (error) {
            console.error('Error fetching status:', error);
            // Fallback to localStorage status
            isLive = currentPartner.status === 'online';
        }
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
    console.log('Toggle Go Live: Current status:', isLive, 'New status:', newStatus);
    
    try {
        // Update status on server
        const response = await fetch('/api/partner/status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include', // Include cookies for session
            body: JSON.stringify({ status: newStatus })
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            throw new Error(`Server error: ${response.status} - ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (data.success) {
            // Update local state
            isLive = newStatus === 'online';
            currentPartner.status = newStatus;
            localStorage.setItem('currentPartner', JSON.stringify(currentPartner));
            
            // Verify status was updated by fetching it again
            const verifyResponse = await fetch('/api/partner/status', {
                method: 'GET',
                credentials: 'include'
            });
            
            if (!verifyResponse.ok) {
                console.warn('Failed to verify status, but update may have succeeded');
            } else {
                const verifyData = await verifyResponse.json();
                console.log('Verified status:', verifyData);
                
                if (verifyData.success) {
                    // Use the verified status from server
                    isLive = verifyData.status === 'online';
                    currentPartner.status = verifyData.status;
                    localStorage.setItem('currentPartner', JSON.stringify(currentPartner));
                }
            }
            
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
                // Clear available deliveries when going offline
                const availableList = document.getElementById('availableDeliveriesList');
                if (availableList) {
                    const offlineMsg = document.getElementById('offlineMessage');
                    const lookingMsg = document.getElementById('lookingForDeliveries');
                    if (offlineMsg) offlineMsg.style.display = 'block';
                    if (lookingMsg) lookingMsg.style.display = 'none';
                    // Remove any delivery cards
                    const deliveryCards = availableList.querySelectorAll('.delivery-card');
                    deliveryCards.forEach(card => card.remove());
                }
            }
        } else {
            console.error('Update failed:', data.message);
            alert('Failed to update status: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Go Live toggle error:', error);
        alert('Failed to update status: ' + error.message + '. Please check console for details.');
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
    
    if (!goLiveBtn) {
        console.warn('Go Live button not found');
        return;
    }
    
    console.log('Updating Go Live UI, isLive:', isLive);
    
    if (isLive) {
        // Hide "Tap to Go Live" button, show "You are LIVE" button
        goLiveBtn.style.display = 'none';
        if (liveStatusBtn) {
            liveStatusBtn.style.display = 'inline-block';
        }
        if (goLiveArrow) {
            goLiveArrow.style.display = 'inline-block';
        }
        if (offlineMessage) {
            offlineMessage.style.display = 'none';
        }
        if (newDeliveryBar) {
            newDeliveryBar.classList.remove('d-none');
        }
        if (lookingForDeliveries) {
            lookingForDeliveries.classList.remove('d-none');
        }
    } else {
        // Show "Tap to Go Live" button, hide "You are LIVE" button
        goLiveBtn.style.display = 'inline-block';
        if (liveStatusBtn) {
            liveStatusBtn.style.display = 'none';
        }
        if (goLiveArrow) {
            goLiveArrow.style.display = 'none';
        }
        if (offlineMessage) {
            offlineMessage.style.display = 'block';
        }
        if (lookingForDeliveries) {
            lookingForDeliveries.classList.add('d-none');
        }
        if (newDeliveryBar) {
            newDeliveryBar.classList.add('d-none');
        }
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
    
    // Update Go Live UI to reflect current status
    updateGoLiveUI();
    
    // Load deliveries if live
    if (isLive) {
        loadDeliveries();
        // Start auto-refresh every 5 seconds when online
        if (!deliveryRefreshInterval) {
            deliveryRefreshInterval = setInterval(loadDeliveries, 5000);
        }
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
    
    // Active deliveries: not delivered and not completed
    const active = deliveries.filter(d => d.status !== 'delivered' && d.status !== 'completed');
    // Completed deliveries: delivered or completed (payment done)
    const completed = deliveries.filter(d => d.status === 'delivered' || d.status === 'completed');
    
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
        'delivered': '<span class="badge bg-success">Delivered</span>',
        'completed': '<span class="badge bg-success">Completed</span>'
    };
    
    // Payment info
    let paymentInfo = '';
    if (delivery.payment_status && delivery.status === 'delivered') {
        const paymentStatus = delivery.payment_status === 'paid' ? 'success' : 
                             delivery.payment_status === 'pending_cash' ? 'warning' : 'secondary';
        const paymentStatusText = delivery.payment_status === 'paid' ? 'Paid' : 
                                 delivery.payment_status === 'pending_cash' ? 'Cash Pending' : 'Pending';
        const paymentMethod = delivery.payment_method ? ` (${delivery.payment_method.toUpperCase()})` : '';
        paymentInfo = `
            <div class="mt-2">
                <strong>Payment:</strong> 
                <span class="badge bg-${paymentStatus}">${paymentStatusText}${paymentMethod}</span>
                ${delivery.total_amount ? `<br><small class="text-muted">Amount: ₹${parseFloat(delivery.total_amount).toFixed(2)}</small>` : ''}
            </div>
        `;
    }
    
    // COD Confirmation Button
    let codButton = '';
    if (isCompleted && delivery.payment_method === 'cash' && delivery.payment_status === 'pending_cash') {
        codButton = `
            <button class="btn btn-success btn-sm mt-2" onclick="confirmCashPayment('${delivery.id}')">
                <i class="fas fa-money-bill-wave me-1"></i>Confirm Cash Received
            </button>
        `;
    }
    
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
            ${delivery.status === 'on_the_way' && (!delivery.total_stops || delivery.total_stops === 1) ? `
                <button class="btn btn-success" onclick="updateDeliveryStatus('${delivery.id}', 'delivered')">
                    <i class="fas fa-check-circle me-1"></i>Mark as Delivered
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
                        ${paymentInfo}
                    </div>
                    <div class="col-md-4 text-end">
                        ${statusBadges[delivery.status] || '<span class="badge bg-secondary">' + delivery.status + '</span>'}
                        ${statusButtons}
                        ${codButton}
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
            if (data.all_delivered) {
                alert(`All stops delivered! Customer will be redirected to payment page.\n\nTracking ID: ${data.delivery_id}`);
            } else {
                alert(`Stop ${stopNumber} marked as delivered!`);
            }
            // Reload deliveries to update stats
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
            // Reload deliveries to update stats
            loadDeliveries();
            
            if (newStatus === 'delivered') {
                alert('Delivery marked as delivered! Customer will be redirected to payment page.\n\nTracking ID: ' + deliveryId);
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
    
    // Count deliveries by status
    const totalDeliveries = deliveries.length;
    const completed = deliveries.filter(d => d.status === 'delivered' || d.status === 'completed').length;
    const inProgress = deliveries.filter(d => d.status !== 'delivered' && d.status !== 'completed' && d.status !== 'available').length;
    const available = deliveries.filter(d => d.status === 'available').length;
    
    // Calculate total earnings from actual delivery amounts (only paid deliveries)
    const paidDeliveries = deliveries.filter(d => 
        (d.status === 'delivered' || d.status === 'completed') && 
        d.payment_status === 'paid'
    );
    const totalEarnings = paidDeliveries.reduce((sum, delivery) => {
        const amount = parseFloat(delivery.total_amount) || 0;
        // Partner gets 70% of delivery amount (30% platform fee)
        const partnerEarning = amount * 0.7;
        return sum + partnerEarning;
    }, 0);
    
    // Update total deliveries
    const totalDeliveriesEl = document.getElementById('totalDeliveries');
    if (totalDeliveriesEl) {
        totalDeliveriesEl.textContent = totalDeliveries;
    }
    
    // Update completed deliveries
    const completedEl = document.getElementById('completedDeliveries');
    if (completedEl) completedEl.textContent = completed;
    
    // Update in progress deliveries
    const inProgressEl = document.getElementById('inProgressDeliveries');
    if (inProgressEl) inProgressEl.textContent = inProgress;
    
    // Update earnings (use totalEarnings if exists, otherwise todayEarnings)
    const totalEarningsEl = document.getElementById('totalEarnings');
    const todayEarningsEl = document.getElementById('todayEarnings');
    if (totalEarningsEl) {
        totalEarningsEl.textContent = `₹${totalEarnings.toFixed(2)}`;
    }
    if (todayEarningsEl) {
        todayEarningsEl.textContent = `₹${totalEarnings.toFixed(2)}`;
    }
    
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
// Confirm cash payment received
async function confirmCashPayment(bookingId) {
    if (!currentPartner) return;
    
    if (!confirm('Confirm that you have received cash payment from the customer?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/payment/cash-confirm/${bookingId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Cash payment confirmed successfully! Earnings updated.');
            // Reload deliveries to update stats and show updated status
            loadDeliveries();
        } else {
            alert('Failed to confirm payment: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Confirm cash payment error:', error);
        alert('Failed to confirm payment. Please try again.');
    }
}

window.deliverStop = deliverStop;
window.toggleGoLive = toggleGoLive;
window.confirmCashPayment = confirmCashPayment;

