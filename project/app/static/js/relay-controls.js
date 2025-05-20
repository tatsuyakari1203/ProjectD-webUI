/**
 * Relay Control JavaScript
 * Handles AJAX form submission and Socket.IO updates for relay control
 */

// Function to format remaining time (MM:SS)
function formatRemainingTime(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
}

// Function to update individual relay card UI elements
function updateRelayCardUI(relay) {
    console.log("Updating UI for relay:", relay); // Debug log
    const card = document.querySelector(`.card[data-relay-id="${relay.id}"]`);
    if (!card) {
        console.warn(`Card for relay ID ${relay.id} not found`);
        return;
    }

    // Update Badge (ON/OFF status)
    const badge = card.querySelector('.relay-status-badge');
    if (badge) {
        badge.className = relay.state ? 'badge fs-6 bg-success relay-status-badge' : 'badge fs-6 bg-secondary relay-status-badge';
        badge.textContent = relay.state ? 'ON' : 'OFF';
    }

    // Update Controls Form (dynamically show ON/OFF buttons and duration input)
    const controlsForm = card.querySelector('.relay-control-form');
    if (controlsForm) {
        // Store any event listeners (re-apply after updating innerHTML)
        const oldForm = controlsForm.cloneNode(true);
        
        // Update the form HTML
        controlsForm.innerHTML = createRelayControlFormContent(relay);
        
        // Set up event listener on the new form content
        setupFormAjaxSubmit(controlsForm);
    }

    // Update Status Column (Remaining Time, Last Updated)
    const statusCol = card.querySelector('.relay-status-column');
    if (statusCol) {
        // Remove existing remaining time if present
        const existingRemainingTimeDiv = statusCol.querySelector('.relay-remaining-time-container');
        if (existingRemainingTimeDiv) existingRemainingTimeDiv.remove();

        // Add new remaining time if applicable
        if (relay.state && relay.remaining_time > 0) {
            const newElDiv = document.createElement('div');
            newElDiv.className = 'mb-2 relay-remaining-time-container';
            newElDiv.innerHTML = `
                <strong><i class="fas fa-stopwatch me-2"></i>Remaining:</strong>
                <span class="remaining-time fs-5" data-seconds="${relay.remaining_time}">
                    ${formatRemainingTime(relay.remaining_time)}
                </span>
            `;
            const lastUpdateDiv = statusCol.querySelector('.mb-0'); 
            if(lastUpdateDiv) statusCol.insertBefore(newElDiv, lastUpdateDiv);
            else statusCol.appendChild(newElDiv);
        }

        // Update Last Updated Time
        const lastUpdatedSpan = statusCol.querySelector('.relay-last-updated');
        if (lastUpdatedSpan && relay.last_updated) {
            lastUpdatedSpan.dataset.date = relay.last_updated;
            try {
                lastUpdatedSpan.textContent = new Date(relay.last_updated).toLocaleString(); 
            } catch (e) { 
                console.warn('Date formatting error for last_updated:', e); 
                lastUpdatedSpan.textContent = 'Invalid Date';
            }
        }
    }
}

// Helper function to generate control form HTML
function createRelayControlFormContent(relay) {
    let formContent = `<input type="hidden" name="relay_id" value="${relay.id}">`;
    if (!relay.state) {
        // For OFF state, show options to turn ON
        formContent += `
            <div class="card border-0 bg-transparent mb-2">
                <div class="card-body p-0">
                    <div class="mb-3">
                        <div class="form-check form-switch">
                            <input class="form-check-input duration-toggle" type="checkbox" id="duration-toggle-${relay.id}" checked>
                            <label class="form-check-label" for="duration-toggle-${relay.id}">Use Duration Timer</label>
                        </div>
                    </div>
                    
                    <div class="duration-input-group">
                        <label for="duration-${relay.id}" class="form-label">Duration (minutes):</label>
                        <div class="input-group mb-3">
                            <input type="number" class="form-control" name="duration" id="duration-${relay.id}" 
                                min="1" max="120" value="5" placeholder="Minutes">
                            <button class="btn btn-primary" type="submit" name="action" value="on">
                                <i class="fas fa-clock me-1"></i>Turn On with Timer
                            </button>
                        </div>
                    </div>
                    
                    <div class="d-grid">
                        <button type="submit" name="action" value="on" class="btn btn-success no-duration-btn" disabled>
                            <i class="fas fa-toggle-on me-1"></i>Turn On (No Timer)
                        </button>
                    </div>
                </div>
            </div>
        `;
    } else {
        // For ON state, just show option to turn OFF
        formContent += `
            <div class="d-grid">
                <button type="submit" name="action" value="off" class="btn btn-danger">
                    <i class="fas fa-toggle-off me-1"></i>Turn Off
                </button>
            </div>
        `;
        
        // If the relay has remaining time, show it
        if (relay.remaining_time > 0) {
            const minutes = Math.floor(relay.remaining_time / 60);
            const seconds = relay.remaining_time % 60;
            formContent += `
                <div class="text-center mt-2">
                    <small class="text-muted">Auto-off in ${minutes}:${seconds < 10 ? '0' + seconds : seconds}</small>
                </div>
            `;
        }
    }
    return formContent;
}

