function initializeViewToggle() {
    const viewButtons = document.querySelectorAll('.view-toggle-btn');
    const gridView = document.getElementById('grid-view');
    const tableView = document.getElementById('table-view');

    if (!viewButtons.length || !gridView || !tableView) return;

    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const view = this.dataset.view;
            
            // Update active button
            viewButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Show/hide views
            if (view === 'grid') {
                gridView.style.display = 'grid';
                tableView.style.display = 'none';
            } else {
                gridView.style.display = 'none';
                tableView.style.display = 'block';
            }
            
            // Save preference
            localStorage.setItem('viewPreference', view);
        });
    });

    // Load saved preference
    const savedView = localStorage.getItem('viewPreference');
    if (savedView) {
        const button = document.querySelector(`[data-view="${savedView}"]`);
        if (button) button.click();
    }
}

function initializeTableSort() {
    const sortableHeaders = document.querySelectorAll('.sortable');
    
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const sortKey = this.dataset.sort;
            const tbody = this.closest('table').querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // Toggle sort direction
            const isAscending = !this.classList.contains('sort-asc');
            sortableHeaders.forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
            });
            this.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
            
            // Sort rows
            rows.sort((a, b) => {
                let aVal = a.querySelector(`[data-${sortKey}]`).dataset[sortKey];
                let bVal = b.querySelector(`[data-${sortKey}]`).dataset[sortKey];
                return isAscending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            });
            
            // Update DOM
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

// Initialize all admin features
document.addEventListener('DOMContentLoaded', function() {
    initializeViewToggle();
    initializeTableSort();
}); 