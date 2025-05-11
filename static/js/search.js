/**
 * Simple search functionality for Sunmax Inventory
 * This handles searching products and services by name or code
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Search.js loaded');

    // Get search elements
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const searchSuggestions = document.getElementById('search-suggestions');
    const searchResultsSummary = document.getElementById('search-results-summary');

    // Check if we're on the home page with search functionality
    if (!searchInput || !searchButton) {
        console.log('Search elements not found, not on home page');
        return;
    }

    console.log('Search elements found, initializing search functionality');

    // Initialize - show all items on page load
    showAllItems();

    // Add event listeners
    searchButton.addEventListener('click', function() {
        console.log('Search button clicked');
        performSearch();
    });

    searchInput.addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            console.log('Enter key pressed in search input');
            performSearch();
        }
    });

    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.trim();
        console.log('Search input changed:', searchTerm);

        if (searchTerm === '') {
            // If search is cleared, show all items and hide suggestions immediately
            showAllItems();
            hideSuggestions();

            // Also explicitly hide and clear the search results summary
            if (searchResultsSummary) {
                searchResultsSummary.classList.remove('active');
                searchResultsSummary.textContent = '';
            }

            console.log('Search cleared, hiding suggestions and results summary');
        } else {
            // Show suggestions as user types and filter items dynamically
            showSuggestions(searchTerm);
            filterItemsDynamically(searchTerm);
        }
    });

    // Hide suggestions when clicking outside
    document.addEventListener('click', function(event) {
        if (event.target !== searchInput &&
            event.target !== searchSuggestions &&
            !searchSuggestions.contains(event.target)) {
            hideSuggestions();
        }
    });

    /**
     * Show all product and service items
     */
    function showAllItems() {
        console.log('Showing all items');

        // Get all item cards
        const itemCards = document.querySelectorAll('.item-card');

        // Show all cards
        itemCards.forEach(card => {
            card.style.display = 'flex';
        });

        // Hide the search results summary
        if (searchResultsSummary) {
            searchResultsSummary.classList.remove('active');
            searchResultsSummary.textContent = ''; // Clear the text
        }

        // Hide "no items" messages if there are items
        updateNoItemsMessages();
    }

    /**
     * Perform search based on the current search input value
     */
    function performSearch() {
        const searchTerm = searchInput.value.trim().toLowerCase();
        console.log('Performing search for:', searchTerm);

        // Hide suggestions
        hideSuggestions();

        if (searchTerm === '') {
            showAllItems();
            return;
        }

        // Get all item cards
        const itemCards = document.querySelectorAll('.item-card');
        let visibleProducts = 0;
        let visibleServices = 0;

        // Filter items based on search term
        itemCards.forEach(card => {
            const nameElement = card.querySelector('h3');
            const codeElement = card.querySelector('.item-code');

            if (!nameElement || !codeElement) {
                console.error('Card missing name or code element:', card);
                return;
            }

            const name = nameElement.textContent.toLowerCase();
            const code = codeElement.textContent.toLowerCase();
            const isService = card.classList.contains('service-card');

            // Check if the item matches the search term
            const matches = name.includes(searchTerm) || code.includes(searchTerm);

            // Show or hide based on match
            if (matches) {
                card.style.display = 'flex';
                if (isService) {
                    visibleServices++;
                } else {
                    visibleProducts++;
                }
            } else {
                card.style.display = 'none';
            }
        });

        // Update search results summary
        if (searchResultsSummary) {
            const totalResults = visibleProducts + visibleServices;
            searchResultsSummary.textContent = `Found ${totalResults} items matching "${searchTerm}"`;
            searchResultsSummary.classList.add('active');
        }

        // Update "no items" messages
        updateNoItemsMessages();
    }

    /**
     * Show search suggestions based on the search term
     */
    function showSuggestions(searchTerm) {
        if (!searchSuggestions) return;

        // Clear previous suggestions
        searchSuggestions.innerHTML = '';

        if (searchTerm === '') {
            hideSuggestions();
            return;
        }

        // Get all item cards
        const itemCards = document.querySelectorAll('.item-card');
        const suggestions = [];

        // Find matching items
        itemCards.forEach(card => {
            const nameElement = card.querySelector('h3');
            const codeElement = card.querySelector('.item-code');

            if (!nameElement || !codeElement) return;

            const name = nameElement.textContent;
            const code = codeElement.textContent.replace('Code: ', '');
            const isService = card.classList.contains('service-card');

            // Check if the item matches the search term
            if (name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                code.toLowerCase().includes(searchTerm.toLowerCase())) {
                suggestions.push({
                    name: name,
                    code: code,
                    type: isService ? 'service' : 'product'
                });
            }
        });

        // Limit to 5 suggestions
        const limitedSuggestions = suggestions.slice(0, 5);
        console.log('Found suggestions:', limitedSuggestions);

        // Add suggestions to the dropdown
        if (limitedSuggestions.length > 0) {
            limitedSuggestions.forEach(suggestion => {
                const suggestionItem = document.createElement('div');
                suggestionItem.className = `suggestion-item ${suggestion.type}`;
                suggestionItem.innerHTML = `
                    <span class="suggestion-name">${suggestion.name}</span>
                    <span class="suggestion-code">${suggestion.code}</span>
                `;

                // Add click event to fill the search input and perform search
                suggestionItem.addEventListener('click', () => {
                    searchInput.value = suggestion.name;
                    performSearch();
                });

                searchSuggestions.appendChild(suggestionItem);
            });

            // Show the suggestions container
            searchSuggestions.classList.add('active');
        } else {
            // If no suggestions, show a "no results" message
            const noResults = document.createElement('div');
            noResults.className = 'suggestion-item no-results';
            noResults.textContent = `No matches found for "${searchTerm}"`;
            searchSuggestions.appendChild(noResults);
            searchSuggestions.classList.add('active');
        }
    }

    /**
     * Filter items dynamically as user types
     * This provides real-time filtering without waiting for search button click
     */
    function filterItemsDynamically(searchTerm) {
        console.log('Filtering items dynamically for:', searchTerm);

        if (!searchTerm) {
            showAllItems();
            return;
        }

        // Get all item cards
        const itemCards = document.querySelectorAll('.item-card');
        let visibleProducts = 0;
        let visibleServices = 0;

        // Filter items based on search term
        itemCards.forEach(card => {
            const nameElement = card.querySelector('h3');
            const codeElement = card.querySelector('.item-code');

            if (!nameElement || !codeElement) {
                console.error('Card missing name or code element:', card);
                return;
            }

            const name = nameElement.textContent.toLowerCase();
            const code = codeElement.textContent.toLowerCase();
            const isService = card.classList.contains('service-card');

            // Check if the item matches the search term
            const matches = name.includes(searchTerm.toLowerCase()) ||
                           code.includes(searchTerm.toLowerCase());

            // Show or hide based on match
            if (matches) {
                card.style.display = 'flex';
                if (isService) {
                    visibleServices++;
                } else {
                    visibleProducts++;
                }
            } else {
                card.style.display = 'none';
            }
        });

        // Update "no items" messages
        updateNoItemsMessages();

        // Update search results summary if needed
        if (searchResultsSummary) {
            const totalResults = visibleProducts + visibleServices;
            searchResultsSummary.textContent = `Found ${totalResults} items matching "${searchTerm}"`;
            searchResultsSummary.classList.add('active');
        }
    }

    /**
     * Hide search suggestions
     */
    function hideSuggestions() {
        if (searchSuggestions) {
            searchSuggestions.classList.remove('active');
            // Clear the suggestions content to ensure they're fully hidden
            searchSuggestions.innerHTML = '';
        }
    }

    /**
     * Update "no items" messages based on visible items
     */
    function updateNoItemsMessages() {
        // Check products section
        const productsSection = document.getElementById('products');
        if (productsSection) {
            const noProductsMessage = productsSection.querySelector('.no-items');
            const visibleProducts = productsSection.querySelectorAll('.item-card:not(.service-card)[style*="display: flex"]').length;

            if (noProductsMessage) {
                noProductsMessage.style.display = visibleProducts === 0 ? 'block' : 'none';
            }
        }

        // Check services section
        const servicesSection = document.getElementById('services');
        if (servicesSection) {
            const noServicesMessage = servicesSection.querySelector('.no-items');
            const visibleServices = servicesSection.querySelectorAll('.item-card.service-card[style*="display: flex"]').length;

            if (noServicesMessage) {
                noServicesMessage.style.display = visibleServices === 0 ? 'block' : 'none';
            }
        }
    }
});
