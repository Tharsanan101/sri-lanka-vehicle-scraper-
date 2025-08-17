// Main JavaScript file for Vehicle Information Scraper Web App

// Global variables
var progressInterval = null;
var currentScrapingStatus = null;

// Document ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize application
function initializeApp() {
    // Add fade-in animation to cards
    document.querySelectorAll('.card').forEach(card => {
        card.classList.add('fade-in');
    });

    // Initialize tooltips
    initializeTooltips();

    // Initialize form validation
    initializeFormValidation();

    // Initialize file input handlers
    initializeFileHandlers();

    // Check for existing scraping status
    checkExistingScrapingStatus();

    // Add keyboard shortcuts
    initializeKeyboardShortcuts();
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

// Initialize file input handlers
function initializeFileHandlers() {
    const fileInput = document.getElementById('vehicle_file');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                validateAndPreviewFile(file);
            }
        });
    }
}

// Validate and preview uploaded file
function validateAndPreviewFile(file) {
    const maxSize = 16 * 1024 * 1024; // 16MB
    const allowedTypes = ['text/plain', 'text/csv', 'application/csv'];
    
    // Check file size
    if (file.size > maxSize) {
        showAlert('File too large. Maximum size is 16MB.', 'error');
        document.getElementById('vehicle_file').value = '';
        return;
    }
    
    // Check file type
    if (!allowedTypes.includes(file.type) && !file.name.toLowerCase().endsWith('.csv') && !file.name.toLowerCase().endsWith('.txt')) {
        showAlert('Invalid file type. Please upload a CSV or TXT file.', 'error');
        document.getElementById('vehicle_file').value = '';
        return;
    }
    
    // Preview file contents
    const reader = new FileReader();
    reader.onload = function(e) {
        const content = e.target.result;
        const lines = content.split('\n').filter(line => line.trim() !== '');
        const vehicleCount = lines.length;
        
        if (vehicleCount === 0) {
            showAlert('File appears to be empty.', 'warning');
            return;
        }
        
        showAlert(`File loaded successfully. Found ${vehicleCount} vehicle numbers.`, 'success');
    };
    
    reader.onerror = function() {
        showAlert('Error reading file.', 'error');
    };
    
    reader.readAsText(file);
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.container-fluid');
    const alertDiv = document.createElement('div');
    
    const alertClass = type === 'error' ? 'danger' : type;
    const iconClass = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    }[type] || 'info-circle';
    
    alertDiv.className = `alert alert-${alertClass} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        <i class="fas fa-${iconClass} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top
    alertContainer.insertBefore(alertDiv, alertContainer.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Format duration
function formatDuration(seconds) {
    if (seconds < 60) {
        return `${Math.floor(seconds)}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}m ${remainingSeconds}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showAlert('Copied to clipboard!', 'success');
    }).catch(function(err) {
        showAlert('Failed to copy to clipboard.', 'error');
    });
}

// Export table to CSV
function exportTableToCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    for (let i = 0; i < rows.length; i++) {
        const row = [];
        const cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length - 1; j++) { // Exclude last column (actions)
            let cellText = cols[j].textContent.trim();
            cellText = cellText.replace(/"/g, '""'); // Escape quotes
            row.push(`"${cellText}"`);
        }
        
        csv.push(row.join(','));
    }
    
    // Download CSV
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Check for existing scraping status
function checkExistingScrapingStatus() {
    fetch('/progress')
        .then(response => {
            if (!response.ok) {
                throw new Error('No active scraping job');
            }
            return response.json();
        })
        .then(status => {
            if (status && status.is_running) {
                showAlert('Found an existing scraping job in progress.', 'info');
                // Redirect to results page to show progress
                setTimeout(() => {
                    window.location.href = '/results';
                }, 2000);
            }
        })
        .catch(error => {
            console.log('No existing scraping job found:', error.message);
        });
}

// Initialize keyboard shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl+Enter to submit form
        if (e.ctrlKey && e.key === 'Enter') {
            const form = document.getElementById('scrapingForm');
            if (form) {
                form.dispatchEvent(new Event('submit'));
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                bootstrap.Modal.getInstance(modal)?.hide();
            });
        }
    });
}

// Validate session ID format
function validateSessionId(sessionId) {
    // Basic validation for JSESSIONID format
    const sessionIdPattern = /^[A-F0-9]{32}$/i;
    return sessionIdPattern.test(sessionId);
}

// Validate vehicle number format
function validateVehicleNumber(vehicleNumber) {
    // Sri Lankan vehicle number patterns
    const patterns = [
        /^[A-Z]{2,3}-\d{4}$/,     // ABC-1234 or AB-1234
        /^\d{2,3}-\d{4}$/,        // 12-3456 or 123-4567
        /^[A-Z]{2,3}\d{4}$/,      // ABC1234
        /^\d{2,3}\d{4}$/          // 123456
    ];
    
    return patterns.some(pattern => pattern.test(vehicleNumber.toUpperCase()));
}

