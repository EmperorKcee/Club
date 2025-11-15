/**
 * Players Page JavaScript
 * Handles export and print functionality for the players page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // View toggle functionality
    function switchToCardView() {
        document.getElementById('playersCards').style.display = 'block';
        document.getElementById('playersTable').style.display = 'none';
        localStorage.setItem('playersView', 'cards');
    }

    function switchToTableView() {
        document.getElementById('playersCards').style.display = 'none';
        document.getElementById('playersTable').style.display = 'block';
        localStorage.setItem('playersView', 'table');
    }

    // Restore saved view preference
    const savedView = localStorage.getItem('playersView') || 'cards';
    if (savedView === 'table') {
        document.getElementById('tableView').checked = true;
        switchToTableView();
    } else {
        document.getElementById('cardView').checked = true;
        switchToCardView();
    }

    // Set up view toggle event listeners
    document.getElementById('cardView').addEventListener('change', function() {
        if (this.checked) switchToCardView();
    });

    document.getElementById('tableView').addEventListener('change', function() {
        if (this.checked) switchToTableView();
    });

    // Export to CSV functionality
    function exportPlayersToCSV() {
        const table = document.querySelector('#playersTable table');
        if (!table) {
            alert('No player data available to export');
            return;
        }

        let csv = [];
        const rows = table.querySelectorAll('tr');
        
        for (let i = 0; i < rows.length; i++) {
            const row = [];
            const cols = rows[i].querySelectorAll('td, th');
            
            for (let j = 0; j < cols.length; j++) {
                // Skip the action buttons column
                if (cols[j].querySelector('.btn-group')) continue;
                
                // Clean and format the cell content
                let text = cols[j].innerText.replace(/\n/g, ' ').trim();
                row.push('"' + text.replace(/"/g, '""') + '"');
            }
            
            if (row.length > 0) {
                csv.push(row.join(','));
            }
        }

        // Create CSV file and download
        const csvContent = 'data:text/csv;charset=utf-8,' + csv.join('\n');
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement('a');
        link.setAttribute('href', encodedUri);
        link.setAttribute('download', `players_export_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Print functionality
    function printPlayersTable() {
        const table = document.querySelector('#playersTable table');
        if (!table) {
            alert('No player data available to print');
            return;
        }

        // Clone the table to avoid modifying the original
        const tableClone = table.cloneNode(true);
        
        // Remove action buttons from the cloned table
        const actionButtons = tableClone.querySelectorAll('.btn-group');
        actionButtons.forEach(btn => btn.remove());

        // Create a new window for printing
        const printWindow = window.open('', '_blank');
        const title = document.title;
        
        const printContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>${title}</title>
                <style>
                    @media print {
                        body { font-family: Arial, sans-serif; font-size: 12px; }
                        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
                        th { background-color: #f8f9fa; text-align: left; padding: 8px; border: 1px solid #dee2e6; }
                        td { padding: 8px; border: 1px solid #dee2e6; }
                        .no-print { display: none !important; }
                        .print-title { text-align: center; margin-bottom: 20px; }
                        .print-date { text-align: right; margin-bottom: 10px; font-size: 11px; color: #6c757d; }
                        img { max-width: 40px; height: auto; margin-right: 8px; }
                    }
                </style>
            </head>
            <body>
                <div class="print-title">
                    <h2>${title}</h2>
                    <div class="print-date">Generated on: ${new Date().toLocaleString()}</div>
                </div>
                ${tableClone.outerHTML}
                <script>
                    window.onload = function() {
                        window.print();
                        window.onafterprint = function() {
                            window.close();
                        };
                    };
                <\/script>
            </body>
            </html>
        `;

        printWindow.document.open();
        printWindow.document.write(printContent);
        printWindow.document.close();
    }

    // Set up event listeners for export and print buttons
    const exportBtn = document.getElementById('exportBtn');
    const printBtn = document.getElementById('printBtn');
    
    if (exportBtn) {
        exportBtn.addEventListener('click', exportPlayersToCSV);
    }
    
    if (printBtn) {
        printBtn.addEventListener('click', printPlayersTable);
    }

    // Handle player deletion
    document.querySelectorAll('.delete-player').forEach(button => {
        button.addEventListener('click', function() {
            const playerId = this.getAttribute('data-id');
            const form = document.getElementById('deletePlayerForm');
            if (form) {
                form.action = `/players/${playerId}/delete`;
                const modal = new bootstrap.Modal(document.getElementById('deletePlayerModal'));
                modal.show();
            }
        });
    });

    // Reset filters
    const resetFiltersBtn = document.getElementById('reset-filters');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', function() {
            window.location.href = '{{ url_for("players") }}';
        });
    }

    // Add smooth animations for card interactions
    document.querySelectorAll('.player-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
});
