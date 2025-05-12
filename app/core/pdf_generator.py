from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import os
import traceback
from datetime import datetime



def generate_pdf_invoice(invoice):
    """Generate a PDF invoice that matches the web view layout"""
    # Check if invoice is a dictionary or an object
    is_dict = isinstance(invoice, dict)

    try:
        # Get invoice details
        if is_dict:
            invoice_number = invoice.get('invoice_number', '')
            pdf_path = invoice.get('pdf_path', f"invoices/{invoice_number}.pdf")

            # Get date
            date = invoice.get('date')
            if hasattr(date, 'strftime'):
                date_str = date.strftime('%d-%m-%Y')
            else:
                date_str = str(date)

            # Get payment details
            payment_method = invoice.get('payment_method', 'Cash')
            payment_status = invoice.get('payment_status', 'Unpaid')
            amount_paid = invoice.get('amount_paid', 0)

            # Get items
            items = invoice.get('invoice_items', invoice.get('items', []))
        else:
            invoice_number = getattr(invoice, 'invoice_number', '')
            pdf_path = getattr(invoice, 'pdf_path', f"invoices/{invoice_number}.pdf")

            # Get date
            date = getattr(invoice, 'date', datetime.now())
            if hasattr(date, 'strftime'):
                date_str = date.strftime('%d-%m-%Y')
            else:
                date_str = str(date)

            # Get payment details
            payment_method = getattr(invoice, 'payment_method', 'Cash')
            payment_status = getattr(invoice, 'payment_status', 'Unpaid')
            amount_paid = getattr(invoice, 'amount_paid', 0)

            # Get items
            if hasattr(invoice, 'invoice_items'):
                items = invoice.invoice_items
            elif hasattr(invoice, 'items') and not callable(getattr(invoice, 'items')):
                items = invoice.items
            else:
                items = []

        # Create invoices directory if it doesn't exist
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

        # Create PDF with A4 size
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4

        # Set title
        c.setTitle(f"Invoice {invoice_number}")

        # Define colors
        header_color = colors.Color(0.5, 0.0, 0.5)  # Purple for headers
        light_gray = colors.Color(0.9, 0.9, 0.9)    # Light gray for backgrounds
        green_color = colors.Color(0.0, 0.5, 0.0)    # Green for "Fully Paid" status

        # Define pagination variables
        items_per_page = 20
        total_pages = (len(items) + items_per_page - 1) // items_per_page
        
        # Process each page
        for page_num in range(total_pages):
            if page_num > 0:
                c.showPage()  # Start a new page
                
            # Create a clean white background
            c.setFillColor(colors.white)
            c.rect(0, 0, width, height, fill=1, stroke=0)

            # Add logo in the top left
            logo_path = "static/images/logo.png"
            if os.path.exists(logo_path):
                c.drawImage(logo_path, 40, height - 80, width=80, height=60, mask='auto')

            # Add invoice details on the right
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(colors.black)
            c.drawString(width - 200, height - 40, "Invoice Number:")
            c.drawString(width - 200, height - 60, "Date:")
            c.drawString(width - 200, height - 80, "GST Number:")

            # Add invoice details values
            c.setFont("Helvetica", 10)
            c.setFillColor(colors.black)
            c.drawString(width - 100, height - 40, invoice_number)
            c.drawString(width - 100, height - 60, date_str)
            c.drawString(width - 100, height - 80, "37FUWPS9742A1ZT")

            # Add company name
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(colors.black)
            c.drawString(40, height - 90, "Sunmax Renewables")

            # Add horizontal line
            c.setStrokeColor(colors.black)
            c.setLineWidth(1)
            c.line(40, height - 100, width - 40, height - 100)

            # Get customer details
            if is_dict:
                customer_name = invoice.get('customer_name', '')
                customer_address = invoice.get('customer_address', '')
                customer_phone = invoice.get('customer_phone', '')
                customer_email = invoice.get('customer_email', '')
                customer_gst = invoice.get('customer_gst', '')
            else:
                customer_name = getattr(invoice, 'customer_name', '')
                customer_address = getattr(invoice, 'customer_address', '')
                customer_phone = getattr(invoice, 'customer_phone', '')
                customer_email = getattr(invoice, 'customer_email', '')
                customer_gst = getattr(invoice, 'customer_gst', '')

            # Set initial y position
            y_position = height - 120

            # Only add company and customer details on first page
            if page_num == 0:
                # Left box for company details
                c.setFillColor(light_gray)
                c.rect(40, y_position - 90, (width - 80) / 2 - 5, 90, fill=1, stroke=0)
                c.setStrokeColor(colors.black)
                c.rect(40, y_position - 90, (width - 80) / 2 - 5, 90, fill=0, stroke=1)

                # Right box for customer details
                c.setFillColor(light_gray)
                c.rect(40 + (width - 80) / 2 + 5, y_position - 90, (width - 80) / 2 - 5, 90, fill=1, stroke=0)
                c.setStrokeColor(colors.black)
                c.rect(40 + (width - 80) / 2 + 5, y_position - 90, (width - 80) / 2 - 5, 90, fill=0, stroke=1)

                # Add company details
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(50, y_position - 20, "Company Details:")
                c.setFont("Helvetica", 9)
                c.drawString(50, y_position - 35, "Sunmax Renewables")
                c.drawString(50, y_position - 50, "Ground floor of Sneha Nagar Sachivalayam")
                c.drawString(50, y_position - 65, "B.V.Nagar, NGO Colony, Nellore")
                c.drawString(50, y_position - 75, "Andhra Pradesh 524004")
                c.drawString(50, y_position - 85, "Phone: 9381488225, 7013023946")

                # Add customer details
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(40 + (width - 80) / 2 + 15, y_position - 20, "Customer Details:")
                c.setFont("Helvetica", 9)
                c.drawString(40 + (width - 80) / 2 + 15, y_position - 35, f"Name: {customer_name}")
                c.drawString(40 + (width - 80) / 2 + 15, y_position - 50, f"Address: {customer_address}")
                c.drawString(40 + (width - 80) / 2 + 15, y_position - 65, f"Phone: {customer_phone}")
                
                if customer_email:
                    c.drawString(40 + (width - 80) / 2 + 15, y_position - 75, f"Email: {customer_email}")
                
                if customer_gst:
                    c.drawString(40 + (width - 80) / 2 + 15, y_position - 85, f"GST: {customer_gst}")
                
                # Adjust y position after customer details
                y_position = y_position - 110
            else:
                # For continuation pages
                c.setFont("Helvetica-Bold", 12)
                c.drawString(40, y_position - 20, f"Invoice {invoice_number} - Continued")
                y_position = y_position - 40

            # Add items table header
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor(colors.black)
            c.drawString(40, y_position, "Invoice Items")
            
            # Add table header with background
            y_position -= 20
            c.setFillColor(header_color)
            c.rect(40, y_position - 20, width - 80, 20, fill=1, stroke=0)
            
            # Add column headers
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 9)
            
            # Calculate column positions
            col1 = 45           # Item
            col2 = col1 + 180   # HSN
            col3 = col2 + 60    # Qty
            col4 = col3 + 50    # Price
            col5 = col4 + 60    # Discount
            col6 = col5 + 60    # GST
            col7 = col6 + 60    # Total
            
            c.drawString(col1, y_position - 15, "Item")
            c.drawString(col2, y_position - 15, "HSN")
            c.drawString(col3, y_position - 15, "Qty")
            c.drawString(col4, y_position - 15, "Price")
            c.drawString(col5, y_position - 15, "Discount")
            c.drawString(col6, y_position - 15, "GST")
            c.drawString(col7, y_position - 15, "Total")
            
            # Get items for this page
            start_idx = page_num * items_per_page
            end_idx = min(start_idx + items_per_page, len(items))
            page_items = items[start_idx:end_idx]
            
            # Add items
            y_position -= 25
            row_count = 0
            
            for item in page_items:
                # Get item details
                if isinstance(item, dict):
                    item_name = item.get('item_name', '')
                    hsn_code = item.get('hsn_code', '')
                    quantity = item.get('quantity', 0)
                    price = item.get('price', 0)
                    discount = item.get('discount', 0)
                    gst_rate = item.get('gst_rate', 0)
                    gst_amount = item.get('gst_amount', 0)
                    total = item.get('total', 0)
                else:
                    item_name = getattr(item, 'item_name', '')
                    hsn_code = getattr(item, 'hsn_code', '')
                    quantity = getattr(item, 'quantity', 0)
                    price = getattr(item, 'price', 0)
                    discount = getattr(item, 'discount', 0)
                    gst_rate = getattr(item, 'gst_rate', 0)
                    gst_amount = getattr(item, 'gst_amount', 0)
                    total = getattr(item, 'total', 0)
                
                # Draw alternating row background
                if row_count % 2 == 0:
                    c.setFillColor(colors.white)
                else:
                    c.setFillColor(light_gray)
                
                c.rect(40, y_position - 20, width - 80, 20, fill=1, stroke=0)
                
                # Add item details
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 8)
                
                # Truncate item name if too long
                if len(item_name) > 30:
                    item_name = item_name[:27] + "..."
                
                c.drawString(col1, y_position - 15, item_name)
                c.drawString(col2, y_position - 15, str(hsn_code))
                c.drawString(col3, y_position - 15, str(quantity))
                c.drawString(col4, y_position - 15, f"Rs.{price:.2f}")
                c.drawString(col5, y_position - 15, f"{discount}%")
                c.drawString(col6, y_position - 15, f"{gst_rate}% (Rs.{gst_amount:.2f})")
                c.drawString(col7, y_position - 15, f"Rs.{total:.2f}")
                
                # Move to next row
                y_position -= 20
                row_count += 1
            
            # Add summary section only on the last page
            if page_num == total_pages - 1:
                # Calculate totals
                if is_dict:
                    subtotal = invoice.get('subtotal', 0)
                    total_discount = invoice.get('total_discount', 0)
                    discounted_subtotal = invoice.get('discounted_subtotal', 0)
                    total_gst = invoice.get('total_gst', 0)
                    total_amount = invoice.get('total_amount', invoice.get('total', 0))
                    amount_paid = invoice.get('amount_paid', 0)
                    balance_due = total_amount - amount_paid
                
                else:
                    subtotal = getattr(invoice, 'subtotal', 0)
                    total_discount = getattr(invoice, 'total_discount', 0)
                    discounted_subtotal = getattr(invoice, 'discounted_subtotal', 0)
                    total_gst = getattr(invoice, 'total_gst', 0)
                    total_amount = getattr(invoice, 'total_amount', getattr(invoice, 'total', 0))
                    amount_paid = getattr(invoice, 'amount_paid', 0)
                    balance_due = total_amount - amount_paid
                
                # Add summary box
                summary_y = y_position - 20
                c.setFillColor(light_gray)
                c.rect(width - 250, summary_y - 120, 210, 120, fill=1, stroke=0)
                c.setStrokeColor(colors.black)
                c.rect(width - 250, summary_y - 120, 210, 120, fill=0, stroke=1)
                
                # Add summary details
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(width - 240, summary_y - 20, "Subtotal:")
                c.drawString(width - 240, summary_y - 40, "Discount:")
                c.drawString(width - 240, summary_y - 60, "GST Amount:")
                c.drawString(width - 240, summary_y - 80, "Total Amount:")
                c.drawString(width - 240, summary_y - 100, "Amount Paid:")
                c.drawString(width - 240, summary_y - 120, "Balance Due:")
                
                # Add values
                c.setFont("Helvetica", 10)
                c.drawString(width - 150, summary_y - 20, f"Rs.{subtotal:.2f}")
                c.drawString(width - 150, summary_y - 40, f"Rs.{total_discount:.2f}")
                c.drawString(width - 150, summary_y - 60, f"Rs.{total_gst:.2f}")
                c.setFont("Helvetica-Bold", 10)
                c.drawString(width - 150, summary_y - 80, f"Rs.{total_amount:.2f}")
                c.drawString(width - 150, summary_y - 100, f"Rs.{amount_paid:.2f}")
                
                # Add balance due color
                if balance_due <= 0:
                    c.setFillColor(green_color)
                else:
                    c.setFillColor(colors.red)
                    c.drawString(width - 150, summary_y - 120, f"Rs.{balance_due:.2f}")
                    c.setFillColor(colors.black)
                
                # Add payment status
                payment_y = summary_y - 150
                c.setFont("Helvetica-Bold", 12)
                
                if payment_status == "Fully Paid":
                    c.setFillColor(green_color)
                    status_text = "PAID"
                elif payment_status == "Partially Paid":
                    c.setFillColor(colors.orange)
                    status_text = f"PARTIALLY (Rs.{amount_paid:.2f})"
                else:
                    c.setFillColor(colors.red)
                    status_text = "UNPAID"
                
                c.drawString(width - 240, payment_y, f"Payment Status: {status_text}")
                c.drawString(width - 240, payment_y - 20, f"Payment Method: {payment_method}")
            
            # Add page number
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.black)
            c.drawString(width - 100, 30, f"Page {page_num + 1} of {total_pages}")
            
            # Add footer
            if page_num == total_pages - 1:
                c.setFont("Helvetica", 8)
                c.drawString(40, 30, "This is a computer-generated invoice and does not require a signature.")
            else:
                c.drawString(40, 30, "Continued on next page...")
        
        # Save the PDF
        c.save()
        return pdf_path
    except Exception as e:
        print(f"Error generating PDF invoice: {e}")
        traceback.print_exc()
        return None
    
    
    
