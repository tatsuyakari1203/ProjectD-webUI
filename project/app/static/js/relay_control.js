document.addEventListener('DOMContentLoaded', function () {
    // const socket = io(); // SocketIO removed
    const activeTimers = {}; // To store interval IDs for countdowns

    function sendRelayCommand(relayId, action, durationMinutes = null) {
        const payload = {
            relay_id: parseInt(relayId),
            action: action
        };
        if (durationMinutes && action === 'on') {
            payload.duration = parseInt(durationMinutes);
        }

        fetch('/api/relay/control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Command response:', data);
            if (data.status === 'error') {
                alert('Error: ' + data.message);
            }
            // UI updates will primarily be driven by SocketIO `relay_status_update`
        })
        .catch((error) => {
            console.error('Error sending command:', error);
            alert('Failed to send command. Check console for details.');
        });
    }

    function updateRelayCardUI(relayData) {
        const relayId = relayData.id;
        const card = document.getElementById(`relay-card-${relayId}`);
        if (!card) return;

        const stateElement = document.getElementById(`relay-state-${relayId}`);
        const timeElement = document.getElementById(`relay-time-${relayId}`);
        const timeLeftTextElement = timeElement ? timeElement.closest('.remaining-time-text') : null;
        const btnOn = card.querySelector('.btn-on');
        const btnOff = card.querySelector('.btn-off');
        const durationInput = card.querySelector('.duration-input');

        if (stateElement) {
            stateElement.textContent = relayData.state ? 'On' : 'Off';
        }

        // Clear any existing countdown for this relay
        if (activeTimers[relayId]) {
            clearInterval(activeTimers[relayId]);
            delete activeTimers[relayId];
        }

        if (relayData.state) { // Relay is ON
            btnOn.classList.add('d-none');
            durationInput.classList.add('d-none');
            btnOff.classList.remove('d-none');
            
            if (relayData.remaining_time && relayData.remaining_time > 0) {
                if (timeLeftTextElement) timeLeftTextElement.classList.remove('d-none');
                if (timeElement) timeElement.textContent = relayData.remaining_time;
                
                // Start countdown
                let remaining = relayData.remaining_time;
                activeTimers[relayId] = setInterval(() => {
                    remaining--;
                    if (timeElement) timeElement.textContent = remaining;
                    if (remaining <= 0) {
                        clearInterval(activeTimers[relayId]);
                        delete activeTimers[relayId];
                        // Optionally, reflect that time is up, though MQTT status should confirm OFF state soon
                        if (timeLeftTextElement) timeLeftTextElement.classList.add('d-none');
                        // stateElement.textContent = 'Off'; // This might be preemptive
                        // btnOff.classList.add('d-none');
                        // btnOn.classList.remove('d-none');
                        // durationInput.classList.remove('d-none');
                    }
                }, 1000);
            } else {
                if (timeLeftTextElement) timeLeftTextElement.classList.add('d-none');
                if (timeElement) timeElement.textContent = '0';
            }
        } else { // Relay is OFF
            btnOff.classList.add('d-none');
            btnOn.classList.remove('d-none');
            durationInput.classList.remove('d-none');
            if (timeLeftTextElement) timeLeftTextElement.classList.add('d-none');
            if (timeElement) timeElement.textContent = '0';
        }
    }

    // socket.on('connect', () => { // SocketIO removed
    //     console.log('SocketIO connected');
    // });

    // socket.on('relay_status_update', function (data) { // SocketIO removed
    //     console.log('Received relay_status_update:', data);
    //     if (data.relays && Array.isArray(data.relays)) {
    //         data.relays.forEach(relayData => {
    //             updateRelayCardUI(relayData);
    //         });
    //     }
    // });

    // socket.on('disconnect', () => { // SocketIO removed
    //     console.log('SocketIO disconnected');
    // });

    // Add event listeners for control buttons
    document.querySelectorAll('.btn-on').forEach(button => {
        button.addEventListener('click', function () {
            const relayId = this.dataset.id;
            const durationInput = document.getElementById(`duration-${relayId}`);
            const duration = durationInput ? durationInput.value : null;
            sendRelayCommand(relayId, 'on', duration ? parseInt(duration) : null);
        });
    });

    document.querySelectorAll('.btn-off').forEach(button => {
        button.addEventListener('click', function () {
            const relayId = this.dataset.id;
            sendRelayCommand(relayId, 'off');
        });
    });
}); 