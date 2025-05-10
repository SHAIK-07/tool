// Sunmax Renewable App JavaScript
console.log("Sunmax Renewable app initialized");

// Cart functionality
let cart;

// Initialize cart from localStorage
try {
    const savedCart = localStorage.getItem('cart');
    console.log("Saved cart from localStorage:", savedCart);
    cart = savedCart ? JSON.parse(savedCart) : [];
    console.log("Initialized cart:", cart);
} catch (error) {
    console.error("Error loading cart from localStorage:", error);
    cart = [];
}

// Increment quantity in input field
function incrementQuantity(inputId, maxQuantity) {
    const input = document.getElementById(inputId);
    if (!input) return;

    let value = parseInt(input.value, 10);
    if (isNaN(value)) value = 0;

    if (maxQuantity && value >= maxQuantity) {
        showNotification(`Maximum available quantity is ${maxQuantity}`);
        return;
    }

    input.value = value + 1;
}

// Decrement quantity in input field
function decrementQuantity(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;

    let value = parseInt(input.value, 10);
    if (isNaN(value) || value <= 1) {
        input.value = 1;
        return;
    }

    input.value = value - 1;
}

// Add item to cart
function addToCart(itemId, itemName, price, gstRate, availableQuantity, itemType = 'product') {
    console.log("Adding to cart:", { itemId, itemName, price, gstRate, availableQuantity, itemType });

    // Initialize cart if it doesn't exist
    if (!cart) {
        cart = [];
    }

    // Get quantity from input field if it exists
    let quantity = 1;
    const quantityInput = document.getElementById(`qty-${itemId}`);
    if (quantityInput) {
        quantity = parseInt(quantityInput.value, 10);
        if (isNaN(quantity) || quantity < 1) {
            quantity = 1;
        }
    }

    // Check if item already exists in cart
    const existingItemIndex = cart.findIndex(item => item.id === itemId);

    // Calculate current quantity in cart
    let currentCartQuantity = 0;
    if (existingItemIndex !== -1) {
        currentCartQuantity = cart[existingItemIndex].quantity;
    }

    // Check if there's enough stock available (only for products, not services)
    if (itemType === 'product' && availableQuantity !== undefined && (currentCartQuantity + quantity) > availableQuantity) {
        showNotification(`Sorry, only ${availableQuantity} units available in stock.`);
        return;
    }

    if (existingItemIndex !== -1) {
        // Item exists, add the selected quantity
        cart[existingItemIndex].quantity += quantity;
        console.log("Increased quantity for existing item:", cart[existingItemIndex]);
    } else {
        // Add new item to cart with the selected quantity
        const newItem = {
            id: itemId,
            item_name: itemName,
            price: parseFloat(price),
            quantity: quantity,
            discount: 0, // Initialize with 0% discount
            gst_rate: parseFloat(gstRate),
            item_type: itemType // Add item type (product or service)
        };
        cart.push(newItem);
        console.log("Added new item to cart:", newItem);
    }

    // Reserve the stock by making an API call (only for products)
    if (itemType === 'product') {
        reserveStock(itemId, quantity);
    }

    // Reset discount applied flag when adding new items
    localStorage.removeItem('discountApplied');

    // Save cart to localStorage
    saveCart();

    // Show notification
    showNotification(`${quantity} ${itemName} added to cart`);

    // Show cart popup if the global function exists
    if (typeof window.showCartPopup === 'function') {
        console.log('Showing cart popup after adding item');
        window.showCartPopup();
    }
}

// Reserve stock temporarily
function reserveStock(itemId, quantity) {
    fetch('/api/reserve-stock', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            item_code: itemId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Stock reservation response:", data);
        if (!data.success) {
            showNotification(data.message || "Could not reserve stock");
            // If there's an error, update the UI to show the correct stock
            if (data.message && data.message.includes("Only")) {
                // Extract the available quantity from the error message
                const availableMatch = data.message.match(/Only (\d+) units available/);
                if (availableMatch && availableMatch[1]) {
                    const availableQuantity = parseInt(availableMatch[1], 10);
                    updateProductQuantityDisplay(itemId, availableQuantity);
                }
            }
        } else if (data.new_quantity !== undefined) {
            // Update the UI to show the new stock quantity
            updateProductQuantityDisplay(itemId, data.new_quantity);
        }
    })
    .catch(error => {
        console.error("Error reserving stock:", error);
    });
}

// Update product quantity display in the UI
function updateProductQuantityDisplay(itemId, newQuantity) {
    // Update quantity display in product cards
    const stockElements = document.querySelectorAll(`.item-stock[data-id="${itemId}"]`);
    stockElements.forEach(element => {
        if (newQuantity > 0) {
            element.innerHTML = `<span>In Stock: ${newQuantity}</span>`;

            // Update class based on quantity
            if (newQuantity < 5) {
                element.classList.add('low-stock');
                element.classList.remove('out-of-stock');
            } else {
                element.classList.remove('low-stock');
                element.classList.remove('out-of-stock');
            }
        } else {
            element.innerHTML = `<span class="out-of-stock">Out of Stock</span>`;
            element.classList.remove('low-stock');
            element.classList.add('out-of-stock');
        }
    });

    // Update add to cart buttons
    const addToCartButtons = document.querySelectorAll(`.add-to-cart-btn[data-id="${itemId}"]`);
    addToCartButtons.forEach(button => {
        button.setAttribute('data-quantity', newQuantity);

        if (newQuantity <= 0) {
            button.disabled = true;
            button.textContent = 'Out of Stock';
        } else {
            button.disabled = false;
            button.textContent = 'Add to Cart';
        }
    });

    // Update quantity inputs max value
    const quantityInputs = document.querySelectorAll(`input[id^="qty-${itemId}"]`);
    quantityInputs.forEach(input => {
        input.setAttribute('max', newQuantity);

        // If current value is greater than new max, adjust it
        if (parseInt(input.value, 10) > newQuantity) {
            input.value = newQuantity;
        }

        // Disable if out of stock
        input.disabled = newQuantity <= 0;
    });
}

