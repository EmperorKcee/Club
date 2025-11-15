// Handle player deletion
document.addEventListener('DOMContentLoaded', function() {
    // Function to set up delete handlers
    function setupDeleteHandlers() {
        // Add click handler to the document and delegate to delete buttons
        document.addEventListener('click', function(e) {
            const deleteBtn = e.target.closest('.delete-player');
            if (!deleteBtn) return;
            
            e.preventDefault();
            const playerId = deleteBtn.getAttribute('data-id');
            
            // Get player name from the card or table row
            const playerCard = deleteBtn.closest('.player-card') || deleteBtn.closest('tr');
            let playerName = 'this player';
            
            if (playerCard) {
                const nameElement = playerCard.querySelector('.card-title, .player-name') || 
                                  playerCard.querySelector('h5, h6, .text-truncate, td:nth-child(2)');
                if (nameElement) {
                    playerName = nameElement.textContent.trim();
                }
            }
            
            // Update modal content with player name
            const modal = document.getElementById('deletePlayerModal');
            const modalBody = modal.querySelector('.modal-body p:not(.text-muted)');
            if (modalBody) {
                modalBody.innerHTML = `Are you sure you want to delete <strong>${playerName}</strong>?`;
            }
            
            // Update form action
            const form = document.getElementById('deletePlayerForm');
            if (form) {
                form.action = `/players/${playerId}/delete`;
                
                // Show the modal
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            }
        });
    }

    // Initial setup
    setupDeleteHandlers();
    
    // Re-initialize delete handlers when switching views
    const cardView = document.getElementById('cardView');
    const tableView = document.getElementById('tableView');
    
    if (cardView) cardView.addEventListener('change', setupDeleteHandlers);
    if (tableView) tableView.addEventListener('change', setupDeleteHandlers);
});
