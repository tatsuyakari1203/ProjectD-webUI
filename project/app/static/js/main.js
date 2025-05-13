/**
 * Main JavaScript for Irrigation Control System
 */

// Update time in real-time
function updateCurrentTime() {
    const now = new Date();
    const timeElements = document.querySelectorAll('.current-time');
    
    timeElements.forEach(el => {
        el.textContent = now.toLocaleTimeString();
    });
}

// Format dates for display
function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Format remaining time in minutes:seconds
function formatRemainingTime(seconds) {
    if (!seconds || seconds <= 0) return '0:00';
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Days of week lookup
const daysOfWeek = {
    1: 'Monday',
    2: 'Tuesday',
    3: 'Wednesday',
    4: 'Thursday',
    5: 'Friday',
    6: 'Saturday',
    7: 'Sunday'
};

// Format days list to human-readable format
function formatDaysList(days) {
    if (!days || !days.length) return 'None';
    
    if (days.length === 7) return 'Every day';
    
    return days.map(day => daysOfWeek[day]).join(', ');
}

// Update data via API fetch
function fetchData(endpoint, callback) {
    fetch(`/api/${endpoint}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            callback(data);
        })
        .catch(error => {
            console.error(`Error fetching ${endpoint}:`, error);
        });
}

// Post data to API endpoint
function postData(endpoint, data, callback) {
    fetch(`/api/${endpoint}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(responseData => {
        if (callback) callback(responseData);
    })
    .catch(error => {
        console.error(`Error posting to ${endpoint}:`, error);
    });
}

// Set up auto-refresh for data elements
function setupAutoRefresh(elementId, endpoint, intervalSeconds, updateFunction) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Initial fetch
    fetchData(endpoint, data => {
        updateFunction(element, data);
    });
    
    // Set up interval
    setInterval(() => {
        fetchData(endpoint, data => {
            updateFunction(element, data);
        });
    }, intervalSeconds * 1000);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Update time every second
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
    
    // Setup tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Highlight active sidebar item
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar .nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
    
    // Format dates
    document.querySelectorAll('.format-date').forEach(element => {
        const dateString = element.getAttribute('data-date');
        if (dateString) {
            element.textContent = formatDateTime(dateString);
        }
    });
    
    // Format days lists
    document.querySelectorAll('.format-days').forEach(element => {
        const daysString = element.getAttribute('data-days');
        if (daysString) {
            try {
                const days = JSON.parse(daysString);
                element.textContent = formatDaysList(days);
            } catch (e) {
                console.error('Error parsing days:', e);
            }
        }
    });
}); 