// Update item quantity in cart
function updateQuantity(itemId, change) {
    const itemIndex = cart.findIndex(item => item.id === itemId);

    if (itemIndex !== -1) {
        const item = cart[itemIndex];
        const isProduct = !item.item_type || item.item_type === 'product';

        // Only handle stock for products, not services
        if (isProduct) {
            // If decreasing quantity, release stock
            if (change < 0) {
                releaseStock(itemId, Math.abs(change));
            }
            // If increasing quantity, reserve more stock
            else if (change > 0) {
                reserveStock(itemId, change);
            }
        }

        cart[itemIndex].quantity += change;

        // Remove item if quantity is 0 or less
        if (cart[itemIndex].quantity <= 0) {
            removeItem(itemId);
            return;
        }

        // Update quantity display
        document.getElementById(`quantity-${itemId}`).textContent = cart[itemIndex].quantity;

        // Reset discount applied flag when changing quantity
        localStorage.removeItem('discountApplied');

        // Save cart and update totals
        saveCart();
        updateCartTotals();

        // Update cart display if on cart page
        if (window.location.pathname === '/cart') {
            renderCartItems();
        }
    }
}

// Update item discount in cart
function updateDiscount(itemId, discountValue) {
    const itemIndex = cart.findIndex(item => item.id === itemId);

    if (itemIndex !== -1) {
        // Parse discount value and ensure it's a valid number between 0 and 100
        let discount = parseFloat(discountValue);
        if (isNaN(discount)) discount = 0;
        if (discount < 0) discount = 0;
        if (discount > 100) discount = 100;

        // Update the discount in the cart
        cart[itemIndex].discount = discount;

        // Update the input field with the validated value
        const discountInput = document.getElementById(`discount-${itemId}`);
        if (discountInput) {
            discountInput.value = discount;
        }

        // Set the discount applied flag
        localStorage.setItem('discountApplied', 'true');

        // Save cart and update totals
        saveCart();
        updateCartTotals();

        // Show notification
        showNotification(`Discount of ${discount}% applied to ${cart[itemIndex].item_name}`);

        // Update cart display if on cart page
        if (window.location.pathname === '/cart') {
            renderCartItems();
        }
    }
}

// Remove item from cart
function removeItem(itemId) {
    // Find the item to get its quantity before removing
    const item = cart.find(item => item.id === itemId);
    if (item) {
        // Release the reserved stock (only for products)
        if (!item.item_type || item.item_type === 'product') {
            releaseStock(itemId, item.quantity);
        }
    }

    // Remove from cart
    cart = cart.filter(item => item.id !== itemId);
    saveCart();

    // Remove discount applied flag if cart is empty
    if (cart.length === 0) {
        localStorage.removeItem('discountApplied');
    }

    // Update cart display if on cart page
    if (window.location.pathname === '/cart') {
        renderCartItems();
    } else {
        // Update cart popup
        updateCartPopup();
    }
}