// Parse vehicle numbers from text
function parseVehicleNumbers(text) {
    // Split by various delimiters and clean up
    const delimiters = /[\n,;|\t]/;
    const numbers = text.split(delimiters)
        .map(num => num.trim().toUpperCase())
        .filter(num => num.length > 0);
    
    // Remove duplicates while preserving order
    return [...new Set(numbers)];
}

// Validate all vehicle numbers
function validateVehicleNumbers(vehicleNumbers) {
    const valid = [];
    const invalid = [];
    
    vehicleNumbers.forEach(num => {
        if (validateVehicleNumber(num)) {
            valid.push(num);
        } else {
            invalid.push(num);
        }
    });
    
    return { valid, invalid };
}

// Show loading overlay
function showLoadingOverlay(message = 'Loading...') {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.id = 'loadingOverlay';
    overlay.innerHTML = `
        <div class="text-center">
            <div class="spinner-border loading-spinner" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div class="mt-3 text-white">${message}</div>
        </div>
    `;
    
    document.body.appendChild(overlay);
}

// Hide loading overlay
function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

// Animate numbers (counting effect)
function animateNumber(element, start, end, duration = 1000) {
    const range = end - start;
    let current = start;
    const increment = range / (duration / 16); // 60fps
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= end) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

// Format timestamp
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

// Get time ago string
function getTimeAgo(timestamp) {
    const now = new Date();
    const past = new Date(timestamp);
    const diffInSeconds = Math.floor((now - past) / 1000);
    
    if (diffInSeconds < 60) {
        return 'just now';
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
        const days = Math.floor(diffInSeconds / 86400);
        return `${days} day${days > 1 ? 's' : ''} ago`;
    }
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Local storage helpers
const storage = {
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.error('Error saving to localStorage:', e);
        }
    },
    
    get: function(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Error reading from localStorage:', e);
            return defaultValue;
        }
    },
    
    remove: function(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            console.error('Error removing from localStorage:', e);
        }
    }
};

// Save form data to localStorage
function saveFormData() {
    const formData = {
        session_id: document.getElementById('session_id')?.value || '',
        max_workers: document.getElementById('max_workers')?.value || '3',
        delay: document.getElementById('delay')?.value || '2.0',
        nic: document.getElementById('nic')?.value || '2200000000',
        contact: document.getElementById('contact')?.value || '0777777777'
    };
    
    storage.set('scraper_form_data', formData);
}

// Load form data from localStorage
function loadFormData() {
    const formData = storage.get('scraper_form_data');
    
    if (formData) {
        Object.keys(formData).forEach(key => {
            const element = document.getElementById(key);
            if (element && formData[key]) {
                element.value = formData[key];
            }
        });
    }
}

// Initialize form data persistence
document.addEventListener('DOMContentLoaded', function() {
    loadFormData();
    
    // Save form data on change
    const formInputs = document.querySelectorAll('#scrapingForm input, #scrapingForm select');
    formInputs.forEach(input => {
        input.addEventListener('change', debounce(saveFormData, 500));
    });
});

// Print functionality
function printResults() {
    window.print();
}

// Generate report
function generateReport(results) {
    const report = {
        timestamp: new Date().toISOString(),
        summary: {
            total: results.length,
            successful: results.filter(r => r.status === 'success').length,
            failed: results.filter(r => r.status !== 'success').length
        },
        results: results
    };
    
    return report;
}

// Export to Excel (requires additional library)
function exportToExcel(data, filename = 'vehicle_data.xlsx') {
    // This would require a library like SheetJS
    showAlert('Excel export requires additional setup.', 'info');
}

// Console logging utility
const logger = {
    info: (message, ...args) => console.log(`[INFO] ${message}`, ...args),
    warn: (message, ...args) => console.warn(`[WARN] ${message}`, ...args),
    error: (message, ...args) => console.error(`[ERROR] ${message}`, ...args),
    debug: (message, ...args) => console.debug(`[DEBUG] ${message}`, ...args)
};

// Error handling
window.addEventListener('error', function(e) {
    logger.error('JavaScript error:', e.error);
    showAlert('An unexpected error occurred. Please refresh the page.', 'error');
});

// Unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(e) {
    logger.error('Unhandled promise rejection:', e.reason);
    showAlert('A network error occurred. Please check your connection.', 'error');
});

// Page visibility API to pause/resume when tab is hidden
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden, pause any timers if needed
        logger.debug('Page hidden, pausing updates');
    } else {
        // Page is visible, resume
        logger.debug('Page visible, resuming updates');
    }
});

// Export functions for global use
window.VehicleScraper = {
    showAlert,
    formatDuration,
    formatFileSize,
    copyToClipboard,
    exportTableToCSV,
    validateSessionId,
    validateVehicleNumber,
    parseVehicleNumbers,
    validateVehicleNumbers,
    showLoadingOverlay,
    hideLoadingOverlay,
    animateNumber,
    formatTimestamp,
    getTimeAgo,
    storage,
    logger,
    printResults,
    generateReport
};
