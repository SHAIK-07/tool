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

        # Add company and customer details boxes
        y_position = height - 120

        # Left box for company details - increased height to 90
        c.setFillColor(light_gray)
        c.rect(40, y_position - 90, (width - 80) / 2 - 5, 90, fill=1, stroke=0)
        c.setStrokeColor(colors.black)
        c.rect(40, y_position - 100, (width - 80) / 2 - 5, 90, fill=0, stroke=1)

        # Right box for customer details - increased height to 90
        c.setFillColor(light_gray)
        c.rect(40 + (width - 80) / 2 + 5, y_position - 100, (width - 80) / 2 - 5, 90, fill=1, stroke=0)
        c.setStrokeColor(colors.black)
        c.rect(40 + (width - 80) / 2 + 5, y_position - 100, (width - 80) / 2 - 5, 90, fill=0, stroke=1)

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

        # Adjust positions to prevent overlapping
        customer_detail_y = y_position - 65
        if customer_gst:
            c.drawString(40 + (width - 80) / 2 + 15, customer_detail_y, f"GST Number: {customer_gst}")
            customer_detail_y -= 15

        if customer_phone:
            c.drawString(40 + (width - 80) / 2 + 15, customer_detail_y, f"Phone: {customer_phone}")
            customer_detail_y -= 15

        if customer_email:
            c.drawString(40 + (width - 80) / 2 + 15, customer_detail_y, f"Email: {customer_email}")

        # Add "Invoice Items" header - adjusted for increased box height
        y_position = y_position - 110
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.black)
        c.drawString(40, y_position, "Invoice Items")

        # Add items table header with purple background
        y_position -= 20  # Adjusted for the new layout
        c.setFillColor(header_color)
        c.rect(40, y_position - 20, width - 80, 20, fill=1, stroke=0)
        c.setStrokeColor(colors.black)
        c.rect(40, y_position - 20, width - 80, 20, fill=0, stroke=1)

        # Define column widths - simplified for the requested columns
        table_width = width - 80
        col_widths = [
            table_width * 0.15,  # Item
            table_width * 0.12,  # HSN Code
            table_width * 0.08,  # Quantity
            table_width * 0.12,  # Subtotal
            table_width * 0.12,  # Discount
            table_width * 0.15,  # Taxable Amount
            table_width * 0.12,  # GST Rate
            table_width * 0.14   # Total
        ]

        # Calculate column positions
        col_positions = [40]
        for width_val in col_widths:
            col_positions.append(col_positions[-1] + width_val)

        # Add column headers
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)

        headers = ["Item", "HSN Code", "Quantity", "Subtotal", "Discount",
                  "Taxable Amount", "GST Rate", "Total"]

        for i, header in enumerate(headers):
            c.drawString(col_positions[i] + 5, y_position - 15, header)

        # Add items to the invoice
        y_position -= 25
        row_count = 0

        # Calculate totals
        subtotal = 0
        total_discount = 0
        total_taxable = 0
        total_tax = 0
        total_amount = 0

        for item in items:
            # Get item details
            if isinstance(item, dict):
                item_name = item.get('item_name', '')
                hsn_code = item.get('hsn_code', '')
                quantity = item.get('quantity', 0)
                price = item.get('price', 0)
                item_subtotal = price * quantity

                # Get discount - check multiple possible fields
                discount = item.get('discount', 0)
                if discount == 0:
                    discount_percent = item.get('discount_percent', 0)
                    if discount_percent > 0:
                        discount = item_subtotal * (discount_percent / 100)
                    else:
                        discount_amount = item.get('discount_amount', 0)
                        if discount_amount > 0:
                            discount = discount_amount

                taxable_amount = item_subtotal - discount
                gst_rate = item.get('gst_rate', 0)
                gst_amount = taxable_amount * (gst_rate / 100)
                total = taxable_amount + gst_amount
            else:
                # If item is an ORM object
                item_name = getattr(item, 'item_name', '')
                hsn_code = getattr(item, 'hsn_code', '')
                quantity = getattr(item, 'quantity', 0)
                price = getattr(item, 'price', 0)
                item_subtotal = price * quantity

                # Get discount - check multiple possible fields
                discount = getattr(item, 'discount', 0)
                if discount == 0:
                    discount_percent = getattr(item, 'discount_percent', 0)
                    if discount_percent > 0:
                        discount = item_subtotal * (discount_percent / 100)
                    else:
                        discount_amount = getattr(item, 'discount_amount', 0)
                        if discount_amount > 0:
                            discount = discount_amount

                taxable_amount = item_subtotal - discount
                gst_rate = getattr(item, 'gst_rate', 0)
                gst_amount = taxable_amount * (gst_rate / 100)
                total = taxable_amount + gst_amount

            # Add item row with alternating background
            if row_count % 2 == 0:
                c.setFillColor(colors.white)
            else:
                c.setFillColor(light_gray)

            c.rect(40, y_position - 20, width - 80, 20, fill=1, stroke=0)
            c.setStrokeColor(colors.black)
            c.rect(40, y_position - 20, width - 80, 20, fill=0, stroke=1)

            # Add item details
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 8)

            # Draw item details with the new column structure
            values = [
                item_name,
                str(hsn_code),
                str(quantity),
                f"Rs.{item_subtotal:.1f}",
                f"Rs.{discount:.1f}",
                f"Rs.{taxable_amount:.1f}",
                f"{gst_rate:.1f}%",
                f"Rs.{total:.1f}"
            ]

            for i, value in enumerate(values):
                if i < 3:  # Left align text fields
                    c.drawString(col_positions[i] + 5, y_position - 15, value)
                else:  # Right align numeric fields
                    text_width = c.stringWidth(value, "Helvetica", 8)
                    c.drawString(col_positions[i+1] - text_width - 5, y_position - 15, value)

            # Update totals
            subtotal += item_subtotal
            total_discount += discount
            total_taxable += taxable_amount
            total_tax += gst_amount
            total_amount += total

            # Move to next row
            y_position -= 25
            row_count += 1

        # Add summary section
        y_position -= 20

        # Left box for financial calculations
        c.setFillColor(light_gray)
        c.rect(40, y_position - 120, (width - 80) / 2 - 5, 120, fill=1, stroke=0)
        c.setStrokeColor(colors.black)
        c.rect(40, y_position - 120, (width - 80) / 2 - 5, 120, fill=0, stroke=1)

        # Right box for payment information
        c.setFillColor(light_gray)
        c.rect(40 + (width - 80) / 2 + 5, y_position - 120, (width - 80) / 2 - 5, 120, fill=1, stroke=0)
        c.setStrokeColor(colors.black)
        c.rect(40 + (width - 80) / 2 + 5, y_position - 120, (width - 80) / 2 - 5, 120, fill=0, stroke=1)

        # Define column positions for summary
        left_col_x = 60
        right_col_x = 40 + (width - 80) / 2 + 25

        # Add left column headers (financial calculations)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left_col_x, y_position - 20, "Subtotal:")
        c.drawString(left_col_x, y_position - 40, "Discount:")
        c.drawString(left_col_x, y_position - 60, "Taxable Amount:")
        c.drawString(left_col_x, y_position - 80, "GST:")
        c.drawString(left_col_x, y_position - 100, "Total:")

        # Add left column values with right alignment
        c.setFont("Helvetica", 10)
        c.drawRightString(left_col_x + 150, y_position - 20, f"Rs.{subtotal:.1f}")
        c.drawRightString(left_col_x + 150, y_position - 40, f"Rs.{total_discount:.1f}")
        c.drawRightString(left_col_x + 150, y_position - 60, f"Rs.{total_taxable:.1f}")
        c.drawRightString(left_col_x + 150, y_position - 80, f"Rs.{total_tax:.1f}")
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(left_col_x + 150, y_position - 100, f"Rs.{total_amount:.1f}")

        # Add right column headers (payment information)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(right_col_x, y_position - 20, "Payment Method:")
        c.drawString(right_col_x, y_position - 40, "Payment Status:")
        c.drawString(right_col_x, y_position - 60, "Amount Paid:")
        c.drawString(right_col_x, y_position - 80, "Balance Due:")

        # Add right column values with right alignment
        c.setFont("Helvetica", 10)
        c.drawRightString(right_col_x + 150, y_position - 20, payment_method)

        # Set color for payment status
        if payment_status.lower() == "fully paid":
            c.setFillColor(green_color)
        elif payment_status.lower() == "partially paid":
            c.setFillColor(colors.orange)
        else:
            c.setFillColor(colors.red)

        c.drawRightString(right_col_x + 150, y_position - 40, payment_status)
        c.setFillColor(colors.black)
        c.drawRightString(right_col_x + 150, y_position - 60, f"Rs.{amount_paid:.1f}")

        # Set color for balance due
        balance_due = max(0, total_amount - amount_paid)  # Ensure balance is never negative

        # If fully paid, balance should be 0
        if payment_status.lower() == "fully paid":
            balance_due = 0
            c.setFillColor(green_color)
        elif balance_due > 0:
            c.setFillColor(colors.red)
        else:
            c.setFillColor(green_color)

        c.drawRightString(right_col_x + 150, y_position - 80, f"Rs.{balance_due:.1f}")
        c.setFillColor(colors.black)

        # Add footer
        footer_y = 50
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)

        # Center the footer text
        footer_text = "Thank you for your business!"
        text_width = c.stringWidth(footer_text, "Helvetica", 9)
        c.drawString((width - text_width) / 2, footer_y, footer_text)

        footer_text = "For any queries, please contact us at contactsunmax@gmail.com"
        text_width = c.stringWidth(footer_text, "Helvetica", 9)
        c.drawString((width - text_width) / 2, footer_y - 15, footer_text)

        footer_text = "This is a computer-generated invoice and does not require a signature."
        text_width = c.stringWidth(footer_text, "Helvetica", 9)
        c.drawString((width - text_width) / 2, footer_y - 30, footer_text)

        # Save the PDF
        c.save()
        return pdf_path
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error generating PDF: {e}")
        print(f"Error details: {error_details}")

        # Create a simple error PDF instead
        try:
            # Create a very basic PDF with error information
            c = canvas.Canvas(pdf_path, pagesize=A4)
            width, height = A4

            # Set title
            c.setTitle(f"Invoice {invoice_number} - Error")

            # Add error information
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, height - 100, "Error Generating Invoice PDF")

            c.setFont("Helvetica", 12)
            c.drawString(50, height - 150, f"Invoice Number: {invoice_number}")
            c.drawString(50, height - 180, f"Error: {str(e)}")

            # Save the PDF
            c.save()
            print(f"Created error PDF at {pdf_path}")
            return pdf_path
        except Exception as inner_e:
            print(f"Failed to create error PDF: {inner_e}")
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

        # Add company and customer details boxes
        y_position = height - 120

        # Left box for company details - increased height to 90
        c.setFillColor(light_gray)
        c.rect(40, y_position - 90, (width - 80) / 2 - 5, 90, fill=1, stroke=0)
        c.setStrokeColor(colors.black)
        c.rect(40, y_position - 100, (width - 80) / 2 - 5, 90, fill=0, stroke=1)

        # Right box for customer details - increased height to 90
        c.setFillColor(light_gray)
        c.rect(40 + (width - 80) / 2 + 5, y_position - 100, (width - 80) / 2 - 5, 90, fill=1, stroke=0)
        c.setStrokeColor(colors.black)
        c.rect(40 + (width - 80) / 2 + 5, y_position - 100, (width - 80) / 2 - 5, 90, fill=0, stroke=1)

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

        # Adjust positions to prevent overlapping
        customer_detail_y = y_position - 65
        if customer_phone:
            c.drawString(40 + (width - 80) / 2 + 15, customer_detail_y, f"Phone: {customer_phone}")
            customer_detail_y -= 15

        if customer_email:
            c.drawString(40 + (width - 80) / 2 + 15, customer_detail_y, f"Email: {customer_email}")

        # Add "Quotation Items" header - adjusted for increased box height
        y_position = y_position - 110
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.black)
        c.drawString(40, y_position, "Quotation Items")

        # Add items table header with purple background
        y_position -= 20  # Adjusted for the new layout
        c.setFillColor(header_color)
        c.rect(40, y_position - 20, width - 80, 20, fill=1, stroke=0)
        c.setStrokeColor(colors.black)
        c.rect(40, y_position - 20, width - 80, 20, fill=0, stroke=1)

        # Define column widths - simplified for the requested columns
        table_width = width - 80
        col_widths = [
            table_width * 0.20,  # Item
            table_width * 0.10,  # Quantity
            table_width * 0.15,  # Price
            table_width * 0.15,  # Subtotal
            table_width * 0.15,  # GST Rate
            table_width * 0.25   # Total
        ]

        # Calculate column positions
        col_positions = [40]
        for width_val in col_widths:
            col_positions.append(col_positions[-1] + width_val)

        # Add column headers
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)

        headers = ["Item", "Quantity", "Price", "Subtotal", "GST Rate", "Total"]

        for i, header in enumerate(headers):
            c.drawString(col_positions[i] + 5, y_position - 15, header)

        # Add items to the quotation
        y_position -= 25
        row_count = 0

        # Calculate totals
        subtotal = 0
        total_tax = 0
        total_amount = 0

        for item in items:
            # Get item details
            if isinstance(item, dict):
                item_name = item.get('item_name', '')
                quantity = item.get('quantity', 0)
                price = item.get('price', 0)
                item_subtotal = price * quantity
                gst_rate = item.get('gst_rate', 0)
                gst_amount = item.get('gst_amount', item_subtotal * (gst_rate / 100))
                total = item.get('total', item_subtotal + gst_amount)
            else:
                # If item is an ORM object
                item_name = getattr(item, 'item_name', '')
                quantity = getattr(item, 'quantity', 0)
                price = getattr(item, 'price', 0)
                item_subtotal = price * quantity
                gst_rate = getattr(item, 'gst_rate', 0)
                gst_amount = getattr(item, 'gst_amount', item_subtotal * (gst_rate / 100))
                total = getattr(item, 'total', item_subtotal + gst_amount)

            # Add item row with alternating background
            if row_count % 2 == 0:
                c.setFillColor(colors.white)
            else:
                c.setFillColor(light_gray)

            c.rect(40, y_position - 20, width - 80, 20, fill=1, stroke=0)
            c.setStrokeColor(colors.black)
            c.rect(40, y_position - 20, width - 80, 20, fill=0, stroke=1)

            # Add item details
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 8)

            # Draw item details with the new column structure
            values = [
                item_name,
                str(quantity),
                f"Rs.{price:.1f}",
                f"Rs.{item_subtotal:.1f}",
                f"{gst_rate:.1f}%",
                f"Rs.{total:.1f}"
            ]

            for i, value in enumerate(values):
                if i < 2:  # Left align text fields
                    c.drawString(col_positions[i] + 5, y_position - 15, value)
                else:  # Right align numeric fields
                    text_width = c.stringWidth(value, "Helvetica", 8)
                    c.drawString(col_positions[i+1] - text_width - 5, y_position - 15, value)

            # Update totals
            subtotal += item_subtotal
            total_tax += gst_amount
            total_amount += total

            # Move to next row
            y_position -= 25
            row_count += 1

        # Add summary section
        y_position -= 20

        # Left box for financial calculations
        c.setFillColor(light_gray)
        c.rect(40, y_position - 100, (width - 80) / 2 - 5, 100, fill=1, stroke=0)
        c.setStrokeColor(colors.black)
        c.rect(40, y_position - 100, (width - 80) / 2 - 5, 100, fill=0, stroke=1)

        # Right box for quotation information
        c.setFillColor(light_gray)
        c.rect(40 + (width - 80) / 2 + 5, y_position - 100, (width - 80) / 2 - 5, 100, fill=1, stroke=0)
        c.setStrokeColor(colors.black)
        c.rect(40 + (width - 80) / 2 + 5, y_position - 100, (width - 80) / 2 - 5, 100, fill=0, stroke=1)

        # Define column positions for summary
        left_col_x = 60
        right_col_x = 40 + (width - 80) / 2 + 25

        # Add left column headers (financial calculations)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left_col_x, y_position - 20, "Subtotal:")
        c.drawString(left_col_x, y_position - 40, "GST:")
        c.drawString(left_col_x, y_position - 60, "Total:")

        # Add left column values with right alignment
        c.setFont("Helvetica", 10)
        c.drawRightString(left_col_x + 150, y_position - 20, f"Rs.{subtotal:.1f}")
        c.drawRightString(left_col_x + 150, y_position - 40, f"Rs.{total_tax:.1f}")
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(left_col_x + 150, y_position - 60, f"Rs.{total_amount:.1f}")

        # Add right column headers (quotation information)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(right_col_x, y_position - 20, "Validity:")
        if asked_about:
            c.drawString(right_col_x, y_position - 40, "Regarding:")

        # Add right column values
        c.setFont("Helvetica", 10)
        c.drawString(right_col_x + 70, y_position - 20, "30 days from issue date")
        if asked_about:
            # Wrap text if too long
            if len(asked_about) > 30:
                c.drawString(right_col_x + 70, y_position - 40, asked_about[:30] + "...")
                c.drawString(right_col_x + 70, y_position - 55, asked_about[30:60] + ("..." if len(asked_about) > 60 else ""))
            else:
                c.drawString(right_col_x + 70, y_position - 40, asked_about)

        # Add footer
        footer_y = 50
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)

        # Center the footer text
        footer_text = "Thank you for your business!"
        text_width = c.stringWidth(footer_text, "Helvetica", 9)
        c.drawString((width - text_width) / 2, footer_y, footer_text)

        footer_text = "For any queries, please contact us at contactsunmax@gmail.com"
        text_width = c.stringWidth(footer_text, "Helvetica", 9)
        c.drawString((width - text_width) / 2, footer_y - 15, footer_text)

        footer_text = "This is a computer-generated quotation and does not require a signature."
        text_width = c.stringWidth(footer_text, "Helvetica", 9)
        c.drawString((width - text_width) / 2, footer_y - 30, footer_text)

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