// Function to populate the items list in the discount form
function populateDiscountItemsList(cart) {
    const itemsList = document.getElementById('discount-items-list');
    if (!itemsList) return;

    itemsList.innerHTML = '';

    cart.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span>${item.item_name} (${item.quantity} x ₹${item.price.toFixed(2)})</span>
            <span>₹${(item.price * item.quantity).toFixed(2)}</span>
        `;
        itemsList.appendChild(li);
    });
}

// Function to apply global discount to all items
function applyGlobalDiscount() {
    // Get discount value
    const discountInput = document.getElementById('global-discount');
    let discount = parseFloat(discountInput.value);

    // Validate discount
    if (isNaN(discount)) discount = 0;
    if (discount < 0) discount = 0;
    if (discount > 100) discount = 100;

    // Update discount input with validated value
    discountInput.value = discount;

    // Apply discount to all items
    cart.forEach(item => {
        item.discount = discount;
    });

    // Save updated cart
    saveCart();

    // Set flag that discount has been applied
    localStorage.setItem('discountApplied', 'true');

    // Show cart details
    document.querySelector('.empty-cart').style.display = 'none';
    document.getElementById('cart-details-container').style.display = 'block';

    // Render cart items
    renderCartItems();

    // Show notification
    showNotification(`Discount of ${discount}% applied to all items`);
}

// Function to reset discount
function resetDiscount() {
    // Reset all item discounts to 0
    cart.forEach(item => {
        item.discount = 0;
    });

    // Save updated cart
    saveCart();

    // Remove discount applied flag
    localStorage.removeItem('discountApplied');

    // Update the cart display without reloading
    renderCartItems();

    // Show notification
    showNotification('Discounts have been reset');
}

// Release reserved stock
function releaseStock(itemId, quantity) {
    fetch('/api/release-stock', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            item_code: itemId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Stock release response:", data);
        if (data.success && data.new_quantity !== undefined) {
            // Update the UI to show the new stock quantity
            updateProductQuantityDisplay(itemId, data.new_quantity);
        }
    })
    .catch(error => {
        console.error("Error releasing stock:", error);
    });
}

// Save cart to localStorage
function saveCart() {
    try {
        console.log("Saving cart to localStorage:", cart);
        localStorage.setItem('cart', JSON.stringify(cart));
        console.log("Cart saved successfully");
    } catch (error) {
        console.error("Error saving cart to localStorage:", error);
    }

    // Update cart count in header
    updateCartCount();
}

// Update cart count display
function updateCartCount() {
    const cartCount = cart.reduce((total, item) => total + item.quantity, 0);

    // Update header cart count
    const cartCountElement = document.getElementById('cart-count');
    if (cartCountElement) {
        cartCountElement.textContent = cartCount;
        cartCountElement.style.display = cartCount > 0 ? 'inline-block' : 'none';
    }

    // Update cart popup toggle button count
    const cartToggleCount = document.getElementById('cart-toggle-count');
    if (cartToggleCount) {
        cartToggleCount.textContent = cartCount;
        // Always show the count badge, even if it's 0
        cartToggleCount.style.display = 'flex';
    }

    // Update cart popup count
    const popupCartCount = document.getElementById('popup-cart-count');
    if (popupCartCount) {
        popupCartCount.textContent = cartCount;
    }

    // Update cart popup content
    updateCartPopup();
}

// Update cart totals
function updateCartTotals() {
    console.log("Updating cart totals");

    if (!cart || cart.length === 0) {
        console.log("Cart is empty, no totals to update");
        return;
    }

    const subtotal = cart.reduce((total, item) => total + (item.price * item.quantity), 0);

    // Calculate total discount
    const totalDiscount = cart.reduce((total, item) => {
        const itemSubtotal = item.price * item.quantity;
        const discountAmount = itemSubtotal * ((item.discount || 0) / 100);
        return total + discountAmount;
    }, 0);

    // Calculate Taxable Amount (Subtotal - Discount)
    const taxableAmount = subtotal - totalDiscount;

    // Calculate GST on Taxable Amount
    const gstAmount = cart.reduce((total, item) => {
        const itemSubtotal = item.price * item.quantity;
        const discountAmount = itemSubtotal * ((item.discount || 0) / 100);
        const discountedSubtotal = itemSubtotal - discountAmount;
        const itemGst = discountedSubtotal * (item.gst_rate / 100);
        return total + itemGst;
    }, 0);

    // Total = Taxable Amount + GST
    const total = taxableAmount + gstAmount;

    console.log("Cart totals:", { subtotal, totalDiscount, taxableAmount, gstAmount, total });

    // Update display if elements exist
    const summaryRows = document.querySelectorAll('.summary-row');
    if (summaryRows && summaryRows.length >= 5) {
        // Update subtotal
        const subtotalElement = summaryRows[0].querySelector('span:last-child');
        if (subtotalElement) {
            subtotalElement.textContent = `₹${subtotal.toFixed(2)}`;
        }

        // Update discount
        const discountElement = summaryRows[1].querySelector('span:last-child');
        if (discountElement) {
            discountElement.textContent = `₹${totalDiscount.toFixed(2)}`;
        }

        // Update Taxable Amount
        const taxableAmountElement = summaryRows[2].querySelector('span:last-child');
        if (taxableAmountElement) {
            taxableAmountElement.textContent = `₹${taxableAmount.toFixed(2)}`;
        }

        // Update GST amount
        const gstElement = summaryRows[3].querySelector('span:last-child');
        if (gstElement) {
            gstElement.textContent = `₹${gstAmount.toFixed(2)}`;
        }

        // Update total
        const totalElement = document.querySelector('.summary-row.total span:last-child');
        if (totalElement) {
            totalElement.textContent = `₹${total.toFixed(2)}`;
        }
    } else {
        console.error("Could not find summary rows to update totals");
    }
}

// Render cart items
function renderCartItems() {
    console.log("Rendering cart items:", cart);

    const cartDetailsContainer = document.getElementById('cart-details-container');
    const emptyCartContainer = document.querySelector('.empty-cart');

    if (!cart || cart.length === 0) {
        console.log("Cart is empty, showing empty cart message");
        // Show empty cart message
        if (cartDetailsContainer) cartDetailsContainer.style.display = 'none';
        if (emptyCartContainer) emptyCartContainer.style.display = 'block';
        return;
    }

    console.log("Cart has items, showing cart details");

    // Always show cart details
    if (emptyCartContainer) emptyCartContainer.style.display = 'none';
    if (cartDetailsContainer) cartDetailsContainer.style.display = 'block';

    // Get the tbody element to populate with cart items
    const tbody = document.querySelector('.cart-table tbody');
    if (!tbody) {
        console.error("Could not find cart table tbody element");
        return;
    }

    // Clear existing rows
    tbody.innerHTML = '';

    // Calculate item totals
    const itemsWithTotals = cart.map(item => {
        // Ensure discount exists and is a number
        if (item.discount === undefined) {
            item.discount = 0;
        }

        const itemSubtotal = item.price * item.quantity;
        const discountAmount = itemSubtotal * (item.discount / 100);
        const discountedSubtotal = itemSubtotal - discountAmount;
        const itemGst = discountedSubtotal * (item.gst_rate / 100);
        const itemTotal = discountedSubtotal + itemGst;

        return {
            ...item,
            subtotal: itemSubtotal,
            discount_amount: discountAmount,
            discounted_subtotal: discountedSubtotal,
            gst_amount: itemGst,
            total: itemTotal
        };
    });

    console.log("Items with totals:", itemsWithTotals);

    // Add rows for each item
    itemsWithTotals.forEach(item => {
        const row = document.createElement('tr');
        const itemType = item.item_type || 'product';
        const typeClass = `item-type-${itemType}`;

        row.innerHTML = `
            <td>${item.item_name}</td>
            <td>
                <span class="item-type-badge ${typeClass}">${itemType.charAt(0).toUpperCase() + itemType.slice(1)}</span>
            </td>
            <td>₹${item.price.toFixed(2)}</td>
            <td>
                <div class="quantity-control">
                    <button class="quantity-btn" onclick="updateQuantity('${item.id}', -1)">-</button>
                    <span id="quantity-${item.id}">${item.quantity}</span>
                    <button class="quantity-btn" onclick="updateQuantity('${item.id}', 1)">+</button>
                </div>
            </td>
            <td>
                <div class="discount-control">
                    <input type="number"
                           id="discount-${item.id}"
                           class="discount-input"
                           value="${item.discount || 0}"
                           min="0"
                           max="100"
                           step="0.1"
                           onchange="updateDiscount('${item.id}', this.value)">
                </div>
            </td>
            <td>₹${item.discounted_subtotal.toFixed(2)}</td>
            <td>${item.gst_rate}% (₹${item.gst_amount.toFixed(2)})</td>
            <td>₹${item.total.toFixed(2)}</td>
            <td><button class="remove-btn" onclick="removeItem('${item.id}')">Remove</button></td>
        `;
        tbody.appendChild(row);
    });

    // Update cart totals
    updateCartTotals();
}

// Checkout function
function checkout() {
    // Check if cart is empty
    if (!cart || cart.length === 0) {
        showNotification('Your cart is empty. Add some items before checkout.');
        return;
    }

    // Redirect to checkout page
    window.location.href = '/checkout';
}

// Download invoice as PDF
function downloadInvoice(invoiceNumber) {
    window.location.href = `/api/invoices/download/${invoiceNumber}`;
}

// Show notification
function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;

    document.body.appendChild(notification);

    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    // Hide and remove notification after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Product details modal functionality
function openProductModal(itemId) {
    // Get product details from API
    fetch(`/api/inventory/item/${itemId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showNotification(data.error);
                return;
            }

            // Populate modal with product details
            const detailsContainer = document.getElementById('product-details-container');
            detailsContainer.innerHTML = `
                <div class="product-details">
                    <div class="product-header">
                        <h2>${data.item_name}</h2>
                        <div class="product-code">Code: ${data.item_code}</div>
                    </div>

                    <div class="product-info">
                        <div class="info-row">
                            <span class="info-label">HSN Code:</span>
                            <span class="info-value">${data.hsn_code}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Buy Price:</span>
                            <span class="info-value">₹${data.purchase_price_per_unit}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Margin:</span>
                            <span class="info-value">${data.margin || 20}%</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Selling Price:</span>
                            <span class="info-value">₹${(data.purchase_price_per_unit * (1 + ((data.margin || 20) / 100))).toFixed(2)}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">GST Rate:</span>
                            <span class="info-value">${data.gst_rate}%</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Available Quantity:</span>
                            <span class="info-value">${data.quantity}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Supplier:</span>
                            <span class="info-value">${data.supplier_name}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Supplier GST:</span>
                            <span class="info-value">${data.supplier_gst_number}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Added On:</span>
                            <span class="info-value">${new Date(data.date).toLocaleDateString()}</span>
                        </div>
                    </div>

                    <div class="product-actions">
                        <button class="add-to-cart-btn modal-add-btn"
                            data-id="${data.item_code}"
                            data-name="${data.item_name}"
                            data-price="${(data.purchase_price_per_unit * (1 + ((data.margin || 20) / 100))).toFixed(2)}"
                            data-gst="${data.gst_rate}"
                            data-quantity="${data.quantity}"
                            ${data.quantity <= 0 ? 'disabled' : ''}>
                            ${data.quantity > 0 ? 'Add to Cart' : 'Out of Stock'}
                        </button>
                    </div>
                </div>
            `;

            // Add event listener to the Add to Cart button in modal
            const addBtn = detailsContainer.querySelector('.modal-add-btn');
            if (addBtn && !addBtn.disabled) {
                addBtn.addEventListener('click', function() {
                    const itemId = this.getAttribute('data-id');
                    const itemName = this.getAttribute('data-name');
                    const price = this.getAttribute('data-price');
                    const gstRate = this.getAttribute('data-gst');
                    const quantity = this.getAttribute('data-quantity');

                    addToCart(itemId, itemName, price, gstRate, parseInt(quantity, 10));

                    // Close modal after adding to cart
                    closeModal();
                });
            }

            // Show modal
            const modal = document.getElementById('product-modal');
            modal.style.display = 'flex';
        })
        .catch(error => {
            console.error('Error fetching product details:', error);
            showNotification('Error loading product details. Please try again.');
        });
}

