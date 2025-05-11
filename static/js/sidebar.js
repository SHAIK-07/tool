document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const sidebar = document.getElementById('sidebar');
    const contentWrapper = document.querySelector('.content-wrapper');
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const mobileSidebarToggle = document.getElementById('mobile-sidebar-toggle');

    // Create overlay element for mobile
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);

    // Set localStorage to ensure sidebar is expanded by default
    localStorage.setItem('sidebarCollapsed', 'false');

    // Check if we're on mobile initially
    const isMobile = window.innerWidth <= 992;

    // Function to toggle sidebar on desktop
    function toggleSidebar() {
        sidebar.classList.toggle('collapsed');
        contentWrapper.classList.toggle('expanded');

        // Save state to localStorage
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    }

    // Function to toggle sidebar on mobile
    function toggleMobileSidebar() {
        sidebar.classList.toggle('mobile-open');
        overlay.classList.toggle('active');

        // Prevent scrolling when sidebar is open
        if (sidebar.classList.contains('mobile-open')) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    }

    // Add event listeners
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', toggleSidebar);
    }

    if (mobileSidebarToggle) {
        mobileSidebarToggle.addEventListener('click', toggleMobileSidebar);
    }

    // Close sidebar when clicking on overlay
    overlay.addEventListener('click', toggleMobileSidebar);

    // Set active link based on current page
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');

    navLinks.forEach(link => {
        const href = link.getAttribute('href');

        // Check if the current path matches the link href
        if (currentPath === href ||
            (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        }

        // Prevent sidebar toggle when clicking nav links
        link.addEventListener('click', function(e) {
            // Don't stop the navigation, just prevent sidebar toggle
            e.stopPropagation();

            // Store the current sidebar state to maintain it after page load
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });
    });

    // Check if sidebar state is saved in localStorage
    // Default to expanded (not collapsed) if no state is saved
    let sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';

    // Force sidebar to be expanded on first load
    if (localStorage.getItem('sidebarCollapsed') === null) {
        localStorage.setItem('sidebarCollapsed', 'false');
        sidebarCollapsed = false;
    }

    if (sidebarCollapsed) {
        sidebar.classList.add('collapsed');
        contentWrapper.classList.add('expanded');
    } else {
        sidebar.classList.remove('collapsed');
        contentWrapper.classList.remove('expanded');
    }

    // Handle window resize
    function handleResize() {
        const currentIsMobile = window.innerWidth <= 992;

        if (currentIsMobile) {
            // Mobile view
            sidebar.classList.remove('collapsed');
            contentWrapper.classList.remove('expanded');

            if (sidebar.classList.contains('mobile-open')) {
                document.body.style.overflow = 'hidden';
            }
        } else {
            // Desktop view
            if (sidebar.classList.contains('mobile-open')) {
                sidebar.classList.remove('mobile-open');
                overlay.classList.remove('active');
                document.body.style.overflow = '';
            }

            // Restore saved state
            if (sidebarCollapsed) {
                sidebar.classList.add('collapsed');
                contentWrapper.classList.add('expanded');
            }
        }
    }

    // Initial call to set correct state
    handleResize();

    // Add resize event listener
    window.addEventListener('resize', handleResize);
});