// Countdown timer for remaining times
function updateRemainingTimes() {
    document.querySelectorAll('.remaining-time').forEach(element => {
        let seconds = parseInt(element.dataset.seconds || 0);
        if (seconds > 0) {
            seconds--;
            element.dataset.seconds = seconds;
            element.textContent = formatRemainingTime(seconds);
        } else {
            element.textContent = '0:00';
        }
    });
}

// Function to show toast notifications
function showToast(title, message, type = 'success') {
    const toastPlacement = document.getElementById('toastPlacement');
    if (!toastPlacement) {
        console.warn('Toast container #toastPlacement not found. Using alert.');
        alert(`${title}: ${message}`);
        return;
    }
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body"><strong>${title}</strong>: ${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    toastPlacement.insertAdjacentHTML('beforeend', toastHtml);
    const toastElement = document.getElementById(toastId);
    if (toastElement) {
        const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
        toast.show();
        toastElement.addEventListener('hidden.bs.toast', () => toastElement.remove());
    }
}

// Function to handle duration toggle switch
function setupDurationToggle(form) {
    const toggleSwitch = form.querySelector('.duration-toggle');
    if (!toggleSwitch) return;
    
    const durationInputGroup = form.querySelector('.duration-input-group');
    const noDurationBtn = form.querySelector('.no-duration-btn');
    
    // Initial state
    toggleSwitch.addEventListener('change', function() {
        if (this.checked) {
            // Enable duration input, disable no-duration button
            durationInputGroup.style.display = 'block';
            noDurationBtn.disabled = true;
        } else {
            // Disable duration input, enable no-duration button
            durationInputGroup.style.display = 'none';
            noDurationBtn.disabled = false;
        }
    });
    
    // Trigger change event to set initial state
    toggleSwitch.dispatchEvent(new Event('change'));
}

// Set up AJAX form submission
function setupFormAjaxSubmit(form) {
    // First set up the duration toggle if applicable
    setupDurationToggle(form);
    
    form.addEventListener('submit', function(event) {
        // Prevent the default form submission (which would cause a page reload)
        event.preventDefault();
        console.log("Form submission intercepted"); // Debug log

        const formData = new FormData(form);
        const relayId = formData.get('relay_id');
        
        // Get the action from the submitter button
        let actionValue = null;
        if (event.submitter && event.submitter.name === 'action') {
            actionValue = event.submitter.value;
        }
        
        // Update formData if action was determined by submitter
        if (actionValue) {
            formData.set('action', actionValue);
        }

        // Check if using duration
        const durationToggle = form.querySelector('.duration-toggle');
        if (durationToggle && !durationToggle.checked) {
            // If toggle is off, remove duration from formData
            formData.delete('duration');
        }

        // Disable buttons while sending command
        form.querySelectorAll('button').forEach(b => b.disabled = true);
        
        // Add loading indicator
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'position-absolute top-0 start-0 w-100 h-100 bg-dark bg-opacity-50 d-flex justify-content-center align-items-center';
        loadingOverlay.style.zIndex = '10';
        loadingOverlay.innerHTML = '<div class="spinner-border text-light" role="status"><span class="visually-hidden">Loading...</span></div>';
        form.parentNode.style.position = 'relative';
        form.parentNode.appendChild(loadingOverlay);

        fetch(form.action, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Command response:", data); // Debug log
            if (data.message) {
                if (data.status === 'success') {
                    showToast('Command Sent', data.message);
                } else {
                    showToast('Command Error', data.message, 'danger');
                    // Re-enable buttons on error
                    form.querySelectorAll('button').forEach(b => b.disabled = false);
                }
            }
            // Remove loading overlay
            form.parentNode.removeChild(loadingOverlay);
        })
        .catch(error => {
            console.error('Error sending relay command:', error);
            showToast('Network Error', 'Error sending command. Check console.', 'danger');
            // Re-enable buttons on error
            form.querySelectorAll('button').forEach(b => b.disabled = false);
            // Remove loading overlay
            form.parentNode.removeChild(loadingOverlay);
        });
    });
}