// Service details modal functionality
function openServiceModal(serviceId) {
    console.log('Opening service modal for ID:', serviceId, 'Type:', typeof serviceId);

    try {
        // Convert serviceId to integer if it's a string
        const serviceIdInt = parseInt(serviceId, 10);
        if (isNaN(serviceIdInt)) {
            console.error('Invalid service ID:', serviceId);
            showNotification('Invalid service ID');
            return;
        }

        // Get service details from API
        const url = `/api/services/item/${serviceIdInt}`;
        console.log('Fetching from URL:', url);

        // Show a notification that we're fetching service details
        showNotification('Fetching service details...');

        fetch(url)
            .then(response => {
                console.log('Response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Service data received:', data);

                if (data.error) {
                    showNotification(data.error);
                    return;
                }

                // Calculate total price with GST
                const totalPrice = data.price + (data.price * data.gst_rate / 100);

                // Populate modal with service details
                const detailsContainer = document.getElementById('product-details-container');
                detailsContainer.innerHTML = `
                    <div class="product-details">
                        <div class="product-header">
                            <h2>${data.service_name}</h2>
                            <div class="product-code">Code: ${data.service_code}</div>
                        </div>
                        <div class="product-info">
                            <div class="info-row">
                                <span class="info-label">Date:</span>
                                <span class="info-value">${data.date}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Employee:</span>
                                <span class="info-value">${data.employee_name}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Description:</span>
                                <span class="info-value">${data.description || 'No description'}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Price:</span>
                                <span class="info-value">₹${data.price.toFixed(2)}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">GST Rate:</span>
                                <span class="info-value">${data.gst_rate}%</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Total Price:</span>
                                <span class="info-value">₹${totalPrice.toFixed(2)}</span>
                            </div>
                        </div>
                        <div class="product-actions">
                            <button class="add-to-cart-btn modal-add-btn"
                                data-id="${data.service_code}"
                                data-name="${data.service_name}"
                                data-price="${data.price.toFixed(2)}"
                                data-gst="${data.gst_rate}"
                                data-type="service">
                                Add to Cart
                            </button>
                        </div>
                    </div>
                `;

                // Add event listener to the Add to Cart button in modal
                const addBtn = detailsContainer.querySelector('.modal-add-btn');
                if (addBtn) {
                    addBtn.addEventListener('click', function() {
                        const itemId = this.getAttribute('data-id');
                        const itemName = this.getAttribute('data-name');
                        const price = this.getAttribute('data-price');
                        const gstRate = this.getAttribute('data-gst');
                        const itemType = this.getAttribute('data-type');

                        addToCart(itemId, itemName, price, gstRate, undefined, itemType);

                        // Close modal after adding to cart
                        closeModal();
                    });
                }

                // Show modal
                const modal = document.getElementById('product-modal');
                modal.style.display = 'flex';
            })
            .catch(error => {
                console.error('Error fetching service details:', error);
                showNotification('Error loading service details. Please try again.');
            });
    } catch (e) {
        console.error('Error in openServiceModal:', e);
        showNotification('Error opening service modal: ' + e.message);
    }
}

