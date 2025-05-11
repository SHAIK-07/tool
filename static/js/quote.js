// Quote management
let quoteItems = [];

// Load quote from localStorage on page load
document.addEventListener('DOMContentLoaded', function() {
    loadQuoteFromStorage();
    updateQuoteUI();

    // Add event listeners to "Add to Quote" buttons
    document.querySelectorAll('.add-to-quote-btn').forEach(button => {
        button.addEventListener('click', function() {
            const itemCode = this.getAttribute('data-id');
            const itemName = this.getAttribute('data-name');
            const price = this.getAttribute('data-price');
            const gstRate = this.getAttribute('data-gst');
            const type = this.getAttribute('data-type');

            // Get quantity from input field if it exists
            let quantity = 1;

            // Try to get quantity from product input field
            let quantityInput = document.getElementById(`qty-${itemCode}`);

            // If not found, try to get quantity from service input field
            if (!quantityInput && type === 'service') {
                quantityInput = document.getElementById(`qty-service-${itemCode}`);
            }

            if (quantityInput) {
                quantity = parseInt(quantityInput.value, 10);
                if (isNaN(quantity) || quantity < 1) {
                    quantity = 1;
                }
            }

            console.log(`Adding to quote: ${itemName}, quantity: ${quantity}`);
            addToQuote(itemCode, itemName, price, gstRate, type, quantity);
        });
    });

    // Close quote popup when clicking outside
    document.addEventListener('click', function(event) {
        const quotePopup = document.getElementById('quote-popup');
        const quoteToggleBtn = document.getElementById('quote-toggle-btn');

        if (quotePopup && quotePopup.classList.contains('show') &&
            !quotePopup.contains(event.target) &&
            quoteToggleBtn && !quoteToggleBtn.contains(event.target)) {
            hideQuotePopup();
        }
    });
});

// Add item to quote
function addToQuote(itemCode, itemName, price, gstRate, type, quantity = 1) {
    console.log(`addToQuote called with: ${itemCode}, ${itemName}, ${price}, ${gstRate}, ${type}, ${quantity}`);

    // Ensure quantity is a number
    quantity = parseInt(quantity, 10);
    if (isNaN(quantity) || quantity < 1) {
        quantity = 1;
    }

    console.log(`Processed quantity: ${quantity}`);

    // Check if item already exists in quote
    const existingItem = quoteItems.find(item => item.code === itemCode && item.type === type);

    if (existingItem) {
        // Replace the quantity with the new quantity
        console.log(`Item exists, current quantity: ${existingItem.quantity}, setting to: ${quantity}`);
        existingItem.quantity = quantity;
        console.log(`New quantity: ${existingItem.quantity}`);
    } else {
        // Add new item to quote
        console.log(`Adding new item with quantity: ${quantity}`);
        quoteItems.push({
            code: itemCode,
            name: itemName,
            price: parseFloat(price),
            gstRate: parseFloat(gstRate),
            quantity: quantity,
            type: type
        });
    }

    // Save quote to localStorage
    saveQuoteToStorage();

    // Update UI
    updateQuoteUI();

    // Show notification
    showNotification(`${quantity} ${itemName} added to quote`);

    // Show quote popup
    showQuotePopup();
}

// Update quote UI
function updateQuoteUI() {
    // Update quote count
    const quoteCount = document.getElementById('quote-toggle-count');
    const popupQuoteCount = document.getElementById('popup-quote-count');

    if (quoteCount && popupQuoteCount) {
        const totalItems = quoteItems.reduce((total, item) => total + item.quantity, 0);
        quoteCount.textContent = totalItems;
        popupQuoteCount.textContent = `${totalItems} item${totalItems !== 1 ? 's' : ''}`;
    }

    // Update quote popup body
    const quotePopupBody = document.getElementById('quote-popup-body');
    const quotePopupEmpty = document.getElementById('quote-popup-empty');

    if (quotePopupBody) {
        if (quoteItems.length === 0) {
            // Show empty message
            quotePopupBody.innerHTML = '<div class="quote-popup-empty"><p>Your quote is empty</p></div>';
        } else {
            // Generate quote items HTML
            let quoteItemsHTML = '';

            quoteItems.forEach((item, index) => {
                const itemTotal = item.price * item.quantity;

                quoteItemsHTML += `
                    <div class="quote-item">
                        <div class="quote-item-details">
                            <div class="quote-item-name">${item.name}</div>
                            <div class="quote-item-price">₹${item.price.toFixed(2)} x ${item.quantity}</div>
                        </div>
                        <div class="quote-item-actions">
                            <div class="quote-item-quantity">
                                <button onclick="decreaseQuoteItemQuantity(${index})">-</button>
                                <span>${item.quantity}</span>
                                <button onclick="increaseQuoteItemQuantity(${index})">+</button>
                            </div>
                            <button class="remove-quote-item" onclick="removeQuoteItem(${index})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `;
            });

            quotePopupBody.innerHTML = quoteItemsHTML;
        }
    }

    // Update quote total
    const quoteTotalAmount = document.getElementById('quote-popup-total-amount');

    if (quoteTotalAmount) {
        const subtotal = quoteItems.reduce((total, item) => total + (item.price * item.quantity), 0);
        const gstAmount = quoteItems.reduce((total, item) => total + (item.price * item.quantity * (item.gstRate / 100)), 0);
        const totalAmount = subtotal + gstAmount;

        quoteTotalAmount.textContent = `₹${totalAmount.toFixed(2)}`;
    }
}