def generate_pdf_quotation(quotation):
    """Generate a PDF quotation that matches the web view layout"""
    # Check if quotation is a dictionary or an object
    is_dict = isinstance(quotation, dict)

    try:
        # Get quotation details
        if is_dict:
            quote_number = quotation.get('quote_number', '')
            pdf_path = quotation.get('pdf_path', f"quotations/{quote_number}.pdf")

            # Get date
            date = quotation.get('date')
            if hasattr(date, 'strftime'):
                date_str = date.strftime('%d-%m-%Y')
            else:
                date_str = str(date)

            # Get items
            items = quotation.get('items', [])

            # Get asked_about
            asked_about = quotation.get('asked_about', '')
        else:
            quote_number = getattr(quotation, 'quote_number', '')
            pdf_path = getattr(quotation, 'pdf_path', f"quotations/{quote_number}.pdf")

            # Get date
            date = getattr(quotation, 'date', datetime.now())
            if hasattr(date, 'strftime'):
                date_str = date.strftime('%d-%m-%Y')
            else:
                date_str = str(date)

            # Get items
            if hasattr(quotation, 'items') and not callable(getattr(quotation, 'items')):
                items = quotation.items
            else:
                items = []

            # Get asked_about
            asked_about = getattr(quotation, 'asked_about', '')

        # Create quotations directory if it doesn't exist
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

        # Create PDF with A4 size
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4

        # Set title
        c.setTitle(f"Quotation {quote_number}")

        # Define colors
        header_color = colors.Color(0.5, 0.0, 0.5)  # Purple for headers
        light_gray = colors.Color(0.9, 0.9, 0.9)    # Light gray for backgrounds

        # Define pagination variables
        items_per_page = 20
        total_pages = (len(items) + items_per_page - 1) // items_per_page
        
        # Process each page
        for page_num in range(total_pages):
            if page_num > 0:
                c.showPage()  # Start a new page
                
            # Create a clean white background
            c.setFillColor(colors.white)
            c.rect(0, 0, width, height, fill=1, stroke=0)

            # Add logo in the top left
            logo_path = "static/images/logo.png"
            if os.path.exists(logo_path):
                c.drawImage(logo_path, 40, height - 80, width=80, height=60, mask='auto')

            # Add quotation details on the right
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(colors.black)
            c.drawString(width - 200, height - 40, "Quotation Number:")
            c.drawString(width - 200, height - 60, "Date:")
            c.drawString(width - 200, height - 80, "GST Number:")

            # Add quotation details values
            c.setFont("Helvetica", 10)
            c.setFillColor(colors.black)
            c.drawString(width - 100, height - 40, quote_number)
            c.drawString(width - 100, height - 60, date_str)
            c.drawString(width - 100, height - 80, "37FUWPS9742A1ZT")

            # Add company name
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(colors.black)
            c.drawString(40, height - 90, "Sunmax Renewables")

            # Add horizontal line
            c.setStrokeColor(colors.black)
            c.setLineWidth(1)
            c.line(40, height - 100, width - 40, height - 100)

            # Get customer details
            if is_dict:
                customer_name = quotation.get('customer_name', '')
                customer_address = quotation.get('customer_address', '')
                customer_phone = quotation.get('customer_phone', '')
                customer_email = quotation.get('customer_email', '')
            else:
                customer_name = getattr(quotation, 'customer_name', '')
                customer_address = getattr(quotation, 'customer_address', '')
                customer_phone = getattr(quotation, 'customer_phone', '')
                customer_email = getattr(quotation, 'customer_email', '')

            # Set initial y position
            y_position = height - 120

            # Only add company and customer details on first page
            if page_num == 0:
                # Left box for company details
                c.setFillColor(light_gray)
                c.rect(40, y_position - 90, (width - 80) / 2 - 5, 90, fill=1, stroke=0)
                c.setStrokeColor(colors.black)
                c.rect(40, y_position - 90, (width - 80) / 2 - 5, 90, fill=0, stroke=1)

                # Right box for customer details
                c.setFillColor(light_gray)
                c.rect(40 + (width - 80) / 2 + 5, y_position - 90, (width - 80) / 2 - 5, 90, fill=1, stroke=0)
                c.setStrokeColor(colors.black)
                c.rect(40 + (width - 80) / 2 + 5, y_position - 90, (width - 80) / 2 - 5, 90, fill=0, stroke=1)

                # Add company details
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(50, y_position - 20, "Company Details:")
                c.setFont("Helvetica", 9)
                c.drawString(50, y_position - 35, "Sunmax Renewables")
                c.drawString(50, y_position - 50, "Ground floor of Sneha Nagar Sachivalayam")
                c.drawString(50, y_position - 65, "B.V.Nagar, NGO Colony, Nellore")
                c.drawString(50, y_position - 75, "Andhra Pradesh 524004")
                c.drawString(50, y_position - 85, "Phone: 9381488225, 7013023946")

                # Add customer details
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(40 + (width - 80) / 2 + 15, y_position - 20, "Customer Details:")
                c.setFont("Helvetica", 9)
                c.drawString(40 + (width - 80) / 2 + 15, y_position - 35, f"Name: {customer_name}")
                
                if customer_address:
                    c.drawString(40 + (width - 80) / 2 + 15, y_position - 50, f"Address: {customer_address}")
                
                if customer_phone:
                    c.drawString(40 + (width - 80) / 2 + 15, y_position - 65, f"Phone: {customer_phone}")
                
                if customer_email:
                    c.drawString(40 + (width - 80) / 2 + 15, y_position - 80, f"Email: {customer_email}")
                
                # Add asked about section if available
                if asked_about:
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(40, y_position - 110, "Enquiry About:")
                    c.setFont("Helvetica", 9)
                    
                    # Split long text into multiple lines
                    max_width = width - 80
                    words = asked_about.split()
                    lines = []
                    current_line = []
                    
                    for word in words:
                        test_line = ' '.join(current_line + [word])
                        if c.stringWidth(test_line, "Helvetica", 9) < max_width:
                            current_line.append(word)
                        else:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                    
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    for i, line in enumerate(lines[:3]):  # Limit to 3 lines
                        c.drawString(40, y_position - 125 - (i * 15), line)
                    
                    y_position = y_position - 125 - (min(len(lines), 3) * 15) - 10
                else:
                    y_position = y_position - 110
            else:
                # For continuation pages
                c.setFont("Helvetica-Bold", 12)
                c.drawString(40, y_position - 20, f"Quotation {quote_number} - Continued")
                y_position = y_position - 40

            # Add items table header
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor(colors.black)
            c.drawString(40, y_position, "Quotation Items")
            
            # Add table header with background
            y_position -= 20
            c.setFillColor(header_color)
            c.rect(40, y_position - 20, width - 80, 20, fill=1, stroke=0)
            
            # Add column headers
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 9)
            
            # Calculate column positions
            col1 = 45           # Item
            col2 = col1 + 200   # Quantity
            col3 = col2 + 60    # Price
            col4 = col3 + 60    # GST
            col5 = col4 + 60    # Total
            
            c.drawString(col1, y_position - 15, "Item")
            c.drawString(col2, y_position - 15, "Quantity")
            c.drawString(col3, y_position - 15, "Price")
            c.drawString(col4, y_position - 15, "GST")
            c.drawString(col5, y_position - 15, "Total")
            
            # Get items for this page
            start_idx = page_num * items_per_page
            end_idx = min(start_idx + items_per_page, len(items))
            page_items = items[start_idx:end_idx]
            
            # Add items
            y_position -= 25
            row_count = 0
            
            for item in page_items:
                # Get item details
                if isinstance(item, dict):
                    item_name = item.get('item_name', '')
                    quantity = item.get('quantity', 0)
                    price = item.get('price', 0)
                    gst_rate = item.get('gst_rate', 0)
                    gst_amount = item.get('gst_amount', 0)
                    total = item.get('total', 0)
                else:
                    item_name = getattr(item, 'item_name', '')
                    quantity = getattr(item, 'quantity', 0)
                    price = getattr(item, 'price', 0)
                    gst_rate = getattr(item, 'gst_rate', 0)
                    gst_amount = getattr(item, 'gst_amount', 0)
                    total = getattr(item, 'total', 0)
                
                # Draw alternating row background
                if row_count % 2 == 0:
                    c.setFillColor(colors.white)
                else:
                    c.setFillColor(light_gray)
                
                c.rect(40, y_position - 20, width - 80, 20, fill=1, stroke=0)
                
                # Add item details
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 8)
                
                # Truncate item name if too long
                if len(item_name) > 35:
                    item_name = item_name[:32] + "..."
                
                c.drawString(col1, y_position - 15, item_name)
                c.drawString(col2, y_position - 15, str(quantity))
                c.drawString(col3, y_position - 15, f"Rs.{price:.2f}")
                c.drawString(col4, y_position - 15, f"{gst_rate}% (Rs.{gst_amount:.2f})")
                c.drawString(col5, y_position - 15, f"Rs.{total:.2f}")
                
                # Move to next row
                y_position -= 20
                row_count += 1
            
            # Add summary section only on the last page
            if page_num == total_pages - 1:
                # Calculate totals
                if is_dict:
                    subtotal = quotation.get('subtotal', 0)
                    total_gst = quotation.get('total_gst', 0)
                    total_amount = quotation.get('total_amount', 0)
                else:
                    subtotal = getattr(quotation, 'subtotal', 0)
                    total_gst = getattr(quotation, 'total_gst', 0)
                    total_amount = getattr(quotation, 'total_amount', 0)
                
                # Add summary box
                summary_y = y_position - 20
                c.setFillColor(light_gray)
                c.rect(width - 250, summary_y - 80, 210, 80, fill=1, stroke=0)
                c.setStrokeColor(colors.black)
                c.rect(width - 250, summary_y - 80, 210, 80, fill=0, stroke=1)
                
                # Add summary details
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(width - 240, summary_y - 20, "Subtotal:")
                c.drawString(width - 240, summary_y - 40, "GST Amount:")
                c.drawString(width - 240, summary_y - 60, "Total Amount:")
                
                # Add values
                c.setFont("Helvetica", 10)
                c.drawString(width - 150, summary_y - 20, f"Rs.{subtotal:.2f}")
                c.drawString(width - 150, summary_y - 40, f"Rs.{total_gst:.2f}")
                c.setFont("Helvetica-Bold", 10)
                c.drawString(width - 150, summary_y - 60, f"Rs.{total_amount:.2f}")
                
                # Add note
                note_y = summary_y - 100
                c.setFont("Helvetica-Oblique", 9)
                c.drawString(40, note_y, "Note: This is just a quotation, not an invoice. Prices may vary at the time of purchase.")
                
                # Add validity
                c.setFont("Helvetica", 9)
                c.drawString(40, note_y - 20, "Quotation Validity: 15 days from the date of issue")
            
            # Add page number
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.black)
            c.drawString(width - 100, 30, f"Page {page_num + 1} of {total_pages}")
            
            # Add footer
            if page_num == total_pages - 1:
                c.setFont("Helvetica", 8)
                c.drawString(40, 30, "This is a computer-generated quotation and does not require a signature.")
            else:
                c.drawString(40, 30, "Continued on next page...")
        
        # Save the PDF
        c.save()
        return pdf_path
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error generating quotation PDF: {e}")
        print(f"Error details: {error_details}")

        # Create a simple error PDF instead
        try:
            # Create a very basic PDF with error information
            c = canvas.Canvas(pdf_path, pagesize=A4)
            width, height = A4

            # Set title
            c.setTitle(f"Quotation {quote_number} - Error")

            # Add error information
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, height - 100, "Error Generating Quotation PDF")

            c.setFont("Helvetica", 12)
            c.drawString(50, height - 150, f"Quotation Number: {quote_number}")
            c.drawString(50, height - 180, f"Error: {str(e)}")

            # Save the PDF
            c.save()
            print(f"Created error PDF at {pdf_path}")
            return pdf_path
        except Exception as inner_e:
            print(f"Failed to create error PDF: {inner_e}")
            return None