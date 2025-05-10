// Theme Switching Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get theme toggle element
    const themeToggle = document.getElementById('theme-toggle');
    
    // Check for saved theme preference or use default
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Apply the saved theme or default
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    // Update toggle state based on current theme
    if (themeToggle) {
        themeToggle.checked = currentTheme === 'dark';
    }
    
    // Listen for toggle changes
    if (themeToggle) {
        themeToggle.addEventListener('change', function() {
            if (this.checked) {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
                updateThemeIcons('dark');
            } else {
                document.documentElement.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
                updateThemeIcons('light');
            }
        });
    }
    
    // Initialize theme icons
    updateThemeIcons(currentTheme);
});

// Update theme-specific icons
function updateThemeIcons(theme) {
    const themeIcon = document.getElementById('theme-toggle-icon');
    
    if (themeIcon) {
        if (theme === 'dark') {
            themeIcon.innerHTML = '<i class="fas fa-moon"></i>';
        } else {
            themeIcon.innerHTML = '<i class="fas fa-sun"></i>';
        }
    }
}
