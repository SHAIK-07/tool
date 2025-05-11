"""
PDF Generator module for Sunmax Application.

This module provides functions for generating PDF files for invoices and quotations.
It imports the actual implementations from the core.pdf_generator module.
"""

from app.core.pdf_generator import generate_pdf_invoice, generate_pdf_quotation

# Re-export the functions
__all__ = ['generate_pdf_invoice', 'generate_pdf_quotation']