// Set up relay name editing functionality
function setupRelayNameEditing() {
    document.querySelectorAll('.save-relay-name-btn').forEach(button => {
        button.addEventListener('click', function() {
            const relayId = this.getAttribute('data-relay-id');
            const nameInput = document.getElementById(`relayNameInput${relayId}`);
            const newName = nameInput.value.trim();
            
            if (newName && nameInput.checkValidity()) {
                fetch('/api/relay-name', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ relay_id: parseInt(relayId), name: newName }),
                })
                .then(response => response.json())
                .then(data => {
                    const modalElement = document.getElementById(`editRelayModal${relayId}`);
                    if (modalElement) {
                        const modal = bootstrap.Modal.getInstance(modalElement);
                        if (modal) modal.hide();
                    }
                    const cardHeaderNameSpan = document.querySelector(`.card[data-relay-id="${relayId}"] .relay-name-display`);
                    if (cardHeaderNameSpan) {
                        cardHeaderNameSpan.textContent = newName;
                    }
                    showToast('Success', `Zone ${relayId} name updated to ${newName}.`);
                })
                .catch(error => {
                    console.error('Error updating relay name:', error);
                    showToast('Error', 'Failed to update zone name.', 'danger');
                });
            } else if (!newName) {
                nameInput.reportValidity();
                showToast('Validation Error', 'Zone name cannot be empty.', 'warning');
            }
        });
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded - initializing relay controls"); // Debug log
    
    // Create toast container if it doesn't exist
    if (!document.getElementById('toastPlacement')) {
        const toastContainer = document.createElement('div');
        toastContainer.id = 'toastPlacement';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = '11';
        document.body.appendChild(toastContainer);
    }

    // Connect to Socket.IO server
    const socket = io();

    socket.on('connect', function() {
        console.log('Connected to WebSocket server for relay updates.');
        showToast('Connected', 'Real-time updates are now enabled.');
    });

    socket.on('relay_status_update', function(data) {
        console.log('Received relay status update:', data); // Debug log
        if (data && data.relays && Array.isArray(data.relays)) {
            data.relays.forEach(relay => {
                updateRelayCardUI(relay);
            });
        }
    });

    socket.on('disconnect', function() {
        console.warn('Disconnected from WebSocket server for relay updates.');
        showToast('Disconnected', 'Real-time updates interrupted. Will try to reconnect.', 'warning');
    });

    // Set up AJAX form submission for all relay control forms
    document.querySelectorAll('.relay-control-form').forEach(form => {
        setupFormAjaxSubmit(form);
    });

    // Start remaining time countdown
    setInterval(updateRemainingTimes, 1000);
    
    // Set up relay name editing
    setupRelayNameEditing();

    // Initial date formatting
    document.querySelectorAll('.format-date').forEach(el => {
        try {
            const dateValue = el.dataset.date;
            if (dateValue && dateValue.toLowerCase() !== 'none' && dateValue.toLowerCase() !== 'null') {
                const date = new Date(dateValue);
                if (!isNaN(date.getTime())) {
                    el.textContent = date.toLocaleString(); 
                } else { el.textContent = 'Invalid Date'; }
            } else { el.textContent = 'N/A'; }
        } catch (e) {
            el.textContent = 'Date Error';
            console.warn('Could not parse date:', el.dataset.date, e);
        }
    });
}); 