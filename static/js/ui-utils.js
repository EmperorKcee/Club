/**
 * UI Utilities
 * A collection of reusable UI functions for the application
 */

const UI = {
    // Show a notification message
    notify: function(message, type = 'info') {
        // Remove any existing notifications
        document.querySelectorAll('.alert-notification').forEach(el => el.remove());
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed alert-notification`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    },
    
    // Handle button loading state
    setButtonState: function(button, isLoading, loadingText = 'Processing...') {
        if (!button) return;
        
        if (isLoading) {
            button._originalHTML = button._originalHTML || button.innerHTML;
            button.disabled = true;
            button.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i> ${loadingText}`;
        } else {
            button.disabled = false;
            if (button._originalHTML) {
                button.innerHTML = button._originalHTML;
            }
        }
    },
    
    // Reset button to original state
    resetButton: function(button) {
        this.setButtonState(button, false);
    },
    
    // Show a confirmation dialog
    confirm: function(message, confirmCallback, cancelCallback = null) {
        if (confirm(message)) {
            if (typeof confirmCallback === 'function') confirmCallback();
        } else if (cancelCallback && typeof cancelCallback === 'function') {
            cancelCallback();
        }
    }
};

// Make UI object available globally
window.UI = UI;
