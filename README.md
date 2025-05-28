# Sunmax Renewables Management System

A comprehensive business management system for Sunmax Renewables, built with FastAPI, SQLite, and modern web technologies.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Modules](#modules)
- [Database](#database)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [PDF Generation](#pdf-generation)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Overview

The Sunmax Renewables Management System is a comprehensive business management application designed to streamline operations, manage inventory, track sales, handle customer enquiries, and generate professional invoices and quotations. The system provides a user-friendly interface for managing all aspects of the business.

## Features

### Inventory Management
- Add, edit, and delete inventory items
- Track stock levels and pricing
- Search and filter inventory
- Import/export inventory data

### Sales and Invoicing
- Create and manage invoices
- Track payment status
- Generate professional PDF invoices
- Record and track payments
- Support for both product and service invoices

### Customer Management
- Maintain customer database
- Track customer purchases and payment history
- Generate customer statements
- Manage customer enquiries

### Enquiry Management
- Record and track customer enquiries
- Convert enquiries to quotations
- Upload and store quotation files (PDF/Excel)
- Track quotation status

### Quotation System
- Create professional quotations
- Convert quotations to invoices
- Track quotation status
- Generate PDF quotations

### Expenses Management
- Track business expenses and vendor payments
- Record different types of expenses (product purchases, salaries, utilities, etc.)
- Monitor payment status and methods
- Generate expense reports and analytics
- Manage vendor information and GST details

### User Management
- Role-based access control
- Secure authentication
- User activity tracking
- Password management

### Reporting & Analytics
- Sales reports and insights
- Inventory reports
- Customer reports
- Expense tracking and analysis
- Financial summaries and performance metrics

### Document Storage
- Store and manage important documents
- Organize files by category
- Secure access to sensitive files

### Information & Documentation
- Built-in user guide and help system
- Step-by-step instructions for each feature
- Best practices and tips for efficient usage

## System Requirements

- Python 3.8 or higher
- SQLite database
- Modern web browser (Chrome, Firefox, Edge, Safari)
- Minimum 4GB RAM
- 100MB disk space (excluding database growth)

## Installation

### Option 1: Standard Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-organization/sunmax-renewables.git
   cd sunmax-renewables
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```
   python init_db.py
   ```

5. Create necessary directories:
   ```
   python setup_directories.py
   ```
   This script creates all required directories that are excluded from Git.

6. Start the application:
   ```
   python -m app.main
   ```

7. Access the application at http://localhost:8000

### Option 2: Docker Installation

For easy deployment, you can use Docker:

1. Pull the Docker image:
   ```
   docker pull shaik07/sunmax-renewables:latest
   ```

2. Run the container:
   ```
   docker run -p 8080:8080 -d \
     -v ~/sunmax-data/db:/app/db \
     -v ~/sunmax-data/invoices:/app/invoices \
     -v ~/sunmax-data/exports:/app/exports \
     --name sunmax-renewables \
     shaik07/sunmax-renewables:latest
   ```

3. Access the application at http://localhost:8080

For detailed Docker instructions, including how to build and push the image, see [docker_instructions.md](docker_instructions.md).

## Usage

### First-time Setup

1. Log in with the default admin credentials:
   - Username: contactsunmax@gmail.com
   - Password: Sunmax@123

2. Change the default password immediately after first login

3. Set up your company profile in the settings

4. Add inventory items, services, and initial customer data

### Daily Operations

1. **Inventory Management**
   - Add new inventory items as they arrive
   - Update stock levels and pricing as needed
   - Generate inventory reports

2. **Sales Process**
   - Record customer enquiries
   - Create quotations for potential customers
   - Convert quotations to invoices when confirmed
   - Record payments against invoices

3. **Customer Management**
   - Add new customers
   - Track customer interactions
   - Manage payment records

4. **Expense Management**
   - Record business expenses and vendor payments
   - Track different expense categories
   - Monitor payment status and methods
   - Generate expense reports

5. **Reporting & Analytics**
   - Generate daily, weekly, or monthly reports
   - Track sales performance
   - Monitor inventory levels
   - Analyze expense patterns and trends

## Project Structure

```
sunmax-renewables/
├── app/
│   ├── api/                 # API endpoints
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── customers.py     # Customer management
│   │   ├── enquiries.py     # Enquiry management
│   │   ├── expenses.py      # Expense tracking
│   │   ├── inventory.py     # Inventory management
│   │   ├── invoices.py      # Invoice operations
│   │   ├── quotations.py    # Quotation management
│   │   └── services.py      # Service management
│   ├── core/                # Core functionality
│   ├── db/                  # Database models and operations
│   ├── schemas/             # Pydantic schemas
│   └── main.py              # Application entry point
├── db/                      # Database files
│   └── sunmax.db            # SQLite database
├── static/                  # Static assets
│   ├── css/                 # CSS files
│   ├── js/                  # JavaScript files
│   └── images/              # Image files
├── templates/               # HTML templates
├── quotations/              # Stored quotation files
├── invoices/                # Generated invoice PDFs
├── exports/                 # Exported data files
├── documents/               # Document storage
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker configuration
└── README.md                # This file
```

## Modules

### Inventory Module

The inventory module allows you to manage your product catalog, track stock levels, and monitor pricing. Key features include:

- Add, edit, and delete inventory items
- Track stock levels with automatic updates when sales occur
- Set purchase price, margin, and selling price
- Import/export inventory data via Excel
- Search and filter inventory items

### Sales Module

The sales module handles the entire sales process from quotation to invoice to payment. Key features include:

- Create and manage quotations
- Convert quotations to invoices
- Track payment status (Unpaid, Partially Paid, Fully Paid)
- Record multiple payments against invoices
- Generate professional PDF invoices
- Email invoices directly to customers

### Enquiry Module

The enquiry module helps track potential customer leads and their requirements. Key features include:

- Record customer enquiries with contact details
- Track quotation status
- Upload and store quotation files (PDF/Excel)
- Convert enquiries to sales
- Search and filter enquiries

### Expenses Module

The expenses module helps track all business expenditures and vendor payments. Key features include:

- Record various types of expenses (product purchases, salaries, utilities, rent, etc.)
- Track vendor information including GST details and contact information
- Monitor payment status (Paid, Pending, Partially Paid)
- Support multiple payment methods (Cash, Bank Transfer, UPI, Card, Cheque)
- Generate expense reports and analytics
- Export expense data for accounting purposes
- Search and filter expenses by type, vendor, date, or status

### Customer Module

The customer module maintains your customer database and tracks their history. Key features include:

- Maintain customer contact information
- Track purchase history
- Record payment history
- Generate customer statements
- Search and filter customers

### User Module

The user module manages system access and security. Key features include:

- Role-based access control (Top User, Admin, Employee)
- Secure password management
- User activity logging
- Account management

### Document Storage Module

The document storage module provides a centralized location for important files. Key features include:

- Upload and store important documents
- Categorize files by type
- Control access to sensitive documents
- Search for documents

## Database

The application uses SQLite as its database engine. The main database file is located at `db/sunmax.db`.

### Key Tables

- `inventory`: Stores product information
- `invoices`: Stores invoice header information
- `invoice_items`: Stores invoice line items
- `payments`: Records payments against invoices
- `customers`: Stores customer information
- `enquiries`: Records customer enquiries
- `quotations`: Stores quotation information
- `expenses`: Records business expenses and vendor payments
- `expense_payments`: Tracks payments made for expenses
- `users`: Manages user accounts and permissions
- `services`: Tracks service offerings

## API Endpoints

The application provides a RESTful API for all operations. Some key endpoints include:

- `/api/inventory`: Inventory management
- `/api/invoices`: Invoice operations
- `/api/customers`: Customer management
- `/api/enquiries`: Enquiry tracking
- `/api/quotations`: Quotation management
- `/api/expenses`: Expense tracking and management
- `/api/users`: User administration
- `/api/documents`: Document storage
- `/api/auth`: Authentication and authorization

## Authentication

The system uses JWT (JSON Web Tokens) for authentication. Access tokens are valid for 30 minutes, after which they need to be refreshed.

### User Roles

- **Top User**: Full access to all system features, including user management
- **Admin**: Access to most features except user management
- **Employee**: Limited access to day-to-day operations

## PDF Generation

The system generates professional PDFs for:

- Invoices
- Quotations
- Customer statements
- Reports

PDF templates can be customized in the templates directory.

## Troubleshooting

### Common Issues

1. **Database Errors**
   - Run `python migrate_db.py` to update the database schema
   - Check file permissions on the database file

2. **PDF Generation Issues**
   - Ensure all required fonts are installed
   - Check that the templates directory is accessible

3. **File Upload Problems**
   - Verify that the upload directories exist and are writable
   - Check file size limits in the configuration

## Version Control & GitHub

### .gitignore Configuration

The project is configured to exclude certain directories from version control to avoid storing sensitive business data in GitHub:

- `invoices/`: Contains generated PDF invoices
- `quotations/`: Stores quotation files uploaded by users
- `customers/`: Customer-related documents
- `services/`: Service-related files
- `payments/`: Payment records and receipts
- `documents/`: General document storage
- `db/`: Database files and backups

These directories are listed in the `.gitignore` file to ensure they are not tracked by Git. When deploying the application, you'll need to create these directories manually or have the application create them at runtime.

### Data Backup

Since these directories contain important business data but are not stored in Git, it's essential to implement a regular backup strategy:

1. Set up automated backups of these directories
2. Store backups securely in an off-site location
3. Test backup restoration periodically

## Latest Updates & Features

### Recent Additions (2024)

- **Expenses Management System**: Complete expense tracking with vendor management, payment status monitoring, and detailed analytics
- **Built-in Documentation**: Interactive help system with step-by-step guides for all features
- **Enhanced Analytics**: Improved insights dashboard with expense tracking and performance metrics
- **Docker Support**: Full containerization with simplified deployment using Docker Hub
- **Improved UI/UX**: Modern interface with better navigation and user experience
- **Enhanced Security**: Updated authentication system with improved session management

### Upcoming Features

- Advanced reporting with custom date ranges
- Email notifications for important events
- Mobile-responsive design improvements
- API documentation with Swagger/OpenAPI
- Automated backup scheduling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

Please follow the coding standards and include appropriate tests for new features.

## Demo Video
[Demo Video](https://www.linkedin.com/posts/shaik-hidaythulla_aiassisteddevelopment-softwaredevelopment-activity-7327935840645464064-TD6z?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEyF3F8BG29hhzPFUzK484jVQWqnvaw-A60)


This demonstration video provides a walkthrough of the main features of the Sunmax Renewables Management System, including:

- User interface navigation and dashboard overview
- Creating and managing enquiries
- Uploading and downloading quotation files
- Managing inventory items and services
- Generating invoices and tracking payments
- Expense management and vendor tracking
- Document storage functionality
- User management and permissions
- Built-in help and documentation system
- Analytics and reporting features