// Save quote to localStorage
function saveQuoteToStorage() {
    localStorage.setItem('quoteItems', JSON.stringify(quoteItems));
}

// Load quote from localStorage
function loadQuoteFromStorage() {
    const storedQuote = localStorage.getItem('quoteItems');

    if (storedQuote) {
        quoteItems = JSON.parse(storedQuote);
    }
}

// Show/hide quote popup
function showQuotePopup(event) {
    const quotePopup = document.getElementById('quote-popup');

    if (quotePopup) {
        quotePopup.style.display = 'flex';
        quotePopup.classList.add('show');
    }

    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }
}

function hideQuotePopup(event) {
    const quotePopup = document.getElementById('quote-popup');

    if (quotePopup) {
        quotePopup.classList.remove('show');
        setTimeout(() => {
            quotePopup.style.display = 'none';
        }, 300);
    }

    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }
}

// Quote item quantity management
function increaseQuoteItemQuantity(index) {
    if (quoteItems[index]) {
        quoteItems[index].quantity += 1;
        saveQuoteToStorage();
        updateQuoteUI();
    }
}

function decreaseQuoteItemQuantity(index) {
    if (quoteItems[index] && quoteItems[index].quantity > 1) {
        quoteItems[index].quantity -= 1;
        saveQuoteToStorage();
        updateQuoteUI();
    }
}

function removeQuoteItem(index) {
    if (quoteItems[index]) {
        quoteItems.splice(index, 1);
        saveQuoteToStorage();
        updateQuoteUI();
    }
}

// Functions for quote cart page
function increaseQuoteItemQuantityByCode(itemCode) {
    const itemIndex = quoteItems.findIndex(item => item.code === itemCode);
    if (itemIndex !== -1) {
        quoteItems[itemIndex].quantity += 1;
        saveQuoteToStorage();
        updateQuoteUI();
        return true;
    }
    return false;
}

function decreaseQuoteItemQuantityByCode(itemCode) {
    const itemIndex = quoteItems.findIndex(item => item.code === itemCode);
    if (itemIndex !== -1 && quoteItems[itemIndex].quantity > 1) {
        quoteItems[itemIndex].quantity -= 1;
        saveQuoteToStorage();
        updateQuoteUI();
        return true;
    }
    return false;
}

function removeQuoteItemByCode(itemCode) {
    const itemIndex = quoteItems.findIndex(item => item.code === itemCode);
    if (itemIndex !== -1) {
        quoteItems.splice(itemIndex, 1);
        saveQuoteToStorage();
        updateQuoteUI();
        return true;
    }
    return false;
}

// Show notification
function showNotification(message) {
    // Check if notification container exists
    let notificationContainer = document.getElementById('notification-container');

    // Create container if it doesn't exist
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'notification-container';
        notificationContainer.style.position = 'fixed';
        notificationContainer.style.bottom = '20px';
        notificationContainer.style.right = '20px';
        notificationContainer.style.zIndex = '9999';
        document.body.appendChild(notificationContainer);
    }

    // Create notification
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.style.backgroundColor = '#4285f4';
    notification.style.color = 'white';
    notification.style.padding = '10px 20px';
    notification.style.borderRadius = '4px';
    notification.style.marginTop = '10px';
    notification.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
    notification.style.transition = 'opacity 0.3s, transform 0.3s';
    notification.style.opacity = '0';
    notification.style.transform = 'translateY(20px)';
    notification.textContent = message;

    // Add to container
    notificationContainer.appendChild(notification);

    // Trigger animation
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    }, 10);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(20px)';

        setTimeout(() => {
            notificationContainer.removeChild(notification);
        }, 300);
    }, 3000);
}
