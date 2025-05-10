// Header scroll effect
document.addEventListener('DOMContentLoaded', function() {
    const headerWrapper = document.querySelector('.header-wrapper');
    
    // Function to handle scroll event
    function handleScroll() {
        if (window.scrollY > 10) {
            headerWrapper.classList.add('scrolled');
        } else {
            headerWrapper.classList.remove('scrolled');
        }
    }
    
    // Add scroll event listener
    window.addEventListener('scroll', handleScroll);
    
    // Initial check in case page is loaded scrolled
    handleScroll();
});
