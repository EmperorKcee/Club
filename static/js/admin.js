// Admin Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
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

    // Toggle sidebar on mobile
    const sidebarToggler = document.getElementById('sidebarToggler');
    const sidebar = document.querySelector('.admin-sidebar');
    const sidebarOverlay = document.querySelector('.sidebar-overlay');
    
    if (sidebarToggler && sidebar) {
        sidebarToggler.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('show');
            }
        });
    }
    
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            sidebar.classList.remove('show');
            this.classList.remove('show');
        });
    }

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // File input preview
    const fileInputs = document.querySelectorAll('.custom-file-input');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name || 'Choose file';
            const label = this.nextElementSibling;
            if (label) {
                label.textContent = fileName;
            }
        });
    });

    // Password visibility toggle
    const togglePasswordBtns = document.querySelectorAll('.toggle-password');
    togglePasswordBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.previousElementSibling;
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });

    // Generate random password
    const generatePasswordBtn = document.getElementById('generatePassword');
    if (generatePasswordBtn) {
        generatePasswordBtn.addEventListener('click', function() {
            const passwordField = document.querySelector('input[name="password"]');
            if (passwordField) {
                const password = generateRandomPassword(12);
                passwordField.value = password;
                
                // If there's a password confirmation field, update it too
                const confirmPasswordField = document.querySelector('input[name="confirm_password"]');
                if (confirmPasswordField) {
                    confirmPasswordField.value = password;
                }
                
                // Show a toast notification
                showToast('Password generated successfully!', 'success');
            }
        });
    }

    // Initialize DataTables if available
    if (typeof $.fn.DataTable === 'function') {
        $('.datatable').DataTable({
            responsive: true,
            pageLength: 25,
            order: [[0, 'desc']],
            dom: '<"d-flex justify-content-between align-items-center mb-4"f<"d-flex align-items-center">>rt<"d-flex justify-content-between align-items-center"ip>',
            language: {
                search: "",
                searchPlaceholder: "Search...",
                lengthMenu: "Show _MENU_ entries",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                infoEmpty: "No entries found",
                infoFiltered: "(filtered from _MAX_ total entries)",
                paginate: {
                    first: "First",
                    last: "Last",
                    next: "Next",
                    previous: "Previous"
                }
            }
        });
    }
});

// Generate a random password
function generateRandomPassword(length = 12) {
    const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+~`|}{[]\\:;?><,./-=';
    let password = '';
    
    // Ensure at least one of each character type
    const lowercase = 'abcdefghijklmnopqrstuvwxyz';
    const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const numbers = '0123456789';
    const symbols = '!@#$%^&*()_+~`|}{[]\\:;?><,./-=';
    
    // Add one of each required character type
    password += lowercase.charAt(Math.floor(Math.random() * lowercase.length));
    password += uppercase.charAt(Math.floor(Math.random() * uppercase.length));
    password += numbers.charAt(Math.floor(Math.random() * numbers.length));
    password += symbols.charAt(Math.floor(Math.random() * symbols.length));
    
    // Fill the rest with random characters
    for (let i = password.length; i < length; i++) {
        password += charset.charAt(Math.floor(Math.random() * charset.length));
    }
    
    // Shuffle the password to make it more random
    return password.split('').sort(() => 0.5 - Math.random()).join('');
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;
    
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.role = 'alert';
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
    
    bsToast.show();
}

// Confirm before performing destructive actions
document.addEventListener('click', function(e) {
    if (e.target.matches('[data-confirm]')) {
        e.preventDefault();
        const message = e.target.getAttribute('data-confirm') || 'Are you sure you want to perform this action?';
        if (confirm(message)) {
            if (e.target.tagName === 'A') {
                window.location.href = e.target.href;
            } else if (e.target.tagName === 'BUTTON' && e.target.form) {
                e.target.form.submit();
            }
        }
    }
});

// Handle bulk actions
document.addEventListener('DOMContentLoaded', function() {
    const bulkActionForm = document.getElementById('bulkActionForm');
    const bulkSelectAll = document.getElementById('bulkSelectAll');
    const bulkSelectItems = document.querySelectorAll('.bulk-select-item');
    const bulkActionSelect = document.getElementById('bulkAction');
    const bulkActionBtn = document.getElementById('applyBulkAction');
    
    if (bulkSelectAll && bulkSelectItems.length > 0) {
        bulkSelectAll.addEventListener('change', function() {
            const isChecked = this.checked;
            bulkSelectItems.forEach(item => {
                item.checked = isChecked;
            });
            updateBulkActionButton();
        });
    }
    
    if (bulkSelectItems.length > 0) {
        bulkSelectItems.forEach(item => {
            item.addEventListener('change', updateBulkActionButton);
        });
    }
    
    if (bulkActionBtn && bulkActionSelect) {
        bulkActionBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const selectedAction = bulkActionSelect.value;
            const selectedItems = Array.from(bulkSelectItems)
                .filter(item => item.checked)
                .map(item => item.value);
            
            if (selectedItems.length === 0) {
                showToast('Please select at least one item', 'warning');
                return;
            }
            
            if (selectedAction === '') {
                showToast('Please select an action', 'warning');
                return;
            }
            
            if (confirm(`Are you sure you want to ${selectedAction} ${selectedItems.length} selected item(s)?`)) {
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = bulkActionForm ? bulkActionForm.action : '';
                
                const csrfToken = document.querySelector('input[name="csrf_token"]');
                if (csrfToken) {
                    form.appendChild(csrfToken.cloneNode());
                }
                
                const actionInput = document.createElement('input');
                actionInput.type = 'hidden';
                actionInput.name = 'action';
                actionInput.value = selectedAction;
                form.appendChild(actionInput);
                
                selectedItems.forEach(itemId => {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'item_ids[]';
                    input.value = itemId;
                    form.appendChild(input);
                });
                
                document.body.appendChild(form);
                form.submit();
            }
        });
    }
    
    function updateBulkActionButton() {
        if (!bulkActionBtn) return;
        
        const selectedCount = Array.from(bulkSelectItems).filter(item => item.checked).length;
        
        if (selectedCount > 0) {
            bulkActionBtn.disabled = false;
            bulkActionBtn.textContent = `Apply to ${selectedCount} item(s)`;
        } else {
            bulkActionBtn.disabled = true;
            bulkActionBtn.textContent = 'Apply';
        }
    }
});
