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

// API key for authentication
const API_KEY = "8a679613-019f-4b88-9068-da10f09dcdd2";

// Update data via API fetch
function fetchData(endpoint, successCallback, errorCallback) {
    console.log(`[fetchData] Requesting: /api/${endpoint}`);
    fetch(`/api/${endpoint}`, {
        headers: {
            'X-API-Key': API_KEY
        }
    })
    .then(response => {
        console.log(`[fetchData] Response status for /api/${endpoint}: ${response.status}`);
        if (!response.ok) {
            // Try to get text for more detailed error, then throw
            return response.text().then(text => {
                console.error(`[fetchData] HTTP error for /api/${endpoint}: ${response.status}`, text);
                throw new Error(`HTTP error! Status: ${response.status} - ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log(`[fetchData] Response data for /api/${endpoint}:`, data);
        if (data.success) {
            successCallback(data.data || data); 
        } else {
            console.error(`[fetchData] API error in /api/${endpoint}:`, data.error || 'Unknown API error');
            if (errorCallback) errorCallback(data.error || 'Unknown API error');
        }
    })
    .catch(error => {
        console.error(`[fetchData] Catch_Error fetching /api/${endpoint}:`, error);
        if (errorCallback) errorCallback(error);
    });
}

// Post data to API endpoint
function postData(endpoint, body, successCallback, errorCallback) {
    console.log(`[postData] Posting to: /api/${endpoint}`, body);
    fetch(`/api/${endpoint}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        },
        body: JSON.stringify(body),
    })
    .then(response => {
        console.log(`[postData] Response status for /api/${endpoint}: ${response.status}`);
        if (!response.ok) {
            return response.text().then(text => {
                console.error(`[postData] HTTP error for /api/${endpoint}: ${response.status}`, text);
                throw new Error(`HTTP error! Status: ${response.status} - ${text}`);
            });
        }
        return response.json();
    })
    .then(responseData => {
        console.log(`[postData] Response data for /api/${endpoint}:`, responseData);
        if (responseData.success) {
            if (successCallback) successCallback(responseData);
        } else {
            console.error(`[postData] API error in /api/${endpoint}:`, responseData.error || 'Unknown API error');
            if (errorCallback) errorCallback(responseData.error || 'Unknown API error');
        }
    })
    .catch(error => {
        console.error(`[postData] Catch_Error posting to /api/${endpoint}:`, error);
        if (errorCallback) errorCallback(error);
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