// Close modal
function closeModal() {
    const modal = document.getElementById('product-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Product search functionality
function searchProducts() {
    const searchInput = document.getElementById('product-search');
    const searchTerm = searchInput.value.toLowerCase();
    const itemCards = document.querySelectorAll('.item-card');

    itemCards.forEach(card => {
        const itemName = card.querySelector('h3').textContent.toLowerCase();
        const itemCode = card.querySelector('.item-code').textContent.toLowerCase();

        if (itemName.includes(searchTerm) || itemCode.includes(searchTerm)) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

// Toggle item edit mode in inventory
function toggleItemEdit(itemCode) {
    const row = document.getElementById(`row-${itemCode}`);

    // Get all view and edit content elements in the row
    const viewContents = row.querySelectorAll('.view-content');
    const editContents = row.querySelectorAll('.edit-content');

    // Check if already in edit mode (first edit content is visible)
    if (editContents[0].style.display !== 'none') {
        // Cancel edit mode
        cancelItemEdit(itemCode);
    } else {
        // Enter edit mode
        viewContents.forEach(el => {
            el.style.display = 'none';
        });

        editContents.forEach(el => {
            el.style.display = 'block';
        });

        // Focus on the first input
        const firstInput = row.querySelector('.edit-input');
        if (firstInput) {
            firstInput.focus();
        }
    }
}

// Cancel item edit mode
function cancelItemEdit(itemCode) {
    const row = document.getElementById(`row-${itemCode}`);

    // Get all view and edit content elements in the row
    const viewContents = row.querySelectorAll('.view-content');
    const editContents = row.querySelectorAll('.edit-content');

    // Show view mode, hide edit mode
    viewContents.forEach(el => {
        el.style.display = '';
    });

    editContents.forEach(el => {
        el.style.display = 'none';
    });
}

// Save item edits
function saveItemEdit(itemCode) {
    // Get all the input values
    const nameInput = document.getElementById(`name-${itemCode}`);
    const hsnInput = document.getElementById(`hsn-${itemCode}`);
    const priceInput = document.getElementById(`price-${itemCode}`);
    const gstInput = document.getElementById(`gst-${itemCode}`);
    const quantityInput = document.getElementById(`quantity-${itemCode}`);
    const unitInput = document.getElementById(`unit-${itemCode}`);
    const supplierInput = document.getElementById(`supplier-${itemCode}`);

    // Validate inputs
    if (!nameInput.value.trim()) {
        showNotification('Item name cannot be empty');
        nameInput.focus();
        return;
    }

    if (!hsnInput.value.trim()) {
        showNotification('HSN code cannot be empty');
        hsnInput.focus();
        return;
    }

    const price = parseFloat(priceInput.value);
    if (isNaN(price) || price < 0) {
        showNotification('Please enter a valid price');
        priceInput.focus();
        return;
    }

    const gst = parseFloat(gstInput.value);
    if (isNaN(gst) || gst < 0) {
        showNotification('Please enter a valid GST rate');
        gstInput.focus();
        return;
    }

    const quantity = parseInt(quantityInput.value, 10);
    if (isNaN(quantity) || quantity < 0) {
        showNotification('Please enter a valid quantity');
        quantityInput.focus();
        return;
    }

    // Get margin input
    const marginInput = document.getElementById(`margin-${itemCode}`);
    const margin = parseFloat(marginInput.value);
    if (isNaN(margin) || margin < 0) {
        showNotification('Please enter a valid margin');
        marginInput.focus();
        return;
    }

    // Create the update data object
    const updateData = {
        item_name: nameInput.value.trim(),
        hsn_code: hsnInput.value.trim(),
        purchase_price_per_unit: price,
        margin: margin,
        gst_rate: gst,
        quantity: quantity,
        unit_of_measurement: unitInput.value,
        supplier_name: supplierInput.value.trim()
    };

    // Send AJAX request to update the item
    fetch(`/api/inventory/update-item/${itemCode}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Item updated successfully');

            // Update the displayed values in view mode
            const row = document.getElementById(`row-${itemCode}`);

            // Update each view content with the new values
            const cells = row.querySelectorAll('td');
            cells[1].querySelector('.view-content').textContent = updateData.item_name;
            cells[2].querySelector('.view-content').textContent = updateData.hsn_code;
            cells[3].querySelector('.view-content').textContent = updateData.purchase_price_per_unit;
            cells[4].querySelector('.view-content').textContent = updateData.margin + '%';

            // Calculate and update selling price
            const sellingPrice = updateData.purchase_price_per_unit * (1 + (updateData.margin / 100));
            cells[5].querySelector('.view-content').textContent = sellingPrice.toFixed(2);

            cells[6].querySelector('.view-content').textContent = updateData.gst_rate + '%';
            cells[7].querySelector('.view-content').textContent = updateData.quantity;
            cells[8].querySelector('.view-content').textContent = updateData.unit_of_measurement;
            cells[9].querySelector('.view-content').textContent = updateData.supplier_name;

            // Exit edit mode
            cancelItemEdit(itemCode);
        } else {
            showNotification('Error updating item: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error updating item:', error);
        showNotification('Error updating item. Please try again.');
    });
}

// Delete item confirmation
let itemToDelete = null;

function confirmDeleteItem(itemCode, itemName) {
    console.log('Confirming delete for item:', itemCode, itemName);

    // Store the item code to delete
    itemToDelete = itemCode;

    // Update the modal with item details
    const itemNameElement = document.getElementById('delete-item-name');
    if (itemNameElement) {
        itemNameElement.textContent = `${itemName} (${itemCode})`;
    } else {
        console.error('Element with ID "delete-item-name" not found');
    }

    // Show the modal
    const modal = document.getElementById('delete-modal');
    if (modal) {
        console.log('Showing delete modal');
        modal.classList.remove('hidden');
        modal.style.display = 'flex';  // Use flex to center the content
    } else {
        console.error('Element with ID "delete-modal" not found');
    }
}

function closeDeleteModal() {
    // Hide the modal
    const modal = document.getElementById('delete-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.style.display = 'none';
    }

    // Clear the item to delete
    itemToDelete = null;
}

function deleteItem() {
    // Check if we have an item to delete
    if (!itemToDelete) {
        showNotification('No item selected for deletion');
        return;
    }

    console.log('Deleting item:', itemToDelete);

    // Enhanced debugging
    const deleteUrl = `/api/inventory/delete/${itemToDelete}`;
    console.log('Delete URL:', deleteUrl);

    // Send request to delete the item
    fetch(deleteUrl, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log('Delete response status:', response.status);
        if (!response.ok) {
            console.error('Delete response not OK:', response.statusText);
        }
        return response.json();
    })
    .then(data => {
        console.log('Delete response data:', data);
        if (data.success) {
            showNotification(data.message || 'Item deleted successfully');

            // Remove the row from the table
            const row = document.getElementById(`row-${itemToDelete}`);
            if (row) {
                row.remove();
            }

            // Close the modal
            closeDeleteModal();

            // Reload the page after a longer delay to ensure the database operation completes
            setTimeout(() => {
                location.reload();
            }, 2500);
        } else {
            showNotification(data.message || 'Error deleting item');
        }
    })
    .catch(error => {
        console.error('Error deleting item:', error);
        showNotification('Error deleting item. Please try again.');
    });
}

// Update cart popup content
function updateCartPopup() {
    console.log('Updating cart popup content');
    const popupBody = document.getElementById('cart-popup-body');
    const emptyCartMessage = document.getElementById('cart-popup-empty');
    const totalAmountElement = document.getElementById('cart-popup-total-amount');

    if (!popupBody || !emptyCartMessage || !totalAmountElement) {
        console.error('Cart popup elements not found');
        return;
    }

    // Clear existing items (except the empty cart message)
    const existingItems = popupBody.querySelectorAll('.cart-popup-item');
    existingItems.forEach(item => item.remove());

    // Show/hide empty cart message
    if (!cart || cart.length === 0) {
        console.log('Cart is empty');
        emptyCartMessage.style.display = 'block';
        totalAmountElement.textContent = '₹0.00';
        return;
    }

    console.log('Cart has items:', cart.length);
    emptyCartMessage.style.display = 'none';

    // Calculate total with Taxable Amount
    const total = cart.reduce((total, item) => {
        const itemSubtotal = item.price * item.quantity;
        const discountAmount = itemSubtotal * ((item.discount || 0) / 100);
        const taxableAmount = itemSubtotal - discountAmount;
        const itemGst = taxableAmount * (item.gst_rate / 100);
        return total + taxableAmount + itemGst;
    }, 0);

    // Update total amount
    totalAmountElement.textContent = `₹${total.toFixed(2)}`;

    // Add cart items to popup
    cart.forEach(item => {
        const itemElement = document.createElement('div');
        itemElement.className = 'cart-popup-item';

        const itemSubtotal = item.price * item.quantity;
        const discountAmount = itemSubtotal * ((item.discount || 0) / 100);
        const taxableAmount = itemSubtotal - discountAmount;
        const itemGst = taxableAmount * (item.gst_rate / 100);
        const itemTotal = taxableAmount + itemGst;

        itemElement.innerHTML = `
            <div class="cart-item-details">
                <div class="cart-item-name">${item.item_name}</div>
                <div class="cart-item-price">₹${item.price.toFixed(2)} × ${item.quantity} = ₹${itemTotal.toFixed(2)}</div>
            </div>
            <div class="cart-item-quantity">
                <button class="cart-quantity-btn" onclick="updatePopupQuantity('${item.id}', -1)">-</button>
                <span>${item.quantity}</span>
                <button class="cart-quantity-btn" onclick="updatePopupQuantity('${item.id}', 1)">+</button>
                <button class="cart-item-remove" onclick="removePopupItem('${item.id}')"><i class="fas fa-trash"></i></button>
            </div>
        `;

        popupBody.insertBefore(itemElement, emptyCartMessage);
    });

    // If we have a global showCartPopup function, use it to show the popup
    if (typeof window.showCartPopup === 'function' && cart.length > 0) {
        console.log('Using global showCartPopup function');
        // Don't automatically show the popup, just update its content
    }
}

// Update item quantity from popup
function updatePopupQuantity(itemId, change) {
    const itemIndex = cart.findIndex(item => item.id === itemId);

    if (itemIndex !== -1) {
        // If decreasing quantity, release stock
        if (change < 0) {
            releaseStock(itemId, Math.abs(change));
        }
        // If increasing quantity, reserve more stock
        else if (change > 0) {
            reserveStock(itemId, change);
        }

        cart[itemIndex].quantity += change;

        // Remove item if quantity is 0 or less
        if (cart[itemIndex].quantity <= 0) {
            removePopupItem(itemId);
            return;
        }

        // Save cart and update UI
        saveCart();
        updateCartPopup();
    }
}

// Remove item from cart via popup
function removePopupItem(itemId) {
    // Find the item to get its quantity before removing
    const item = cart.find(item => item.id === itemId);
    if (item) {
        // Release the reserved stock
        releaseStock(itemId, item.quantity);
    }

    // Remove from cart
    cart = cart.filter(item => item.id !== itemId);
    saveCart();

    // Update UI
    updateCartPopup();

    // If on cart page, reload to reflect changes
    if (window.location.pathname === '/cart') {
        location.reload();
    }
}

// Toggle cart popup visibility
function toggleCartPopup() {
    console.log('Toggle cart popup called');
    const cartPopup = document.getElementById('cart-popup');
    if (cartPopup) {
        console.log('Cart popup found, toggling show class');
        cartPopup.classList.toggle('show');
        console.log('Cart popup classes after toggle:', cartPopup.className);
    } else {
        console.error('Cart popup element not found');
    }
}

// User management modal functions
function showAddUserModal() {
    console.log('showAddUserModal called');
    document.getElementById('add-user-modal').classList.remove('hidden');
}

function closeAddUserModal() {
    console.log('closeAddUserModal called');
    document.getElementById('add-user-modal').classList.add('hidden');
    document.getElementById('add-user-form').reset();
}

function showEditUserModal(userId) {
    console.log('Fetching user data for ID:', userId);
    // Fetch user data and populate form
    fetch(`/api/users/${userId}`, {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
    .then(user => {
        document.getElementById('edit-user-id').value = user.id;
        document.getElementById('edit-name').value = user.name;
        document.getElementById('edit-email').value = user.email;
        document.getElementById('edit-phone').value = user.phone || '';
        document.getElementById('edit-role').value = user.role;
        document.getElementById('edit-user-modal').classList.remove('hidden');
    })
    .catch(error => {
        console.error('Error fetching user:', error);
        let errorMessage = 'Failed to load user data';
        if (error.message) errorMessage = error.message;
        showNotification(errorMessage, 'error');
    });
}

function closeEditUserModal() {
    document.getElementById('edit-user-modal').classList.add('hidden');
}

function showDeleteUserModal(userId, userName) {
    document.getElementById('delete-user-id').value = userId;
    document.getElementById('delete-user-name').textContent = userName;
    document.getElementById('delete-user-modal').classList.remove('hidden');
}

function closeDeleteUserModal() {
    document.getElementById('delete-user-modal').classList.add('hidden');
}

function addUser() {
    const form = document.getElementById('add-user-form');

    // Validate form
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    // Check if current user has top_user role
    const currentUserRole = document.body.getAttribute('data-user-role');
    if (currentUserRole !== 'top_user') {
        showNotification('Only top users can add new users', 'error');
        return;
    }

    // Get form values directly
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    const role = document.getElementById('role').value;
    const password = document.getElementById('password').value;

    // Create FormData object
    const formData = new FormData();
    formData.append('name', name);
    formData.append('email', email);
    formData.append('phone', phone);
    formData.append('role', role);
    formData.append('password', password);

    // Show loading state
    const submitBtn = document.querySelector('#add-user-modal .submit-btn');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
    submitBtn.disabled = true;

    fetch('/api/users/create', {
        method: 'POST',
        body: formData,
        credentials: 'include'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
    .then(data => {
        closeAddUserModal();
        // Show success message
        showNotification(`User ${data.user.name} added successfully!`, 'success');

        // Reload page to show new user
        setTimeout(() => {
            window.location.reload();
        }, 1500);
    })
    .catch(error => {
        console.error('Error adding user:', error);

        // Reset button state
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;

        // Show error message
        let errorMessage = 'Unknown error occurred';
        if (error.message) {
            errorMessage = error.message;
        } else if (error.detail) {
            errorMessage = error.detail;
        }

        showNotification(`Failed to add user: ${errorMessage}`, 'error');
    });
}

function updateUser() {
    const form = document.getElementById('edit-user-form');

    // Validate form
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    // Check if current user has top_user role
    const currentUserRole = document.body.getAttribute('data-user-role');
    if (currentUserRole !== 'top_user') {
        showNotification('Only top users can update user information', 'error');
        return;
    }

    const userId = document.getElementById('edit-user-id').value;
    const name = document.getElementById('edit-name').value;
    const email = document.getElementById('edit-email').value;
    const phone = document.getElementById('edit-phone').value;
    const role = document.getElementById('edit-role').value;

    // Create FormData object
    const formData = new FormData();
    formData.append('name', name);
    formData.append('email', email);
    formData.append('phone', phone);
    formData.append('role', role);

    // Show loading state
    const submitBtn = document.querySelector('#edit-user-modal .submit-btn');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
    submitBtn.disabled = true;

    fetch(`/api/users/update/${userId}`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
    .then(data => {
        closeEditUserModal();
        showNotification(`User ${data.user.name} updated successfully!`, 'success');

        // Reload page to show updated user
        setTimeout(() => {
            window.location.reload();
        }, 1500);
    })
    .catch(error => {
        console.error('Error updating user:', error);

        // Reset button state
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;

        // Show error message
        let errorMessage = 'Unknown error occurred';
        if (error.message) {
            errorMessage = error.message;
        } else if (error.detail) {
            errorMessage = error.detail;
        }

        showNotification(`Failed to update user: ${errorMessage}`, 'error');
    });
}

function deleteUser() {
    // Check if current user has top_user role
    const currentUserRole = document.body.getAttribute('data-user-role');
    if (currentUserRole !== 'top_user') {
        showNotification('Only top users can delete users', 'error');
        closeDeleteUserModal();
        return;
    }

    const userId = document.getElementById('delete-user-id').value;
    const userName = document.getElementById('delete-user-name').textContent;

    // Show loading state
    const deleteBtn = document.querySelector('#delete-user-modal .delete-confirm-btn');
    const originalText = deleteBtn.innerHTML;
    deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
    deleteBtn.disabled = true;

    fetch(`/api/users/delete/${userId}`, {
        method: 'POST',
        credentials: 'include'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
    .then(data => {
        closeDeleteUserModal();
        showNotification(`User ${userName} deleted successfully!`, 'success');

        // Reload page to update user list
        setTimeout(() => {
            window.location.reload();
        }, 1500);
    })
    .catch(error => {
        console.error('Error deleting user:', error);

        // Reset button state
        deleteBtn.innerHTML = originalText;
        deleteBtn.disabled = false;

        // Show error message
        let errorMessage = 'Unknown error occurred';
        if (error.message) {
            errorMessage = error.message;
        } else if (error.detail) {
            errorMessage = error.detail;
        }

        showNotification(`Failed to delete user: ${errorMessage}`, 'error');
    });
}

// Search functionality
function searchUsers() {
    const input = document.getElementById('userSearchInput');
    const filter = input.value.toUpperCase();
    const table = document.getElementById('usersTable');
    const rows = table.getElementsByTagName('tr');

    for (let i = 1; i < rows.length; i++) {
        let found = false;
        const cells = rows[i].getElementsByTagName('td');

        for (let j = 0; j < cells.length - 1; j++) {
            const cell = cells[j];
            if (cell) {
                const textValue = cell.textContent || cell.innerText;
                if (textValue.toUpperCase().indexOf(filter) > -1) {
                    found = true;
                    break;
                }
            }
        }

        rows[i].style.display = found ? '' : 'none';
    }
}

// Helper function to show notifications
function showNotification(message, type = 'success') {
    // Create notification element if it doesn't exist
    if (!document.querySelector('.notification-container')) {
        const container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
    }

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;

    const icon = document.createElement('i');
    icon.className = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';

    const text = document.createElement('span');
    text.textContent = message;

    notification.appendChild(icon);
    notification.appendChild(text);

    document.querySelector('.notification-container').appendChild(notification);

    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 3000);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Hide all modals on page load
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.style.display = 'none';
        if (modal.id === 'delete-modal') {
            modal.classList.add('hidden');
        }
    });

    // Set up cart popup toggle button
    console.log('Setting up cart popup toggle button');
    const cartToggleBtn = document.getElementById('cart-toggle-btn');
    if (cartToggleBtn) {
        console.log('Cart toggle button found, adding click event listener');
        cartToggleBtn.addEventListener('click', function(event) {
            console.log('Cart toggle button clicked');
            event.stopPropagation(); // Prevent event from bubbling up
            toggleCartPopup();
        });
    } else {
        console.error('Cart toggle button not found');
    }

    // Set up cart popup close button
    console.log('Setting up cart popup close button');
    const cartPopupClose = document.getElementById('cart-popup-close');
    if (cartPopupClose) {
        console.log('Cart popup close button found, adding click event listener');
        cartPopupClose.addEventListener('click', function(event) {
            console.log('Cart popup close button clicked');
            event.stopPropagation(); // Prevent event from bubbling up
            const cartPopup = document.getElementById('cart-popup');
            if (cartPopup) {
                cartPopup.classList.remove('show');
            }
        });
    } else {
        console.error('Cart popup close button not found');
    }

    // Close cart popup when clicking outside
    document.addEventListener('click', function(event) {
        const cartPopup = document.getElementById('cart-popup');
        const cartToggleBtn = document.getElementById('cart-toggle-btn');

        if (cartPopup && cartPopup.classList.contains('show') &&
            !cartPopup.contains(event.target) &&
            cartToggleBtn && !cartToggleBtn.contains(event.target)) {
            cartPopup.classList.remove('show');
        }
    });

    // Update cart count
    updateCartCount();

    // Add event listeners to "Add to Cart" buttons
    const addToCartButtons = document.querySelectorAll('.add-to-cart-btn');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', function() {
            const itemId = this.getAttribute('data-id');
            const itemName = this.getAttribute('data-name');
            const price = this.getAttribute('data-price');
            const gstRate = this.getAttribute('data-gst');
            const quantity = this.getAttribute('data-quantity');
            const itemType = this.getAttribute('data-type') || 'product';

            addToCart(itemId, itemName, price, gstRate, parseInt(quantity, 10), itemType);
        });
    });

    // Service buttons now use inline onclick attributes in the HTML
    console.log('Service buttons now use inline onclick attributes');

    // Add direct click handlers to product buttons (non-service buttons)
    document.querySelectorAll('.view-details-btn:not(.service-details-btn)').forEach(button => {
        console.log('Adding direct click handler to product button:', button);
        button.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            const itemId = this.getAttribute('data-id');
            console.log('Product button clicked directly, id:', itemId);
            openProductModal(itemId);
            return false;
        };
    });

    // Add event listener to close modal button
    const closeModalBtn = document.querySelector('.close-modal');
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeModal);
    }

    // Add event listener to modal background for closing
    const modal = document.getElementById('product-modal');
    if (modal) {
        modal.addEventListener('click', function(event) {
            if (event.target === modal) {
                closeModal();
            }
        });
    }

    // Add event listener to delete modal background for closing
    const deleteModal = document.getElementById('delete-modal');
    if (deleteModal) {
        deleteModal.addEventListener('click', function(event) {
            if (event.target === deleteModal) {
                closeDeleteModal();
            }
        });
    }

    // Add event listener to search button
    const searchBtn = document.getElementById('search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', searchProducts);
    }

    // Add event listener to search input for enter key
    const searchInput = document.getElementById('product-search');
    if (searchInput) {
        searchInput.addEventListener('keyup', function(event) {
            if (event.key === 'Enter') {
                searchProducts();
            }
        });
    }

    // Add event listeners to save quantity buttons
    const saveQuantityButtons = document.querySelectorAll('.save-quantity-btn');
    saveQuantityButtons.forEach(button => {
        button.addEventListener('click', function() {
            const itemCode = this.getAttribute('data-id');
            const input = this.previousElementSibling;
            const newQuantity = parseInt(input.value, 10);

            if (isNaN(newQuantity) || newQuantity < 0) {
                showNotification('Please enter a valid quantity');
                return;
            }

            saveQuantity(itemCode, newQuantity);
        });
    });

    // Render cart items if on cart page
    if (window.location.pathname === '/cart') {
        renderCartItems();
        updateCartTotals();
    }
});
