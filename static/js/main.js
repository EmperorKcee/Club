/**
 * Football Club Management System - Main JavaScript
 * Handles frontend interactivity and API communication
 */

document.addEventListener('DOMContentLoaded', function() {
    // Navbar scroll effect
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }

    // Animate elements on scroll
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.feature-card, .stat-item, .testimonial-card');
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const screenPosition = window.innerHeight / 1.3;
            
            if (elementPosition < screenPosition) {
                element.classList.add('animate-fade-in-up');
            }
        });
    };

    // Run once on page load
    animateOnScroll();
    
    // Run on scroll
    window.addEventListener('scroll', animateOnScroll);

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Handle form submissions with AJAX
    const forms = document.querySelectorAll('.ajax-form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            
            fetch(this.action, {
                method: this.method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.redirect) {
                    window.location.href = data.redirect;
                } else if (data.message) {
                    showAlert(data.message, data.status || 'success');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('An error occurred. Please try again.', 'danger');
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            });
        });
    });

    // Handle delete buttons
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('Are you sure you want to delete this item?')) {
                const url = this.getAttribute('data-url');
                fetch(url, {
                    method: 'DELETE',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ _method: 'DELETE' })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else if (data.message) {
                        showAlert(data.message, 'success');
                        // Remove the deleted item from the DOM
                        const item = this.closest('.item-row, .card, tr, li');
                        if (item) {
                            item.style.opacity = '0';
                            setTimeout(() => item.remove(), 300);
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showAlert('Failed to delete item. Please try again.', 'danger');
                });
            }
        });
    });

    // Toggle password visibility
    const togglePasswordBtns = document.querySelectorAll('.toggle-password');
    togglePasswordBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const input = document.querySelector(this.getAttribute('toggle'));
            if (input) {
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                this.querySelector('i').classList.toggle('fa-eye');
                this.querySelector('i').classList.toggle('fa-eye-slash');
            }
        });
    });

    // Initialize datepickers
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        if (!input.value) {
            input.valueAsDate = new Date();
        }
    });

    // Handle image preview for file inputs
    const imageInputs = document.querySelectorAll('.image-upload');
    imageInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = this.files[0];
            const preview = document.querySelector(this.getAttribute('data-preview'));
            
            if (file && preview) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                }
                reader.readAsDataURL(file);
            }
        });
    });

    // Initialize charts if on dashboard
    if (document.getElementById('performanceChart')) {
        // Chart initialization is handled in the dashboard template
    }
});

/**
 * Show a bootstrap alert message
 * @param {string} message - The message to display
 * @param {string} type - The alert type (success, danger, warning, info)
 * @param {number} duration - Duration in milliseconds to show the alert (0 for permanent)
 */
function showAlert(message, type = 'info', duration = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.alerts-container') || document.body;
    container.prepend(alertDiv);
    
    // Auto-remove alert after duration
    if (duration > 0) {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, duration);
    }
}

/**
 * Toggle sidebar collapse on mobile
 */
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('collapsed');
    }
}

/**
 * Format date to a readable format
 * @param {string} dateString - Date string to format
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// Make functions available globally
window.showAlert = showAlert;
window.toggleSidebar = toggleSidebar;
window.formatDate = formatDate;
