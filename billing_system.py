import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
from datetime import datetime, timedelta
import os
import re
import csv
import json
import webbrowser
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import threading
import time

class BillingSystem:
    def __init__(self, parent, current_user):
        self.parent = parent
        self.current_user = current_user
        
        # Create database tables if they don't exist
        self.create_billing_tables()
        
        # Initialize variables
        self.customer_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.date_from_var = tk.StringVar()
        self.date_to_var = tk.StringVar()
        self.status_var = tk.StringVar(value="All")
        
        # Set default dates (last 30 days)
        today = datetime.now()
        thirty_days_ago = today - timedelta(days=30)
        
        self.date_from_var.set(thirty_days_ago.strftime('%Y-%m-%d'))
        self.date_to_var.set(today.strftime('%Y-%m-%d'))
        
        # Setup the billing tab
        self.setup_billing_tab()
    
    def create_billing_tables(self):
        """Create necessary database tables for billing system"""
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        # Create customers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT,
            tax_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
        ''')
        
        # Create invoices table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            customer_id INTEGER NOT NULL,
            invoice_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date TIMESTAMP,
            subtotal REAL NOT NULL,
            tax_rate REAL DEFAULT 0,
            tax_amount REAL DEFAULT 0,
            discount_rate REAL DEFAULT 0,
            discount_amount REAL DEFAULT 0,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'Unpaid',
            notes TEXT,
            created_by INTEGER,
            FOREIGN KEY (customer_id) REFERENCES customers (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
        ''')
        
        # Create invoice_items table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            description TEXT,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices (id),
            FOREIGN KEY (item_id) REFERENCES inventory (id)
        )
        ''')
        
        # Create payments table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            amount REAL NOT NULL,
            payment_method TEXT,
            reference_number TEXT,
            notes TEXT,
            recorded_by INTEGER,
            FOREIGN KEY (invoice_id) REFERENCES invoices (id),
            FOREIGN KEY (recorded_by) REFERENCES users (id)
        )
        ''')
        
        # Create invoice_templates table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoice_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            header TEXT,
            footer TEXT,
            logo_path TEXT,
            color_theme TEXT,
            is_default INTEGER DEFAULT 0
        )
        ''')
        
        # Insert default template if not exists
        cursor.execute("SELECT COUNT(*) FROM invoice_templates")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
            INSERT INTO invoice_templates (name, header, footer, color_theme, is_default)
            VALUES (?, ?, ?, ?, ?)
            ''', ('Default Template', 'INVOICE', 'Thank you for your business!', '#4CAF50', 1))
        
        # Create payment_gateways table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_gateways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            api_key TEXT,
            secret_key TEXT,
            is_active INTEGER DEFAULT 0
        )
        ''')
        
        # Insert default payment gateways if not exists
        cursor.execute("SELECT COUNT(*) FROM payment_gateways")
        if cursor.fetchone()[0] == 0:
            default_gateways = [
                ('Cash', '', '', 1),
                ('Bank Transfer', '', '', 1),
                ('Credit Card', '', '', 0),
                ('PayPal', '', '', 0)
            ]
            cursor.executemany('''
            INSERT INTO payment_gateways (name, api_key, secret_key, is_active)
            VALUES (?, ?, ?, ?)
            ''', default_gateways)
        
        # Create billing_settings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS billing_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_name TEXT UNIQUE NOT NULL,
            setting_value TEXT
        )
        ''')
        
        # Insert default settings if not exists
        cursor.execute("SELECT COUNT(*) FROM billing_settings")
        if cursor.fetchone()[0] == 0:
            default_settings = [
                ('default_tax_rate', '7.5'),
                ('invoice_prefix', 'INV-'),
                ('invoice_starting_number', '1001'),
                ('default_due_days', '30'),
                ('company_name', 'My Company'),
                ('company_address', '123 Main Street, City, Country'),
                ('company_phone', '+1 (555) 123-4567'),
                ('company_email', 'billing@mycompany.com'),
                ('company_website', 'www.mycompany.com'),
                ('company_tax_id', '123456789'),
                ('currency_symbol', '$'),
                ('smtp_server', ''),
                ('smtp_port', '587'),
                ('smtp_username', ''),
                ('smtp_password', ''),
                ('reminder_days_before', '3,7,14')
            ]
            cursor.executemany('''
            INSERT INTO billing_settings (setting_name, setting_value)
            VALUES (?, ?)
            ''', default_settings)
        
        conn.commit()
        conn.close()
    
    def setup_billing_tab(self):
        """Set up the main billing tab with sub-tabs"""
        # Create notebook for billing sections
        self.billing_notebook = ttk.Notebook(self.parent)
        self.billing_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Invoices tab
        self.invoices_tab = ttk.Frame(self.billing_notebook)
        self.billing_notebook.add(self.invoices_tab, text="Invoices")
        
        # Customers tab
        self.customers_tab = ttk.Frame(self.billing_notebook)
        self.billing_notebook.add(self.customers_tab, text="Customers")
        
        # Payments tab
        self.payments_tab = ttk.Frame(self.billing_notebook)
        self.billing_notebook.add(self.payments_tab, text="Payments")
        
        # Reports tab
        self.billing_reports_tab = ttk.Frame(self.billing_notebook)
        self.billing_notebook.add(self.billing_reports_tab, text="Reports")
        
        # Settings tab (only for admin users)
        if self.current_user["role"] == "admin":
            self.billing_settings_tab = ttk.Frame(self.billing_notebook)
            self.billing_notebook.add(self.billing_settings_tab, text="Settings")
        
        # Initialize tabs
        self.setup_invoices_tab()
        self.setup_customers_tab()
        self.setup_payments_tab()
        self.setup_billing_reports_tab()
        
        if self.current_user["role"] == "admin":
            self.setup_billing_settings_tab()
    
    def setup_invoices_tab(self):
        """Set up the invoices tab with invoice listing and management"""
        # Create frame for invoices content
        invoices_content = ttk.Frame(self.invoices_tab, style="TFrame")
        invoices_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Search and filter bar
        filter_frame = ttk.Frame(invoices_content, style="TFrame")
        filter_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Search
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # Date range
        ttk.Label(filter_frame, text="From:").pack(side=tk.LEFT, padx=(0, 5))
        from_date_entry = ttk.Entry(filter_frame, textvariable=self.date_from_var, width=12)
        from_date_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(filter_frame, text="To:").pack(side=tk.LEFT, padx=(0, 5))
        to_date_entry = ttk.Entry(filter_frame, textvariable=self.date_to_var, width=12)
        to_date_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # Status filter
        ttk.Label(filter_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_var, 
                                   values=["All", "Paid", "Unpaid", "Partial", "Overdue"], 
                                   state="readonly", width=10)
        status_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # Filter button
        filter_button = ttk.Button(filter_frame, text="Filter", 
                                  command=self.load_invoices)
        filter_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Reset button
        reset_button = ttk.Button(filter_frame, text="Reset", 
                                 command=self.reset_invoice_filters)
        reset_button.pack(side=tk.LEFT)
        
        # Action buttons
        action_frame = ttk.Frame(invoices_content, style="TFrame")
        action_frame.pack(fill=tk.X, pady=(0, 20))
        
        create_button = ttk.Button(action_frame, text="Create Invoice", 
                                  command=self.show_create_invoice_dialog)
        create_button.pack(side=tk.LEFT, padx=(0, 10))
        
        view_button = ttk.Button(action_frame, text="View/Edit Invoice", 
                                command=self.show_view_invoice_dialog)
        view_button.pack(side=tk.LEFT, padx=(0, 10))
        
        delete_button = ttk.Button(action_frame, text="Delete Invoice", 
                                  style="Danger.TButton", command=self.delete_invoice)
        delete_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Invoices table
        table_frame = ttk.Frame(invoices_content, style="TFrame")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview
        columns = ("id", "invoice_number", "customer", "date", "due_date", "total", "status")
        self.invoices_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Define headings
        self.invoices_tree.heading("id", text="ID")
        self.invoices_tree.heading("invoice_number", text="Invoice #")
        self.invoices_tree.heading("customer", text="Customer")
        self.invoices_tree.heading("date", text="Invoice Date")
        self.invoices_tree.heading("due_date", text="Due Date")
        self.invoices_tree.heading("total", text="Total Amount")
        self.invoices_tree.heading("status", text="Status")
        
        # Define columns
        self.invoices_tree.column("id", width=50, anchor=tk.CENTER)
        self.invoices_tree.column("invoice_number", width=100, anchor=tk.CENTER)
        self.invoices_tree.column("customer", width=200)
        self.invoices_tree.column("date", width=120, anchor=tk.CENTER)
        self.invoices_tree.column("due_date", width=120, anchor=tk.CENTER)
        self.invoices_tree.column("total", width=120, anchor=tk.E)
        self.invoices_tree.column("status", width=100, anchor=tk.CENTER)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.invoices_tree.yview)
        self.invoices_tree.configure(yscroll=y_scrollbar.set)
        
        x_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.invoices_tree.xview)
        self.invoices_tree.configure(xscroll=x_scrollbar.set)
        
        # Pack widgets
        self.invoices_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind double-click to view/edit
        self.invoices_tree.bind("<Double-1>", lambda event: self.show_view_invoice_dialog())
        
        # Load invoices
        self.load_invoices()
    
    def load_invoices(self):
        """Load invoices into the treeview based on filters"""
        # Clear existing items
        for item in self.invoices_tree.get_children():
            self.invoices_tree.delete(item)
        
        # Get filter values
        search_term = self.search_var.get().lower()
        from_date = self.date_from_var.get()
        to_date = self.date_to_var.get()
        status = self.status_var.get()
        
        # Validate dates
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
            # Add time to make it end of day
            to_date_obj = to_date_obj.replace(hour=23, minute=59, second=59)
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
            return
        
        # Build query based on filters
        query = '''
        SELECT i.id, i.invoice_number, c.name, i.invoice_date, i.due_date, 
               i.total_amount, i.status
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.invoice_date BETWEEN ? AND ?
        '''
        
        params = [from_date_obj.isoformat(), to_date_obj.isoformat()]
        
        if status != "All":
            query += " AND i.status = ?"
            params.append(status)
        
        if search_term:
            query += " AND (LOWER(i.invoice_number) LIKE ? OR LOWER(c.name) LIKE ?)"
            params.extend([f'%{search_term}%', f'%{search_term}%'])
        
        query += " ORDER BY i.invoice_date DESC"
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        invoices = cursor.fetchall()
        conn.close()
        
        # Get currency symbol
        currency_symbol = self.get_setting('currency_symbol')
        
        # Insert into treeview
        for invoice in invoices:
            inv_id, inv_number, customer, date, due_date, total, status = invoice
            
            # Format dates
            try:
                date_formatted = datetime.fromisoformat(date).strftime('%Y-%m-%d')
            except:
                date_formatted = date
            
            try:
                due_date_formatted = datetime.fromisoformat(due_date).strftime('%Y-%m-%d')
            except:
                due_date_formatted = due_date
            
            # Format total
            total_formatted = f"{currency_symbol}{total:.2f}"
            
            # Determine tag based on status
            tag = status.lower()
            
            self.invoices_tree.insert('', tk.END, values=(
                inv_id, inv_number, customer, date_formatted, due_date_formatted, 
                total_formatted, status
            ), tags=(tag,))
        
        # Configure tags for status colors
        self.invoices_tree.tag_configure('paid', background='#d4edda')
        self.invoices_tree.tag_configure('unpaid', background='#fff3cd')
        self.invoices_tree.tag_configure('partial', background='#d1ecf1')
        self.invoices_tree.tag_configure('overdue', background='#f8d7da')
    
    def reset_invoice_filters(self):
        """Reset invoice filters to default values"""
        self.search_var.set("")
        self.status_var.set("All")
        
        # Reset date range to last 30 days
        today = datetime.now()
        thirty_days_ago = today - timedelta(days=30)
        
        self.date_from_var.set(thirty_days_ago.strftime('%Y-%m-%d'))
        self.date_to_var.set(today.strftime('%Y-%m-%d'))
        
        # Reload invoices
        self.load_invoices()
    
    def show_create_invoice_dialog(self):
        """Show dialog to create a new invoice"""
        # Create a new top-level window
        dialog = tk.Toplevel(self.parent)
        dialog.title("Create New Invoice")
        dialog.geometry("900x700")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create main frame
        main_frame = ttk.Frame(dialog, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create form frame
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Invoice header
        header_frame = ttk.LabelFrame(form_frame, text="Invoice Information")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Left column
        left_col = ttk.Frame(header_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Invoice number
        ttk.Label(left_col, text="Invoice Number:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Get next invoice number
        next_invoice_number = self.generate_invoice_number()
        
        invoice_number_var = tk.StringVar(value=next_invoice_number)
        invoice_number_entry = ttk.Entry(left_col, textvariable=invoice_number_var, width=20)
        invoice_number_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Invoice date
        ttk.Label(left_col, text="Invoice Date:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        
        invoice_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        invoice_date_entry = ttk.Entry(left_col, textvariable=invoice_date_var, width=20)
        invoice_date_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Due date
        ttk.Label(left_col, text="Due Date:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        
        # Calculate default due date (e.g., 30 days from now)
        default_due_days = int(self.get_setting('default_due_days'))
        default_due_date = (datetime.now() + timedelta(days=default_due_days)).strftime('%Y-%m-%d')
        
        due_date_var = tk.StringVar(value=default_due_date)
        due_date_entry = ttk.Entry(left_col, textvariable=due_date_var, width=20)
        due_date_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        # Right column
        right_col = ttk.Frame(header_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Customer selection
        ttk.Label(right_col, text="Customer:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Get customers from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM customers ORDER BY name")
        customers = [(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()
        
        # If no customers exist, show message and return
        if not customers:
            messagebox.showinfo("No Customers", "Please add a customer first.")
            dialog.destroy()
            self.show_add_customer_dialog()
            return
        
        # Create a dictionary to map customer names to IDs
        customer_dict = {customer[1]: customer[0] for customer in customers}
        
        customer_var = tk.StringVar()
        customer_combo = ttk.Combobox(right_col, textvariable=customer_var, 
                                     values=[customer[1] for customer in customers], width=30)
        customer_combo.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Add new customer button
        add_customer_button = ttk.Button(right_col, text="Add New", 
                                        command=lambda: self.show_add_customer_dialog(dialog))
        add_customer_button.grid(row=0, column=2, padx=(5, 0), pady=(0, 10))
        
        # Tax rate
        ttk.Label(right_col, text="Tax Rate (%):").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        
        default_tax_rate = self.get_setting('default_tax_rate')
        tax_rate_var = tk.StringVar(value=default_tax_rate)
        tax_rate_entry = ttk.Entry(right_col, textvariable=tax_rate_var, width=10)
        tax_rate_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Discount rate
        ttk.Label(right_col, text="Discount (%):").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        
        discount_rate_var = tk.StringVar(value="0")
        discount_rate_entry = ttk.Entry(right_col, textvariable=discount_rate_var, width=10)
        discount_rate_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        # Items section
        items_frame = ttk.LabelFrame(main_frame, text="Invoice Items")
        items_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create treeview for items
        columns = ("id", "item", "description", "quantity", "price", "total")
        items_tree = ttk.Treeview(items_frame, columns=columns, show="headings", height=10)
        
        # Define headings
        items_tree.heading("id", text="ID")
        items_tree.heading("item", text="Item")
        items_tree.heading("description", text="Description")
        items_tree.heading("quantity", text="Quantity")
        items_tree.heading("price", text="Unit Price")
        items_tree.heading("total", text="Total")
        
        # Define columns
        items_tree.column("id", width=50, anchor=tk.CENTER)
        items_tree.column("item", width=200)
        items_tree.column("description", width=250)
        items_tree.column("quantity", width=80, anchor=tk.CENTER)
        items_tree.column("price", width=100, anchor=tk.E)
        items_tree.column("total", width=100, anchor=tk.E)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, command=items_tree.yview)
        items_tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Item action buttons
        item_buttons_frame = ttk.Frame(main_frame)
        item_buttons_frame.pack(fill=tk.X, pady=(0, 20))
        
        add_item_button = ttk.Button(item_buttons_frame, text="Add Item", 
                                    command=lambda: self.show_add_invoice_item_dialog(items_tree))
        add_item_button.pack(side=tk.LEFT, padx=(0, 10))
        
        edit_item_button = ttk.Button(item_buttons_frame, text="Edit Item", 
                                     command=lambda: self.edit_invoice_item(items_tree))
        edit_item_button.pack(side=tk.LEFT, padx=(0, 10))
        
        remove_item_button = ttk.Button(item_buttons_frame, text="Remove Item", 
                                       style="Danger.TButton", 
                                       command=lambda: self.remove_invoice_item(items_tree))
        remove_item_button.pack(side=tk.LEFT)
        
        # Totals section
        totals_frame = ttk.Frame(main_frame)
        totals_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Create a frame for the totals on the right
        totals_right = ttk.Frame(totals_frame)
        totals_right.pack(side=tk.RIGHT)
        
        # Subtotal
        ttk.Label(totals_right, text="Subtotal:").grid(row=0, column=0, sticky=tk.E, pady=(0, 5))
        subtotal_var = tk.StringVar(value="0.00")
        subtotal_label = ttk.Label(totals_right, textvariable=subtotal_var, width=15, anchor=tk.E)
        subtotal_label.grid(row=0, column=1, sticky=tk.E, pady=(0, 5))
        
        # Tax
        ttk.Label(totals_right, text="Tax:").grid(row=1, column=0, sticky=tk.E, pady=(0, 5))
        tax_var = tk.StringVar(value="0.00")
        tax_label = ttk.Label(totals_right, textvariable=tax_var, width=15, anchor=tk.E)
        tax_label.grid(row=1, column=1, sticky=tk.E, pady=(0, 5))
        
        # Discount
        ttk.Label(totals_right, text="Discount:").grid(row=2, column=0, sticky=tk.E, pady=(0, 5))
        discount_var = tk.StringVar(value="0.00")
        discount_label = ttk.Label(totals_right, textvariable=discount_var, width=15, anchor=tk.E)
        discount_label.grid(row=2, column=1, sticky=tk.E, pady=(0, 5))
        
        # Total
        ttk.Label(totals_right, text="Total:", font=("Helvetica", 10, "bold")).grid(row=3, column=0, sticky=tk.E, pady=(5, 0))
        total_var = tk.StringVar(value="0.00")
        total_label = ttk.Label(totals_right, textvariable=total_var, width=15, anchor=tk.E, font=("Helvetica", 10, "bold"))
        total_label.grid(row=3, column=1, sticky=tk.E, pady=(5, 0))
        
        # Notes section
        notes_frame = ttk.LabelFrame(main_frame, text="Notes")
        notes_frame.pack(fill=tk.X, pady=(0, 20))
        
        notes_text = tk.Text(notes_frame, height=3, width=50)
        notes_text.pack(fill=tk.X, padx=10, pady=10)
        
        # Function to calculate totals
        def calculate_totals():
            # Get all items
            items = []
            for item_id in items_tree.get_children():
                item_values = items_tree.item(item_id, 'values')
                items.append(item_values)
            
            # Calculate subtotal
            subtotal = sum(float(item[5].replace(self.get_setting('currency_symbol'), '')) for item in items)
            
            # Calculate tax
            try:
                tax_rate = float(tax_rate_var.get())
                tax_amount = subtotal * (tax_rate / 100)
            except ValueError:
                tax_rate = 0
                tax_amount = 0
            
            # Calculate discount
            try:
                discount_rate = float(discount_rate_var.get())
                discount_amount = subtotal * (discount_rate / 100)
            except ValueError:
                discount_rate = 0
                discount_amount = 0
            
            # Calculate total
            total = subtotal + tax_amount - discount_amount
            
            # Update labels
            currency = self.get_setting('currency_symbol')
            subtotal_var.set(f"{currency}{subtotal:.2f}")
            tax_var.set(f"{currency}{tax_amount:.2f}")
            discount_var.set(f"{currency}{discount_amount:.2f}")
            total_var.set(f"{currency}{total:.2f}")
            
            return subtotal, tax_amount, discount_amount, total
        
        # Bind tax and discount entries to recalculate totals
        tax_rate_var.trace("w", lambda name, index, mode: calculate_totals())
        discount_rate_var.trace("w", lambda name, index, mode: calculate_totals())
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        save_button = ttk.Button(button_frame, text="Save Invoice", 
                                command=lambda: self.save_invoice(
                                    invoice_number_var.get(),
                                    customer_dict.get(customer_var.get()),
                                    invoice_date_var.get(),
                                    due_date_var.get(),
                                    tax_rate_var.get(),
                                    discount_rate_var.get(),
                                    items_tree,
                                    notes_text.get("1.0", tk.END).strip(),
                                    calculate_totals,
                                    dialog
                                ))
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        save_print_button = ttk.Button(button_frame, text="Save & Print", 
                                      command=lambda: self.save_and_print_invoice(
                                          invoice_number_var.get(),
                                          customer_dict.get(customer_var.get()),
                                          invoice_date_var.get(),
                                          due_date_var.get(),
                                          tax_rate_var.get(),
                                          discount_rate_var.get(),
                                          items_tree,
                                          notes_text.get("1.0", tk.END).strip(),
                                          calculate_totals,
                                          dialog
                                      ))
        save_print_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT)
    
    def show_add_invoice_item_dialog(self, items_tree):
        """Show dialog to add an item to the invoice"""
        # Create a new top-level window
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add Invoice Item")
        dialog.geometry("500x400")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create form frame
        form_frame = ttk.Frame(dialog, padding="20 20 20 20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Item selection
        ttk.Label(form_frame, text="Item:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Get items from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, item_name, description, unit_price, quantity
        FROM inventory
        WHERE quantity > 0
        ORDER BY item_name
        ''')
        
        inventory_items = cursor.fetchall()
        conn.close()
        
        # Create dictionaries to map item names to details
        item_dict = {}
        for item in inventory_items:
            item_id, name, desc, price, qty = item
            item_dict[name] = {
                'id': item_id,
                'description': desc,
                'price': price,
                'available': qty
            }
        
        item_var = tk.StringVar()
        item_combo = ttk.Combobox(form_frame, textvariable=item_var, 
                                 values=list(item_dict.keys()), width=30)
        item_combo.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        description_var = tk.StringVar()
        description_entry = ttk.Entry(form_frame, textvariable=description_var, width=40)
        description_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Quantity
        ttk.Label(form_frame, text="Quantity:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        quantity_var = tk.StringVar(value="1")
        quantity_entry = ttk.Entry(form_frame, textvariable=quantity_var, width=10)
        quantity_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        # Available quantity
        available_var = tk.StringVar(value="")
        available_label = ttk.Label(form_frame, textvariable=available_var, foreground="gray")
        available_label.grid(row=2, column=1, sticky=tk.E, pady=(0, 10))
        
        # Unit price
        ttk.Label(form_frame, text="Unit Price:").grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        price_var = tk.StringVar()
        price_entry = ttk.Entry(form_frame, textvariable=price_var, width=15)
        price_entry.grid(row=3, column=1, sticky=tk.W, pady=(0, 10))
        
        # Total
        ttk.Label(form_frame, text="Total:").grid(row=4, column=0, sticky=tk.W, pady=(0, 10))
        total_var = tk.StringVar(value="0.00")
        total_label = ttk.Label(form_frame, textvariable=total_var)
        total_label.grid(row=4, column=1, sticky=tk.W, pady=(0, 10))
        
        # Function to update fields when item is selected
        def update_item_details(*args):
            selected_item = item_var.get()
            if selected_item in item_dict:
                item_details = item_dict[selected_item]
                description_var.set(item_details['description'] or "")
                price_var.set(f"{item_details['price']:.2f}")
                available_var.set(f"Available: {item_details['available']}")
                update_total()
        
        # Function to update total when quantity or price changes
        def update_total(*args):
            try:
                quantity = int(quantity_var.get())
                price = float(price_var.get())
                total = quantity * price
                currency = self.get_setting('currency_symbol')
                total_var.set(f"{currency}{total:.2f}")
            except ValueError:
                total_var.set("Invalid input")
        
        # Bind events
        item_var.trace("w", update_item_details)
        quantity_var.trace("w", update_total)
        price_var.trace("w", update_total)
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))
        
        add_button = ttk.Button(button_frame, text="Add Item", 
                               command=lambda: self.add_item_to_invoice(
                                   items_tree,
                                   item_dict.get(item_var.get(), {}).get('id', ''),
                                   item_var.get(),
                                   description_var.get(),
                                   quantity_var.get(),
                                   price_var.get(),
                                   dialog
                               ))
        add_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT)
    
    def add_item_to_invoice(self, items_tree, item_id, item_name, description, quantity, price, dialog):
        """Add an item to the invoice items treeview"""
        # Validate inputs
        if not item_name:
            messagebox.showerror("Error", "Please select an item", parent=dialog)
            return
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be a positive number")
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive number", parent=dialog)
            return
        
        try:
            price = float(price)
            if price < 0:
                raise ValueError("Price must be a non-negative number")
        except ValueError:
            messagebox.showerror("Error", "Price must be a valid number", parent=dialog)
            return
        
        # Calculate total
        total = quantity * price
        
        # Format price and total
        currency = self.get_setting('currency_symbol')
        price_formatted = f"{currency}{price:.2f}"
        total_formatted = f"{currency}{total:.2f}"
        
        # Add to treeview
        items_tree.insert('', tk.END, values=(
            item_id, item_name, description, quantity, price_formatted, total_formatted
        ))
        
        # Close dialog
        dialog.destroy()
        
        # Trigger recalculation of totals
        # This is done by simulating a change in the tax rate entry
        for widget in dialog.master.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Frame) and child.winfo_children():
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ttk.Entry) and grandchild.winfo_name().endswith('tax_rate_entry'):
                                grandchild.event_generate("<<Modified>>")
                                return
    
    def edit_invoice_item(self, items_tree):
        """Edit a selected item in the invoice"""
        # Get selected item
        selected = items_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select an item to edit")
            return
        
        # Get item values
        item_values = items_tree.item(selected[0], 'values')
        item_id, item_name, description, quantity, price, total = item_values
        
        # Remove currency symbol from price
        currency = self.get_setting('currency_symbol')
        price = price.replace(currency, '')
        
        # Create a new top-level window
        dialog = tk.Toplevel(self.parent)
        dialog.title("Edit Invoice Item")
        dialog.geometry("500x300")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create form frame
        form_frame = ttk.Frame(dialog, padding="20 20 20 20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Item name (read-only)
        ttk.Label(form_frame, text="Item:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        item_entry = ttk.Entry(form_frame, width=40)
        item_entry.insert(0, item_name)
        item_entry.configure(state="readonly")
        item_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        description_var = tk.StringVar(value=description)
        description_entry = ttk.Entry(form_frame, textvariable=description_var, width=40)
        description_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Quantity
        ttk.Label(form_frame, text="Quantity:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        quantity_var = tk.StringVar(value=quantity)
        quantity_entry = ttk.Entry(form_frame, textvariable=quantity_var, width=10)
        quantity_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        # Unit price
        ttk.Label(form_frame, text="Unit Price:").grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        price_var = tk.StringVar(value=price)
        price_entry = ttk.Entry(form_frame, textvariable=price_var, width=15)
        price_entry.grid(row=3, column=1, sticky=tk.W, pady=(0, 10))
        
        # Total
        ttk.Label(form_frame, text="Total:").grid(row=4, column=0, sticky=tk.W, pady=(0, 10))
        total_var = tk.StringVar()
        total_label = ttk.Label(form_frame, textvariable=total_var)
        total_label.grid(row=4, column=1, sticky=tk.W, pady=(0, 10))
        
        # Function to update total when quantity or price changes
        def update_total(*args):
            try:
                qty = int(quantity_var.get())
                prc = float(price_var.get())
                tot = qty * prc
                total_var.set(f"{currency}{tot:.2f}")
            except ValueError:
                total_var.set("Invalid input")
        
        # Initial update
        update_total()
        
        # Bind events
        quantity_var.trace("w", update_total)
        price_var.trace("w", update_total)
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))
        
        update_button = ttk.Button(button_frame, text="Update Item", 
                                  command=lambda: self.update_invoice_item(
                                      items_tree,
                                      selected[0],
                                      item_id,
                                      item_name,
                                      description_var.get(),
                                      quantity_var.get(),
                                      price_var.get(),
                                      dialog
                                  ))
        update_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT)
    
    def update_invoice_item(self, items_tree, item_id, orig_item_id, item_name, description, quantity, price, dialog):
        """Update an item in the invoice items treeview"""
        # Validate inputs
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be a positive number")
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive number", parent=dialog)
            return
        
        try:
            price = float(price)
            if price < 0:
                raise ValueError("Price must be a non-negative number")
        except ValueError:
            messagebox.showerror("Error", "Price must be a valid number", parent=dialog)
            return
        
        # Calculate total
        total = quantity * price
        
        # Format price and total
        currency = self.get_setting('currency_symbol')
        price_formatted = f"{currency}{price:.2f}"
        total_formatted = f"{currency}{total:.2f}"
        
        # Update treeview
        items_tree.item(item_id, values=(
            orig_item_id, item_name, description, quantity, price_formatted, total_formatted
        ))
        
        # Close dialog
        dialog.destroy()
        
        # Trigger recalculation of totals
        # This is done by simulating a change in the tax rate entry
        for widget in dialog.master.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Frame) and child.winfo_children():
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ttk.Entry) and grandchild.winfo_name().endswith('tax_rate_entry'):
                                grandchild.event_generate("<<Modified>>")
                                return
    
    def remove_invoice_item(self, items_tree):
        """Remove a selected item from the invoice"""
        # Get selected item
        selected = items_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select an item to remove")
            return
        
        # Remove from treeview
        items_tree.delete(selected[0])
        
        # Trigger recalculation of totals
        # Find the tax rate entry and simulate a change
        parent = items_tree.master
        while parent:
            for widget in parent.winfo_children():
                if isinstance(widget, ttk.Entry) and widget.winfo_name().endswith('tax_rate_entry'):
                    widget.event_generate("<<Modified>>")
                    return
            parent = parent.master
    
    def save_invoice(self, invoice_number, customer_id, invoice_date, due_date, tax_rate, discount_rate, items_tree, notes, calculate_totals, dialog):
        """Save the invoice to the database"""
        # Validate inputs
        if not invoice_number:
            messagebox.showerror("Error", "Invoice number is required", parent=dialog)
            return
        
        if not customer_id:
            messagebox.showerror("Error", "Please select a customer", parent=dialog)
            return
        
        # Validate dates
        try:
            invoice_date_obj = datetime.strptime(invoice_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error", "Invalid invoice date format. Use YYYY-MM-DD", parent=dialog)
            return
        
        try:
            due_date_obj = datetime.strptime(due_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error", "Invalid due date format. Use YYYY-MM-DD", parent=dialog)
            return
        
        # Get items
        items = []
        for item_id in items_tree.get_children():
            item_values = items_tree.item(item_id, 'values')
            items.append(item_values)
        
        if not items:
            messagebox.showerror("Error", "Please add at least one item to the invoice", parent=dialog)
            return
        
        # Calculate totals
        subtotal, tax_amount, discount_amount, total = calculate_totals()
        
        # Convert tax and discount rates to float
        try:
            tax_rate = float(tax_rate)
        except ValueError:
            tax_rate = 0
        
        try:
            discount_rate = float(discount_rate)
        except ValueError:
            discount_rate = 0
        
        # Insert into database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            # Check if invoice number already exists
            cursor.execute("SELECT id FROM invoices WHERE invoice_number = ?", (invoice_number,))
            if cursor.fetchone():
                messagebox.showerror("Error", "Invoice number already exists", parent=dialog)
                conn.close()
                return
            
            # Insert invoice
            cursor.execute('''
            INSERT INTO invoices (
                invoice_number, customer_id, invoice_date, due_date, 
                subtotal, tax_rate, tax_amount, discount_rate, discount_amount, 
                total_amount, status, notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                invoice_number, customer_id, invoice_date_obj.isoformat(), due_date_obj.isoformat(),
                subtotal, tax_rate, tax_amount, discount_rate, discount_amount,
                total, "Unpaid", notes, self.current_user["id"]
            ))
            
            # Get the ID of the new invoice
            invoice_id = cursor.lastrowid
            
            # Insert invoice items
            for item in items:
                item_id, item_name, description, quantity, price, item_total = item
                
                # Remove currency symbol from price and total
                currency = self.get_setting('currency_symbol')
                price = float(price.replace(currency, ''))
                item_total = float(item_total.replace(currency, ''))
                
                cursor.execute('''
                INSERT INTO invoice_items (
                    invoice_id, item_id, description, quantity, unit_price, total_price
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    invoice_id, item_id, description, quantity, price, item_total
                ))
                
                # Update inventory quantity
                cursor.execute('''
                UPDATE inventory
                SET quantity = quantity - ?
                WHERE id = ?
                ''', (int(quantity), item_id))
                
                # Add transaction record
                cursor.execute('''
                INSERT INTO transactions (
                    item_id, transaction_type, quantity, user_id, notes
                ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    item_id, 'out', quantity, self.current_user["id"], f"Invoice #{invoice_number}"
                ))
            
            conn.commit()
            messagebox.showinfo("Success", "Invoice created successfully", parent=dialog)
            
            # Close dialog and refresh invoices
            dialog.destroy()
            self.load_invoices()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to create invoice: {str(e)}", parent=dialog)
        
        finally:
            conn.close()
    
    def save_and_print_invoice(self, invoice_number, customer_id, invoice_date, due_date, tax_rate, discount_rate, items_tree, notes, calculate_totals, dialog):
        """Save the invoice and then print it"""
        # First save the invoice
        self.save_invoice(invoice_number, customer_id, invoice_date, due_date, tax_rate, discount_rate, items_tree, notes, calculate_totals, dialog)
        
        # Then get the invoice ID and print it
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM invoices WHERE invoice_number = ?", (invoice_number,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            invoice_id = result[0]
            self.generate_invoice_pdf(invoice_id, True)
    
    def show_view_invoice_dialog(self):
        """Show dialog to view/edit an existing invoice"""
        # Get selected invoice
        selected = self.invoices_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select an invoice to view")
            return
        
        # Get invoice ID
        invoice_id = self.invoices_tree.item(selected[0], 'values')[0]
        
        # Get invoice data from database
        conn = sqlite3.connect('inventory.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT i.*, c.name as customer_name
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.id = ?
        ''', (invoice_id,))
        
        invoice = cursor.fetchone()
        
        if not invoice:
            conn.close()
            messagebox.showerror("Error", "Invoice not found")
            return
        
        # Get invoice items
        cursor.execute('''
        SELECT ii.*, inv.item_name
        FROM invoice_items ii
        JOIN inventory inv ON ii.item_id = inv.id
        WHERE ii.invoice_id = ?
        ''', (invoice_id,))
        
        invoice_items = cursor.fetchall()
        
        # Get payments
        cursor.execute('''
        SELECT p.*, u.username
        FROM payments p
        JOIN users u ON p.recorded_by = u.id
        WHERE p.invoice_id = ?
        ORDER BY p.payment_date DESC
        ''', (invoice_id,))
        
        payments = cursor.fetchall()
        
        conn.close()
        
        # Create a new top-level window
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Invoice #{invoice['invoice_number']}")
        dialog.geometry("900x700")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create notebook for tabs
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Invoice details tab
        details_tab = ttk.Frame(notebook)
        notebook.add(details_tab, text="Invoice Details")
        
        # Payments tab
        payments_tab = ttk.Frame(notebook)
        notebook.add(payments_tab, text="Payments")
        
        # Setup invoice details tab
        self.setup_invoice_details_tab(details_tab, invoice, invoice_items, dialog)
        
        # Setup payments tab
        self.setup_invoice_payments_tab(payments_tab, invoice, payments, dialog)
    
    def setup_invoice_details_tab(self, parent, invoice, invoice_items, dialog):
        """Set up the invoice details tab"""
        # Create main frame
        main_frame = ttk.Frame(parent, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Invoice header
        header_frame = ttk.LabelFrame(main_frame, text="Invoice Information")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Left column
        left_col = ttk.Frame(header_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Invoice number
        ttk.Label(left_col, text="Invoice Number:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Label(left_col, text=invoice['invoice_number']).grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Invoice date
        ttk.Label(left_col, text="Invoice Date:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        invoice_date = datetime.fromisoformat(invoice['invoice_date']).strftime('%Y-%m-%d')
        ttk.Label(left_col, text=invoice_date).grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Due date
        ttk.Label(left_col, text="Due Date:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        due_date = datetime.fromisoformat(invoice['due_date']).strftime('%Y-%m-%d')
        ttk.Label(left_col, text=due_date).grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        # Right column
        right_col = ttk.Frame(header_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Customer
        ttk.Label(right_col, text="Customer:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Label(right_col, text=invoice['customer_name']).grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Status
        ttk.Label(right_col, text="Status:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        status_var = tk.StringVar(value=invoice['status'])
        status_combo = ttk.Combobox(right_col, textvariable=status_var, 
                                   values=["Paid", "Unpaid", "Partial", "Overdue"], 
                                   state="readonly", width=15)
        status_combo.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Update status button
        update_status_button = ttk.Button(right_col, text="Update", 
                                         command=lambda: self.update_invoice_status(
                                             invoice['id'], status_var.get(), dialog
                                         ))
        update_status_button.grid(row=1, column=2, padx=(5, 0), pady=(0, 10))
        
        # Items section
        items_frame = ttk.LabelFrame(main_frame, text="Invoice Items")
        items_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create treeview for items
        columns = ("id", "item", "description", "quantity", "price", "total")
        items_tree = ttk.Treeview(items_frame, columns=columns, show="headings", height=10)
        
        # Define headings
        items_tree.heading("id", text="ID")
        items_tree.heading("item", text="Item")
        items_tree.heading("description", text="Description")
        items_tree.heading("quantity", text="Quantity")
        items_tree.heading("price", text="Unit Price")
        items_tree.heading("total", text="Total")
        
        # Define columns
        items_tree.column("id",  text="Total")
        
        # Define columns
        items_tree.column("id", width=50, anchor=tk.CENTER)
        items_tree.column("item", width=200)
        items_tree.column("description", width=250)
        items_tree.column("quantity", width=80, anchor=tk.CENTER)
        items_tree.column("price", width=100, anchor=tk.E)
        items_tree.column("total", width=100, anchor=tk.E)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, command=items_tree.yview)
        items_tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Load items
        currency = self.get_setting('currency_symbol')
        for item in invoice_items:
            price_formatted = f"{currency}{item['unit_price']:.2f}"
            total_formatted = f"{currency}{item['total_price']:.2f}"
            
            items_tree.insert('', tk.END, values=(
                item['item_id'], item['item_name'], item['description'],
                item['quantity'], price_formatted, total_formatted
            ))
        
        # Totals section
        totals_frame = ttk.Frame(main_frame)
        totals_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Create a frame for the totals on the right
        totals_right = ttk.Frame(totals_frame)
        totals_right.pack(side=tk.RIGHT)
        
        # Subtotal
        ttk.Label(totals_right, text="Subtotal:").grid(row=0, column=0, sticky=tk.E, pady=(0, 5))
        subtotal_formatted = f"{currency}{invoice['subtotal']:.2f}"
        ttk.Label(totals_right, text=subtotal_formatted, width=15, anchor=tk.E).grid(row=0, column=1, sticky=tk.E, pady=(0, 5))
        
        # Tax
        ttk.Label(totals_right, text=f"Tax ({invoice['tax_rate']}%):").grid(row=1, column=0, sticky=tk.E, pady=(0, 5))
        tax_formatted = f"{currency}{invoice['tax_amount']:.2f}"
        ttk.Label(totals_right, text=tax_formatted, width=15, anchor=tk.E).grid(row=1, column=1, sticky=tk.E, pady=(0, 5))
        
        # Discount
        ttk.Label(totals_right, text=f"Discount ({invoice['discount_rate']}%):").grid(row=2, column=0, sticky=tk.E, pady=(0, 5))
        discount_formatted = f"{currency}{invoice['discount_amount']:.2f}"
        ttk.Label(totals_right, text=discount_formatted, width=15, anchor=tk.E).grid(row=2, column=1, sticky=tk.E, pady=(0, 5))
        
        # Total
        ttk.Label(totals_right, text="Total:", font=("Helvetica", 10, "bold")).grid(row=3, column=0, sticky=tk.E, pady=(5, 0))
        total_formatted = f"{currency}{invoice['total_amount']:.2f}"
        ttk.Label(totals_right, text=total_formatted, width=15, anchor=tk.E, font=("Helvetica", 10, "bold")).grid(row=3, column=1, sticky=tk.E, pady=(5, 0))
        
        # Notes section
        if invoice['notes']:
            notes_frame = ttk.LabelFrame(main_frame, text="Notes")
            notes_frame.pack(fill=tk.X, pady=(0, 20))
            
            notes_text = tk.Text(notes_frame, height=3, width=50)
            notes_text.pack(fill=tk.X, padx=10, pady=10)
            notes_text.insert("1.0", invoice['notes'])
            notes_text.configure(state="disabled")
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        print_button = ttk.Button(button_frame, text="Print Invoice", 
                                 command=lambda: self.generate_invoice_pdf(invoice['id'], True))
        print_button.pack(side=tk.LEFT, padx=(0, 10))
        
        email_button = ttk.Button(button_frame, text="Email Invoice", 
                                 command=lambda: self.email_invoice(invoice['id']))
        email_button.pack(side=tk.LEFT, padx=(0, 10))
        
        add_payment_button = ttk.Button(button_frame, text="Add Payment", 
                                       command=lambda: self.show_add_payment_dialog(invoice['id'], dialog))
        add_payment_button.pack(side=tk.LEFT, padx=(0, 10))
        
        close_button = ttk.Button(button_frame, text="Close", 
                                 command=dialog.destroy)
        close_button.pack(side=tk.LEFT)
    
    def setup_invoice_payments_tab(self, parent, invoice, payments, dialog):
        """Set up the invoice payments tab"""
        # Create main frame
        main_frame = ttk.Frame(parent, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Payment summary
        summary_frame = ttk.LabelFrame(main_frame, text="Payment Summary")
        summary_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Get currency symbol
        currency = self.get_setting('currency_symbol')
        
        # Calculate total paid
        total_paid = sum(payment['amount'] for payment in payments)
        balance = invoice['total_amount'] - total_paid
        
        # Left column
        left_col = ttk.Frame(summary_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Invoice total
        ttk.Label(left_col, text="Invoice Total:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        total_formatted = f"{currency}{invoice['total_amount']:.2f}"
        ttk.Label(left_col, text=total_formatted).grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Total paid
        ttk.Label(left_col, text="Total Paid:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        paid_formatted = f"{currency}{total_paid:.2f}"
        ttk.Label(left_col, text=paid_formatted).grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Balance
        ttk.Label(left_col, text="Balance:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        balance_formatted = f"{currency}{balance:.2f}"
        ttk.Label(left_col, text=balance_formatted, 
                 foreground="green" if balance <= 0 else "red").grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        # Right column
        right_col = ttk.Frame(summary_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status
        ttk.Label(right_col, text="Status:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Label(right_col, text=invoice['status']).grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Due date
        ttk.Label(right_col, text="Due Date:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        due_date = datetime.fromisoformat(invoice['due_date']).strftime('%Y-%m-%d')
        ttk.Label(right_col, text=due_date).grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Add payment button
        add_payment_button = ttk.Button(right_col, text="Add Payment", 
                                       command=lambda: self.show_add_payment_dialog(invoice['id'], dialog))
        add_payment_button.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Payments list
        payments_frame = ttk.LabelFrame(main_frame, text="Payment History")
        payments_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create treeview for payments
        columns = ("id", "date", "amount", "method", "reference", "recorded_by")
        payments_tree = ttk.Treeview(payments_frame, columns=columns, show="headings", height=10)
        
        # Define headings
        payments_tree.heading("id", text="ID")
        payments_tree.heading("date", text="Payment Date")
        payments_tree.heading("amount", text="Amount")
        payments_tree.heading("method", text="Payment Method")
        payments_tree.heading("reference", text="Reference")
        payments_tree.heading("recorded_by", text="Recorded By")
        
        # Define columns
        payments_tree.column("id", width=50, anchor=tk.CENTER)
        payments_tree.column("date", width=150, anchor=tk.CENTER)
        payments_tree.column("amount", width=100, anchor=tk.E)
        payments_tree.column("method", width=150)
        payments_tree.column("reference", width=150)
        payments_tree.column("recorded_by", width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(payments_frame, orient=tk.VERTICAL, command=payments_tree.yview)
        payments_tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        payments_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Load payments
        for payment in payments:
            payment_date = datetime.fromisoformat(payment['payment_date']).strftime('%Y-%m-%d %H:%M')
            amount_formatted = f"{currency}{payment['amount']:.2f}"
            
            payments_tree.insert('', tk.END, values=(
                payment['id'], payment_date, amount_formatted,
                payment['payment_method'], payment['reference_number'] or "",
                payment['username']
            ))
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        delete_payment_button = ttk.Button(button_frame, text="Delete Payment", 
                                          style="Danger.TButton",
                                          command=lambda: self.delete_payment(payments_tree, invoice['id'], dialog))
        delete_payment_button.pack(side=tk.LEFT, padx=(0, 10))
        
        close_button = ttk.Button(button_frame, text="Close", 
                                 command=dialog.destroy)
        close_button.pack(side=tk.LEFT)
    
    def update_invoice_status(self, invoice_id, status, dialog):
        """Update the status of an invoice"""
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE invoices SET status = ? WHERE id = ?", (status, invoice_id))
            conn.commit()
            messagebox.showinfo("Success", "Invoice status updated", parent=dialog)
            
            # Refresh invoices list
            self.load_invoices()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to update status: {str(e)}", parent=dialog)
        finally:
            conn.close()
    
    def show_add_payment_dialog(self, invoice_id, parent_dialog):
        """Show dialog to add a payment to an invoice"""
        # Get invoice details
        conn = sqlite3.connect('inventory.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT i.*, c.name as customer_name
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.id = ?
        ''', (invoice_id,))
        
        invoice = cursor.fetchone()
        
        # Calculate total paid so far
        cursor.execute('''
        SELECT SUM(amount) as total_paid
        FROM payments
        WHERE invoice_id = ?
        ''', (invoice_id,))
        
        result = cursor.fetchone()
        total_paid = result['total_paid'] or 0
        
        # Get payment methods
        cursor.execute("SELECT name FROM payment_gateways WHERE is_active = 1")
        payment_methods = [row['name'] for row in cursor.fetchall()]
        
        conn.close()
        
        # Calculate balance
        balance = invoice['total_amount'] - total_paid
        
        # Create a new top-level window
        dialog = tk.Toplevel(parent_dialog)
        dialog.title("Add Payment")
        dialog.geometry("500x400")
        dialog.transient(parent_dialog)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create form frame
        form_frame = ttk.Frame(dialog, padding="20 20 20 20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Invoice info
        info_frame = ttk.LabelFrame(form_frame, text="Invoice Information")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Get currency symbol
        currency = self.get_setting('currency_symbol')
        
        # Left column
        left_col = ttk.Frame(info_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Invoice number
        ttk.Label(left_col, text="Invoice Number:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Label(left_col, text=invoice['invoice_number']).grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Customer
        ttk.Label(left_col, text="Customer:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Label(left_col, text=invoice['customer_name']).grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Right column
        right_col = ttk.Frame(info_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Total amount
        ttk.Label(right_col, text="Total Amount:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        total_formatted = f"{currency}{invoice['total_amount']:.2f}"
        ttk.Label(right_col, text=total_formatted).grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Balance
        ttk.Label(right_col, text="Balance:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        balance_formatted = f"{currency}{balance:.2f}"
        ttk.Label(right_col, text=balance_formatted).grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Payment details
        payment_frame = ttk.LabelFrame(form_frame, text="Payment Details")
        payment_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Payment date
        ttk.Label(payment_frame, text="Payment Date:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=(10, 5))
        
        payment_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        payment_date_entry = ttk.Entry(payment_frame, textvariable=payment_date_var, width=15)
        payment_date_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=(10, 5))
        
        # Amount
        ttk.Label(payment_frame, text="Amount:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        amount_var = tk.StringVar(value=f"{balance:.2f}")
        amount_entry = ttk.Entry(payment_frame, textvariable=amount_var, width=15)
        amount_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Payment method
        ttk.Label(payment_frame, text="Payment Method:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        
        method_var = tk.StringVar()
        method_combo = ttk.Combobox(payment_frame, textvariable=method_var, 
                                   values=payment_methods, state="readonly", width=15)
        if payment_methods:
            method_combo.current(0)
        method_combo.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Reference number
        ttk.Label(payment_frame, text="Reference:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        
        reference_var = tk.StringVar()
        reference_entry = ttk.Entry(payment_frame, textvariable=reference_var, width=20)
        reference_entry.grid(row=3, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Notes
        ttk.Label(payment_frame, text="Notes:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=(5, 10))
        
        notes_entry = ttk.Entry(payment_frame, width=30)
        notes_entry.grid(row=4, column=1, sticky=tk.W, padx=10, pady=(5, 10))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill=tk.X, pady=(0, 0))
        
        save_button = ttk.Button(button_frame, text="Save Payment", 
                                command=lambda: self.save_payment(
                                    invoice_id,
                                    payment_date_var.get(),
                                    amount_var.get(),
                                    method_var.get(),
                                    reference_var.get(),
                                    notes_entry.get(),
                                    balance,
                                    dialog,
                                    parent_dialog
                                ))
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT)
    
    def save_payment(self, invoice_id, payment_date, amount, method, reference, notes, balance, dialog, parent_dialog):
        """Save a payment to the database"""
        # Validate inputs
        try:
            payment_date_obj = datetime.strptime(payment_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error", "Invalid payment date format. Use YYYY-MM-DD", parent=dialog)
            return
        
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be a positive number")
        except ValueError:
            messagebox.showerror("Error", "Amount must be a positive number", parent=dialog)
            return
        
        if not method:
            messagebox.showerror("Error", "Please select a payment method", parent=dialog)
            return
        
        # Check if amount is greater than balance
        if amount > balance:
            confirm = messagebox.askyesno("Confirm", 
                                         "The payment amount is greater than the remaining balance. Continue?", 
                                         parent=dialog)
            if not confirm:
                return
        
        # Insert into database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            # Insert payment
            cursor.execute('''
            INSERT INTO payments (
                invoice_id, payment_date, amount, payment_method, 
                reference_number, notes, recorded_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                invoice_id, payment_date_obj.isoformat(), amount, method,
                reference, notes, self.current_user["id"]
            ))
            
            # Update invoice status
            # Calculate total paid
            cursor.execute("SELECT SUM(amount) FROM payments WHERE invoice_id = ?", (invoice_id,))
            total_paid = cursor.fetchone()[0] or 0
            
            # Get invoice total
            cursor.execute("SELECT total_amount FROM invoices WHERE id = ?", (invoice_id,))
            total_amount = cursor.fetchone()[0]
            
            # Determine new status
            if total_paid >= total_amount:
                new_status = "Paid"
            elif total_paid > 0:
                new_status = "Partial"
            else:
                new_status = "Unpaid"
            
            cursor.execute("UPDATE invoices SET status = ? WHERE id = ?", (new_status, invoice_id))
            
            conn.commit()
            messagebox.showinfo("Success", "Payment recorded successfully", parent=dialog)
            
            # Close dialog
            dialog.destroy()
            
            # Refresh parent dialog
            parent_dialog.destroy()
            self.show_view_invoice_dialog()
            
            # Refresh invoices list
            self.load_invoices()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to record payment: {str(e)}", parent=dialog)
        finally:
            conn.close()
    
    def delete_payment(self, payments_tree, invoice_id, parent_dialog):
        """Delete a selected payment"""
        # Get selected payment
        selected = payments_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a payment to delete", parent=parent_dialog)
            return
        
        # Get payment ID
        payment_id = payments_tree.item(selected[0], 'values')[0]
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Delete", 
                                     "Are you sure you want to delete this payment?\n\nThis action cannot be undone.", 
                                     parent=parent_dialog)
        if not confirm:
            return
        
        # Delete from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            # Delete payment
            cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
            
            # Update invoice status
            # Calculate total paid
            cursor.execute("SELECT SUM(amount) FROM payments WHERE invoice_id = ?", (invoice_id,))
            total_paid = cursor.fetchone()[0] or 0
            
            # Get invoice total
            cursor.execute("SELECT total_amount FROM invoices WHERE id = ?", (invoice_id,))
            total_amount = cursor.fetchone()[0]
            
            # Determine new status
            if total_paid >= total_amount:
                new_status = "Paid"
            elif total_paid > 0:
                new_status = "Partial"
            else:
                new_status = "Unpaid"
            
            cursor.execute("UPDATE invoices SET status = ? WHERE id = ?", (new_status, invoice_id))
            
            conn.commit()
            messagebox.showinfo("Success", "Payment deleted successfully", parent=parent_dialog)
            
            # Refresh parent dialog
            parent_dialog.destroy()
            self.show_view_invoice_dialog()
            
            # Refresh invoices list
            self.load_invoices()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to delete payment: {str(e)}", parent=parent_dialog)
        finally:
            conn.close()
    
    def delete_invoice(self):
        """Delete an invoice"""
        # Get selected invoice
        selected = self.invoices_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select an invoice to delete")
            return
        
        # Get invoice ID and number
        invoice_values = self.invoices_tree.item(selected[0], 'values')
        invoice_id = invoice_values[0]
        invoice_number = invoice_values[1]
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Delete", 
                                     f"Are you sure you want to delete Invoice #{invoice_number}?\n\nThis action cannot be undone.")
        if not confirm:
            return
        
        # Delete from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Get invoice items to restore inventory
            cursor.execute('''
            SELECT item_id, quantity FROM invoice_items WHERE invoice_id = ?
            ''', (invoice_id,))
            
            items = cursor.fetchall()
            
            # Restore inventory quantities
            for item_id, quantity in items:
                cursor.execute('''
                UPDATE inventory
                SET quantity = quantity + ?
                WHERE id = ?
                ''', (quantity, item_id))
                
                # Add transaction record for the restoration
                cursor.execute('''
                INSERT INTO transactions (
                    item_id, transaction_type, quantity, user_id, notes
                ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    item_id, 'in', quantity, self.current_user["id"], 
                    f"Restored from deleted Invoice #{invoice_number}"
                ))
            
            # Delete payments
            cursor.execute("DELETE FROM payments WHERE invoice_id = ?", (invoice_id,))
            
            # Delete invoice items
            cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            
            # Delete invoice
            cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            
            # Commit transaction
            cursor.execute("COMMIT")
            
            messagebox.showinfo("Success", f"Invoice #{invoice_number} deleted successfully")
            
            # Refresh invoices list
            self.load_invoices()
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            messagebox.showerror("Error", f"Failed to delete invoice: {str(e)}")
        finally:
            conn.close()
    
    def generate_invoice_number(self):
        """Generate the next invoice number"""
        # Get settings
        prefix = self.get_setting('invoice_prefix')
        starting_number = int(self.get_setting('invoice_starting_number'))
        
        # Get the highest invoice number from the database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT invoice_number FROM invoices ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Extract the numeric part of the last invoice number
            last_number = result[0]
            if prefix and last_number.startswith(prefix):
                last_number = last_number[len(prefix):]
            
            try:
                # Increment the number
                next_number = int(last_number) + 1
            except ValueError:
                # If conversion fails, use the starting number
                next_number = starting_number
        else:
            # No invoices yet, use the starting number
            next_number = starting_number
        
        # Format the new invoice number
        return f"{prefix}{next_number}"
    
    def generate_invoice_pdf(self, invoice_id, open_pdf=False):
        """Generate a PDF for an invoice"""
        # Get invoice data
        conn = sqlite3.connect('inventory.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT i.*, c.*,
               c.name as customer_name, c.address as customer_address,
               c.email as customer_email, c.phone as customer_phone
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.id = ?
        ''', (invoice_id,))
        
        invoice = cursor.fetchone()
        
        if not invoice:
            conn.close()
            messagebox.showerror("Error", "Invoice not found")
            return
        
        # Get invoice items
        cursor.execute('''
        SELECT ii.*, inv.item_name
        FROM invoice_items ii
        JOIN inventory inv ON ii.item_id = inv.id
        WHERE ii.invoice_id = ?
        ''', (invoice_id,))
        
        invoice_items = cursor.fetchall()
        
        # Get payments
        cursor.execute('''
        SELECT SUM(amount) as total_paid
        FROM payments
        WHERE invoice_id = ?
        ''', (invoice_id,))
        
        payment_result = cursor.fetchone()
        total_paid = payment_result['total_paid'] or 0
        
        # Get company info from settings
        company_name = self.get_setting('company_name')
        company_address = self.get_setting('company_address')
        company_phone = self.get_setting('company_phone')
        company_email = self.get_setting('company_email')
        company_website = self.get_setting('company_website')
        company_tax_id = self.get_setting('company_tax_id')
        
        # Get currency symbol
        currency = self.get_setting('currency_symbol')
        
        conn.close()
        
        # Create PDF filename
        invoice_number = invoice['invoice_number']
        customer_name = invoice['customer_name'].replace(' ', '_')
        filename = f"Invoice_{invoice_number}_{customer_name}.pdf"
        
        # Ask user where to save the file
        file_path = tk.filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=filename
        )
        
        if not file_path:
            return
        
        # Create PDF
        doc = SimpleDocTemplate(
            file_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Center', alignment=1))
        styles.add(ParagraphStyle(name='Right', alignment=2))
        
        # Create content
        content = []
        
        # Add company logo and header
        header_data = [
            [Paragraph(f"<b>{company_name}</b>", styles['Heading1']), 
             Paragraph(f"<b>INVOICE</b>", styles['Heading1'])]
        ]
        header_table = Table(header_data, colWidths=[300, 150])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        content.append(header_table)
        content.append(Spacer(1, 20))
        
        # Company and customer info
        company_info = f"""
        <b>{company_name}</b><br/>
        {company_address}<br/>
        Phone: {company_phone}<br/>
        Email: {company_email}<br/>
        Website: {company_website}<br/>
        Tax ID: {company_tax_id}
        """
        
        customer_info = f"""
        <b>Bill To:</b><br/>
        {invoice['customer_name']}<br/>
        {invoice['customer_address'] or ''}<br/>
        Phone: {invoice['customer_phone'] or ''}<br/>
        Email: {invoice['customer_email'] or ''}<br/>
        {f"Tax ID: {invoice['tax_id']}" if invoice['tax_id'] else ''}
        """
        
        invoice_info = f"""
        <b>Invoice Number:</b> {invoice['invoice_number']}<br/>
        <b>Invoice Date:</b> {datetime.fromisoformat(invoice['invoice_date']).strftime('%Y-%m-%d')}<br/>
        <b>Due Date:</b> {datetime.fromisoformat(invoice['due_date']).strftime('%Y-%m-%d')}<br/>
        <b>Status:</b> {invoice['status']}
        """
        
        info_data = [
            [Paragraph(company_info, styles['Normal']), 
             Paragraph(customer_info, styles['Normal']),
             Paragraph(invoice_info, styles['Normal'])]
        ]
        info_table = Table(info_data, colWidths=[150, 150, 150])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        content.append(info_table)
        content.append(Spacer(1, 20))
        
        # Invoice items
        items_data = [
            ['Item', 'Description', 'Quantity', 'Unit Price', 'Total']
        ]
        
        for item in invoice_items:
            items_data.append([
                item['item_name'],
                item['description'] or '',
                str(item['quantity']),
                f"{currency}{item['unit_price']:.2f}",
                f"{currency}{item['total_price']:.2f}"
            ])
        
        # Add totals
        items_data.append(['', '', '', 'Subtotal:', f"{currency}{invoice['subtotal']:.2f}"])
        items_data.append(['', '', '', f"Tax ({invoice['tax_rate']}%):", f"{currency}{invoice['tax_amount']:.2f}"])
        items_data.append(['', '', '', f"Discount ({invoice['discount_rate']}%):", f"{currency}{invoice['discount_amount']:.2f}"])
        items_data.append(['', '', '', 'Total:', f"{currency}{invoice['total_amount']:.2f}"])
        items_data.append(['', '', '', 'Amount Paid:', f"{currency}{total_paid:.2f}"])
        items_data.append(['', '', '', 'Balance Due:', f"{currency}{(invoice['total_amount'] - total_paid):.2f}"])
        
        # Create table
        items_table = Table(items_data, colWidths=[100, 150, 70, 80, 80])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -len(items_data)), 1, colors.black),
            ('SPAN', (0, -6), (2, -6)),
            ('SPAN', (0, -5), (2, -5)),
            ('SPAN', (0, -4), (2, -4)),
            ('SPAN', (0, -3), (2, -3)),
            ('SPAN', (0, -2), (2, -2)),
            ('SPAN', (0, -1), (2, -1)),
            ('FONTNAME', (3, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEBELOW', (3, -2), (-1, -2), 1, colors.black),
        ]))
        content.append(items_table)
        
        # Add notes if present
        if invoice['notes']:
            content.append(Spacer(1, 20))
            content.append(Paragraph("<b>Notes:</b>", styles['Normal']))
            content.append(Paragraph(invoice['notes'], styles['Normal']))
        
        # Add footer
        content.append(Spacer(1, 40))
        content.append(Paragraph("Thank you for your business!", styles['Center']))
        
        # Build PDF
        doc.build(content)
        
        # Open PDF if requested
        if open_pdf:
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(file_path)
                elif os.name == 'posix':  # macOS or Linux
                    if os.uname().sysname == 'Darwin':  # macOS
                        os.system(f'open "{file_path}"')
                    else:  # Linux
                        os.system(f'xdg-open "{file_path}"')
            except Exception as e:
                messagebox.showinfo("Info", f"PDF saved to {file_path}")
        else:
            messagebox.showinfo("Success", f"Invoice PDF saved to {file_path}")
    
    def email_invoice(self, invoice_id):
        """Email an invoice to a customer"""
        # Check if SMTP settings are configured
        smtp_server = self.get_setting('smtp_server')
        smtp_port = self.get_setting('smtp_port')
        smtp_username = self.get_setting('smtp_username')
        smtp_password = self.get_setting('smtp_password')
        
        if not smtp_server or not smtp_username or not smtp_password:
            messagebox.showinfo("SMTP Not Configured", 
                              "Please configure SMTP settings in the Billing Settings tab.")
            return
        
        # Get invoice and customer data
        conn = sqlite3.connect('inventory.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT i.*, c.name as customer_name, c.email as customer_email
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.id = ?
        ''', (invoice_id,))
        
        invoice = cursor.fetchone()
        conn.close()
        
        if not invoice:
            messagebox.showerror("Error", "Invoice not found")
            return
        
        if not invoice['customer_email']:
            messagebox.showerror("Error", "Customer email address not found")
            return
        
        # Generate PDF
        # Create temporary filename
        invoice_number = invoice['invoice_number']
        customer_name = invoice['customer_name'].replace(' ', '_')
        filename = f"Invoice_{invoice_number}_{customer_name}.pdf"
        temp_path = os.path.join(os.path.expanduser("~"), filename)
        
        # Generate PDF to temp location
        self.generate_invoice_pdf_to_file(invoice_id, temp_path)
        
        # Show email dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("Send Invoice Email")
        dialog.geometry("500x500")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create form frame
        form_frame = ttk.Frame(dialog, padding="20 20 20 20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Email fields
        ttk.Label(form_frame, text="From:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        from_var = tk.StringVar(value=smtp_username)
        from_entry = ttk.Entry(form_frame, textvariable=from_var, width=40)
        from_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="To:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        to_var = tk.StringVar(value=invoice['customer_email'])
        to_entry = ttk.Entry(form_frame, textvariable=to_var, width=40)
        to_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Subject:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        subject_var = tk.StringVar(value=f"Invoice #{invoice['invoice_number']} from {self.get_setting('company_name')}")
        subject_entry = ttk.Entry(form_frame, textvariable=subject_var, width=40)
        subject_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Message:").grid(row=3, column=0, sticky=tk.NW, pady=(0, 10))
        
        # Default message
        default_message = f"""Dear {invoice['customer_name']},

Please find attached your invoice #{invoice['invoice_number']} for the amount of {self.get_setting('currency_symbol')}{invoice['total_amount']:.2f}.

Due date: {datetime.fromisoformat(invoice['due_date']).strftime('%Y-%m-%d')}

If you have any questions, please don't hesitate to contact us.

Thank you for your business!

{self.get_setting('company_name')}
{self.get_setting('company_phone')}
{self.get_setting('company_email')}
"""
        
        message_text = tk.Text(form_frame, height=15, width=40)
        message_text.grid(row=3, column=1, sticky=tk.W, pady=(0, 10))
        message_text.insert("1.0", default_message)
        
        # Attachment info
        attachment_frame = ttk.Frame(form_frame)
        attachment_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(attachment_frame, text="Attachment:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(attachment_frame, text=filename).pack(side=tk.LEFT)
        
        # Status label
        status_var = tk.StringVar()
        status_label = ttk.Label(form_frame, textvariable=status_var, foreground="blue")
        status_label.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(10, 0))
        
        send_button = ttk.Button(button_frame, text="Send Email", 
                                command=lambda: self.send_invoice_email(
                                    from_var.get(),
                                    to_var.get(),
                                    subject_var.get(),
                                    message_text.get("1.0", tk.END),
                                    temp_path,
                                    filename,
                                    status_var,
                                    dialog
                                ))
        send_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=lambda: self.cancel_email(dialog, temp_path))
        cancel_button.pack(side=tk.LEFT)
    
    def generate_invoice_pdf_to_file(self, invoice_id, file_path):
        """Generate a PDF for an invoice to a specific file path"""
        # Get invoice data
        conn = sqlite3.connect('inventory.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT i.*, c.*,
               c.name as customer_name, c.address as customer_address,
               c.email as customer_email, c.phone as customer_phone
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.id = ?
        ''', (invoice_id,))
        
        invoice = cursor.fetchone()
        
        # Get invoice items
        cursor.execute('''
        SELECT ii.*, inv.item_name
        FROM invoice_items ii
        JOIN inventory inv ON ii.item_id = inv.id
        WHERE ii.invoice_id = ?
        ''', (invoice_id,))
        
        invoice_items = cursor.fetchall()
        
        # Get payments
        cursor.execute('''
        SELECT SUM(amount) as total_paid
        FROM payments
        WHERE invoice_id = ?
        ''', (invoice_id,))
        
        payment_result = cursor.fetchone()
        total_paid = payment_result['total_paid'] or 0
        
        # Get company info from settings
        company_name = self.get_setting('company_name')
        company_address = self.get_setting('company_address')
        company_phone = self.get_setting('company_phone')
        company_email = self.get_setting('company_email')
        company_website = self.get_setting('company_website')
        company_tax_id = self.get_setting('company_tax_id')
        
        # Get currency symbol
        currency = self.get_setting('currency_symbol')
        
        conn.close()
        
        # Create PDF
        doc = SimpleDocTemplate(
            file_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Center', alignment=1))
        styles.add(ParagraphStyle(name='Right', alignment=2))
        
        # Create content
        content = []
        
        # Add company logo and header
        header_data = [
            [Paragraph(f"<b>{company_name}</b>", styles['Heading1']), 
             Paragraph(f"<b>INVOICE</b>", styles['Heading1'])]
        ]
        header_table = Table(header_data, colWidths=[300, 150])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        content.append(header_table)
        content.append(Spacer(1, 20))
        
        # Company and customer info
        company_info = f"""
        <b>{company_name}</b><br/>
        {company_address}<br/>
        Phone: {company_phone}<br/>
        Email: {company_email}<br/>
        Website: {company_website}<br/>
        Tax ID: {company_tax_id}
        """
        
        customer_info = f"""
        <b>Bill To:</b><br/>
        {invoice['customer_name']}<br/>
        {invoice['customer_address'] or ''}<br/>
        Phone: {invoice['customer_phone'] or ''}<br/>
        Email: {invoice['customer_email'] or ''}<br/>
        {f"Tax ID: {invoice['tax_id']}" if invoice['tax_id'] else ''}
        """
        
        invoice_info = f"""
        <b>Invoice Number:</b> {invoice['invoice_number']}<br/>
        <b>Invoice Date:</b> {datetime.fromisoformat(invoice['invoice_date']).strftime('%Y-%m-%d')}<br/>
        <b>Due Date:</b> {datetime.fromisoformat(invoice['due_date']).strftime('%Y-%m-%d')}<br/>
        <b>Status:</b> {invoice['status']}
        """
        
        info_data = [
            [Paragraph(company_info, styles['Normal']), 
             Paragraph(customer_info, styles['Normal']),
             Paragraph(invoice_info, styles['Normal'])]
        ]
        info_table = Table(info_data, colWidths=[150, 150, 150])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        content.append(info_table)
        content.append(Spacer(1, 20))
        
        # Invoice items
        items_data = [
            ['Item', 'Description', 'Quantity', 'Unit Price', 'Total']
        ]
        
        for item in invoice_items:
            items_data.append([
                item['item_name'],
                item['description'] or '',
                str(item['quantity']),
                f"{currency}{item['unit_price']:.2f}",
                f"{currency}{item['total_price']:.2f}"
            ])
        
        # Add totals
        items_data.append(['', '', '', 'Subtotal:', f"{currency}{invoice['subtotal']:.2f}"])
        items_data.append(['', '', '', f"Tax ({invoice['tax_rate']}%):", f"{currency}{invoice['tax_amount']:.2f}"])
        items_data.append(['', '', '', f"Discount ({invoice['discount_rate']}%):", f"{currency}{invoice['discount_amount']:.2f}"])
        items_data.append(['', '', '', 'Total:', f"{currency}{invoice['total_amount']:.2f}"])
        items_data.append(['', '', '', 'Amount Paid:', f"{currency}{total_paid:.2f}"])
        items_data.append(['', '', '', 'Balance Due:', f"{currency}{(invoice['total_amount'] - total_paid):.2f}"])
        
        # Create table
        items_table = Table(items_data, colWidths=[100, 150, 70, 80, 80])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -len(items_data)), 1, colors.black),
            ('SPAN', (0, -6), (2, -6)),
            ('SPAN', (0, -5), (2, -5)),
            ('SPAN', (0, -4), (2, -4)),
            ('SPAN', (0, -3), (2, -3)),
            ('SPAN', (0, -2), (2, -2)),
            ('SPAN', (0, -1), (2, -1)),
            ('FONTNAME', (3, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEBELOW', (3, -2), (-1, -2), 1, colors.black),
        ]))
        content.append(items_table)
        
        # Add notes if present
        if invoice['notes']:
            content.append(Spacer(1, 20))
            content.append(Paragraph("<b>Notes:</b>", styles['Normal']))
            content.append(Paragraph(invoice['notes'], styles['Normal']))
        
        # Add footer
        content.append(Spacer(1, 40))
        content.append(Paragraph("Thank you for your business!", styles['Center']))
        
        # Build PDF
        doc.build(content)
    
    def send_invoice_email(self, from_email, to_email, subject, message, attachment_path, attachment_name, status_var, dialog):
        """Send an invoice email with attachment"""
        # Validate inputs
        if not to_email:
            messagebox.showerror("Error", "Recipient email is required", parent=dialog)
            return
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", to_email):
            messagebox.showerror("Error", "Invalid recipient email format", parent=dialog)
            return
        
        # Get SMTP settings
        smtp_server = self.get_setting('smtp_server')
        smtp_port = int(self.get_setting('smtp_port'))
        smtp_username = self.get_setting('smtp_username')
        smtp_password = self.get_setting('smtp_password')
        
        # Update status
        status_var.set("Preparing to send email...")
        
        # Create a function to send the email in a separate thread
        def send_email_thread():
            try:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = from_email
                msg['To'] = to_email
                msg['Subject'] = subject
                
                # Attach message body
                msg.attach(MIMEText(message, 'plain'))
                
                # Attach invoice PDF
                with open(attachment_path, "rb") as attachment:
                    part = MIMEApplication(attachment.read(), Name=attachment_name)
                
                part['Content-Disposition'] = f'attachment; filename="{attachment_name}"'
                msg.attach(part)
                
                # Connect to SMTP server
                status_var.set("Connecting to SMTP server...")
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                
                # Login
                status_var.set("Logging in...")
                server.login(smtp_username, smtp_password)
                
                # Send email
                status_var.set("Sending email...")
                server.send_message(msg)
                server.quit()
                
                # Update status and show success message
                status_var.set("Email sent successfully!")
                
                # Delete temporary file
                try:
                    os.remove(attachment_path)
                except:
                    pass
                
                # Show success message and close dialog after a delay
                time.sleep(2)
                dialog.after(0, lambda: messagebox.showinfo("Success", "Email sent successfully!", parent=dialog))
                dialog.after(100, dialog.destroy)
                
            except Exception as e:
                # Update status and show error message
                error_msg = str(e)
                status_var.set(f"Error: {error_msg}")
                dialog.after(0, lambda: messagebox.showerror("Error", f"Failed to send email: {error_msg}", parent=dialog))
        
        # Start the email sending in a separate thread
        email_thread = threading.Thread(target=send_email_thread)
        email_thread.daemon = True
        email_thread.start()
    
    def cancel_email(self, dialog, temp_path):
        """Cancel email and clean up temporary files"""
        try:
            os.remove(temp_path)
        except:
            pass
        dialog.destroy()
    
    def setup_customers_tab(self):
        """Set up the customers tab with customer listing and management"""
        # Create frame for customers content
        customers_content = ttk.Frame(self.customers_tab, style="TFrame")
        customers_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Search bar
        search_frame = ttk.Frame(customers_content, style="TFrame")
        search_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Search
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        customer_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=customer_search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # Search button
        search_button = ttk.Button(search_frame, text="Search", 
                                  command=lambda: self.search_customers(customer_search_var.get()))
        search_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Reset button
        reset_button = ttk.Button(search_frame, text="Reset", 
                                 command=lambda: self.reset_customer_search(customer_search_var))
        reset_button.pack(side=tk.LEFT)
        
        # Action buttons
        action_frame = ttk.Frame(customers_content, style="TFrame")
        action_frame.pack(fill=tk.X, pady=(0, 20))
        
        add_button = ttk.Button(action_frame, text="Add Customer", 
                               command=self.show_add_customer_dialog)
        add_button.pack(side=tk.LEFT, padx=(0, 10))
        
        edit_button = ttk.Button(action_frame, text="Edit Customer", 
                                command=self.show_edit_customer_dialog)
        edit_button.pack(side=tk.LEFT, padx=(0, 10))
        
        view_button = ttk.Button(action_frame, text="View Customer", 
                                command=self.show_view_customer_dialog)
        view_button.pack(side=tk.LEFT, padx=(0, 10))
        
        delete_button = ttk.Button(action_frame, text="Delete Customer", 
                                  style="Danger.TButton", command=self.delete_customer)
        delete_button.pack(side=tk.LEFT)
        
        # Customers table
        table_frame = ttk.Frame(customers_content, style="TFrame")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview
        columns = ("id", "name", "email", "phone", "address", "tax_id", "created_at")
        self.customers_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Define headings
        self.customers_tree.heading("id", text="ID")
        self.customers_tree.heading("name", text="Name")
        self.customers_tree.heading("email", text="Email")
        self.customers_tree.heading("phone", text="Phone")
        self.customers_tree.heading("address", text="Address")
        self.customers_tree.heading("tax_id", text="Tax ID")
        self.customers_tree.heading("created_at", text="Created At")
        
        # Define columns
        self.customers_tree.column("id", width=50, anchor=tk.CENTER)
        self.customers_tree.column("name", width=200)
        self.customers_tree.column("email", width=200)
        self.customers_tree.column("phone", width=150)
        self.customers_tree.column("address", width=250)
        self.customers_tree.column("tax_id", width=100)
        self.customers_tree.column("created_at", width=150, anchor=tk.CENTER)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.customers_tree.yview)
        self.customers_tree.configure(yscroll=y_scrollbar.set)
        
        x_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.customers_tree.xview)
        self.customers_tree.configure(xscroll=x_scrollbar.set)
        
        # Pack widgets
        self.customers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind double-click to view
        self.customers_tree.bind("<Double-1>", lambda event: self.show_view_customer_dialog())
        
        # Load customers
        self.load_customers()
        
        # Bind search entry to update on keypress
        customer_search_var.trace("w", lambda name, index, mode: self.search_customers(customer_search_var.get()))
    
    def load_customers(self):
        """Load all customers into the treeview"""
        # Clear existing items
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, name, email, phone, address, tax_id, created_at
        FROM customers
        ORDER BY name
        ''')
        
        customers = cursor.fetchall()
        conn.close()
        
        # Insert into treeview
        for customer in customers:
            cust_id, name, email, phone, address, tax_id, created_at = customer
            
            # Format date
            try:
                date_formatted = datetime.fromisoformat(created_at).strftime('%Y-%m-%d')
            except:
                date_formatted = created_at
            
            self.customers_tree.insert('', tk.END, values=(
                cust_id, name, email or "", phone or "", address or "", tax_id or "", date_formatted
            ))
    
    def search_customers(self, search_term):
        """Search customers by name, email, or phone"""
        # Clear existing items
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        
        # If search term is empty, load all customers
        if not search_term:
            self.load_customers()
            return
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, name, email, phone, address, tax_id, created_at
        FROM customers
        WHERE LOWER(name) LIKE ? OR LOWER(email) LIKE ? OR LOWER(phone) LIKE ?
        ORDER BY name
        ''', (f'%{search_term.lower()}%', f'%{search_term.lower()}%', f'%{search_term.lower()}%'))
        
        customers = cursor.fetchall()
        conn.close()
        
        # Insert into treeview
        for customer in customers:
            cust_id, name, email, phone, address, tax_id, created_at = customer
            
            # Format date
            try:
                date_formatted = datetime.fromisoformat(created_at).strftime('%Y-%m-%d')
            except:
                date_formatted = created_at
            
            self.customers_tree.insert('', tk.END, values=(
                cust_id, name, email or "", phone or "", address or "", tax_id or "", date_formatted
            ))
    
    def reset_customer_search(self, search_var):
        """Reset customer search field and reload all customers"""
        search_var.set("")
        self.load_customers()
    
    def show_add_customer_dialog(self, parent=None):
        """Show dialog to add a new customer"""
        # Create a new top-level window
        if parent is None:
            parent = self.parent
            
        dialog = tk.Toplevel(parent)
        dialog.title("Add New Customer")
        dialog.geometry("500x400")
        dialog.transient(parent)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create form frame
        form_frame = ttk.Frame(dialog, padding="20 20 20 20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        name_entry = ttk.Entry(form_frame, width=40)
        name_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        email_entry = ttk.Entry(form_frame, width=40)
        email_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Phone:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        phone_entry = ttk.Entry(form_frame, width=40)
        phone_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Address:").grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        address_entry = ttk.Entry(form_frame, width=40)
        address_entry.grid(row=3, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Tax ID:").grid(row=4, column=0, sticky=tk.W, pady=(0, 10))
        tax_id_entry = ttk.Entry(form_frame, width=40)
        tax_id_entry.grid(row=4, column=1, sticky=tk.W, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))
        
        save_button = ttk.Button(button_frame, text="Save", 
                                command=lambda: self.save_customer(
                                    name_entry.get(),
                                    email_entry.get(),
                                    phone_entry.get(),
                                    address_entry.get(),
                                    tax_id_entry.get(),
                                    dialog
                                ))
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT)
        
        # Set focus to first field
        name_entry.focus_set()
    
    def save_customer(self, name, email, phone, address, tax_id, dialog):
        """Save a new customer to the database"""
        # Validate inputs
        if not name:
            messagebox.showerror("Error", "Customer name is required", parent=dialog)
            return
        
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Error", "Invalid email format", parent=dialog)
            return
        
        # Insert into database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO customers (name, email, phone, address, tax_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, email, phone, address, tax_id, self.current_user["id"]))
            
            conn.commit()
            messagebox.showinfo("Success", "Customer added successfully", parent=dialog)
            
            # Close dialog and refresh customers
            dialog.destroy()
            self.load_customers()
            
            # If this was called from the invoice creation dialog, refresh the customer dropdown
            if dialog.master != self.parent:
                # Find the customer combo box in the parent dialog
                for widget in dialog.master.winfo_children():
                    if isinstance(widget, ttk.Frame):
                        for child in widget.winfo_children():
                            if isinstance(child, ttk.LabelFrame):
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, ttk.Frame):
                                        for great_grandchild in grandchild.winfo_children():
                                            if isinstance(great_grandchild, ttk.Combobox):
                                                # Refresh the customer list
                                                cursor.execute("SELECT id, name FROM customers ORDER BY name")
                                                customers = [(row[0], row[1]) for row in cursor.fetchall()]
                                                great_grandchild['values'] = [customer[1] for customer in customers]
                                                # Select the new customer
                                                great_grandchild.set(name)
                                                break
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to add customer: {str(e)}", parent=dialog)
        
        finally:
            conn.close()
    
    def show_edit_customer_dialog(self):
        """Show dialog to edit an existing customer"""
        # Get selected customer
        selected = self.customers_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a customer to edit")
            return
        
        # Get customer ID
        customer_id = self.customers_tree.item(selected[0], 'values')[0]
        
        # Get customer data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT name, email, phone, address, tax_id
        FROM customers
        WHERE id = ?
        ''', (customer_id,))
        
        customer = cursor.fetchone()
        conn.close()
        
        if not customer:
            messagebox.showerror("Error", "Customer not found")
            return
        
        name, email, phone, address, tax_id = customer
        
        # Create a new top-level window
        dialog = tk.Toplevel(self.parent)
        dialog.title("Edit Customer")
        dialog.geometry("500x400")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create form frame
        form_frame = ttk.Frame(dialog, padding="20 20 20 20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        name_entry = ttk.Entry(form_frame, width=40)
        name_entry.insert(0, name)
        name_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        email_entry = ttk.Entry(form_frame, width=40)
        email_entry.insert(0, email if email else "")
        email_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Phone:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        phone_entry = ttk.Entry(form_frame, width=40)
        phone_entry.insert(0, phone if phone else "")
        phone_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Address:").grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        address_entry = ttk.Entry(form_frame, width=40)
        address_entry.insert(0, address if address else "")
        address_entry.grid(row=3, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Tax ID:").grid(row=4, column=0, sticky=tk.W, pady=(0, 10))
        tax_id_entry = ttk.Entry(form_frame, width=40)
        tax_id_entry.insert(0, tax_id if tax_id else "")
        tax_id_entry.grid(row=4, column=1, sticky=tk.W, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))
        
        save_button = ttk.Button(button_frame, text="Save", 
                                command=lambda: self.update_customer(
                                    customer_id,
                                    name_entry.get(),
                                    email_entry.get(),
                                    phone_entry.get(),
                                    address_entry.get(),
                                    tax_id_entry.get(),
                                    dialog
                                ))
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT)
    
    def update_customer(self, customer_id, name, email, phone, address, tax_id, dialog):
        """Update an existing customer in the database"""
        # Validate inputs
        if not name:
            messagebox.showerror("Error", "Customer name is required", parent=dialog)
            return
        
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Error", "Invalid email format", parent=dialog)
            return
        
        # Update in database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE customers
            SET name = ?, email = ?, phone = ?, address = ?, tax_id = ?
            WHERE id = ?
            ''', (name, email, phone, address, tax_id, customer_id))
            
            conn.commit()
            messagebox.showinfo("Success", "Customer updated successfully", parent=dialog)
            
            # Close dialog and refresh customers
            dialog.destroy()
            self.load_customers()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to update customer: {str(e)}", parent=dialog)
        
        finally:
            conn.close()
    
    def show_view_customer_dialog(self):
        """Show dialog to view customer details and invoices"""
        # Get selected customer
        selected = self.customers_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a customer to view")
            return
        
        # Get customer ID
        customer_id = self.customers_tree.item(selected[0], 'values')[0]
        
        # Get customer data from database
        conn = sqlite3.connect('inventory.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT c.*, u.username as created_by_name
        FROM customers c
        LEFT JOIN users u ON c.created_by = u.id
        WHERE c.id = ?
        ''', (customer_id,))
        
        customer = cursor.fetchone()
        
        if not customer:
            conn.close()
            messagebox.showerror("Error", "Customer not found")
            return
        
        # Get customer invoices
        cursor.execute('''
        SELECT id, invoice_number, invoice_date, due_date, total_amount, status
        FROM invoices
        WHERE customer_id = ?
        ORDER BY invoice_date DESC
        ''', (customer_id,))
        
        invoices = cursor.fetchall()
        
        # Get total sales and outstanding balance
        cursor.execute('''
        SELECT SUM(total_amount) as total_sales
        FROM invoices
        WHERE customer_id = ?
        ''', (customer_id,))
        
        sales_result = cursor.fetchone()
        total_sales = sales_result['total_sales'] or 0
        
        cursor.execute('''
        SELECT SUM(total_amount) as total_outstanding
        FROM invoices
        WHERE customer_id = ? AND status IN ('Unpaid', 'Partial', 'Overdue')
        ''', (customer_id,))
        
        outstanding_result = cursor.fetchone()
        total_outstanding = outstanding_result['total_outstanding'] or 0
        
        conn.close()
        
        # Create a new top-level window
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Customer: {customer['name']}")
        dialog.geometry("800x600")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create main frame
        main_frame = ttk.Frame(dialog, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Customer details section
        details_frame = ttk.LabelFrame(main_frame, text="Customer Details")
        details_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Left column
        left_col = ttk.Frame(details_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Name
        ttk.Label(left_col, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Label(left_col, text=customer['name']).grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Email
        ttk.Label(left_col, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Label(left_col, text=customer['email'] or "").grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Phone
        ttk.Label(left_col, text="Phone:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Label(left_col, text=customer['phone'] or "").grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        # Right column
        right_col = ttk.Frame(details_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Address
        ttk.Label(right_col, text="Address:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Label(right_col, text=customer['address'] or "").grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Tax ID
        ttk.Label(right_col, text="Tax ID:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Label(right_col, text=customer['tax_id'] or "").grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Created info
        created_at = datetime.fromisoformat(customer['created_at']).strftime('%Y-%m-%d')
        created_by = customer['created_by_name'] or "Unknown"
        ttk.Label(right_col, text="Created:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Label(right_col, text=f"{created_at} by {created_by}").grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        # Summary section
        summary_frame = ttk.LabelFrame(main_frame, text="Summary")
        summary_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Get currency symbol
        currency = self.get_setting('currency_symbol')
        
        # Left column
        summary_left = ttk.Frame(summary_frame)
        summary_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Total sales
        ttk.Label(summary_left, text="Total Sales:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Label(summary_left, text=f"{currency}{total_sales:.2f}").grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Outstanding balance
        ttk.Label(summary_left, text="Outstanding Balance:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Label(summary_left, text=f"{currency}{total_outstanding:.2f}",
                 foreground="red" if total_outstanding > 0 else "black").grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Right column
        summary_right = ttk.Frame(summary_frame)
        summary_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Total invoices
        ttk.Label(summary_right, text="Total Invoices:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Label(summary_right, text=str(len(invoices))).grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Create invoice button
        create_invoice_button = ttk.Button(summary_right, text="Create New Invoice", 
                                          command=lambda: self.create_invoice_for_customer(customer['id'], dialog))
        create_invoice_button.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Invoices section
        invoices_frame = ttk.LabelFrame(main_frame, text="Invoices")
        invoices_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create treeview for invoices
        columns = ("id", "invoice_number", "date", "due_date", "total", "status")
        invoices_tree = ttk.Treeview(invoices_frame, columns=columns, show="headings")
        
        # Define headings
        invoices_tree.heading("id", text="ID")
        invoices_tree.heading("invoice_number", text="Invoice #")
        invoices_tree.heading("date", text="Invoice Date")
        invoices_tree.heading("due_date", text="Due Date")
        invoices_tree.heading("total", text="Total Amount")
        invoices_tree.heading("status", text="Status")
        
        # Define columns
        invoices_tree.column("id", width=50, anchor=tk.CENTER)
        invoices_tree.column("invoice_number", width=100, anchor=tk.CENTER)
        invoices_tree.column("date", width=120, anchor=tk.CENTER)
        invoices_tree.column("due_date", width=120, anchor=tk.CENTER)
        invoices_tree.column("total", width=120, anchor=tk.E)
        invoices_tree.column("status", width=100, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(invoices_frame, orient=tk.VERTICAL, command=invoices_tree.yview)
        invoices_tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        invoices_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Load invoices
        for invoice in invoices:
            inv_id, inv_number, date, due_date, total, status = invoice
            
            # Format dates
            date_formatted = datetime.fromisoformat(date).strftime('%Y-%m-%d')
            due_date_formatted = datetime.fromisoformat(due_date).strftime('%Y-%m-%d')
            
            # Format total
            total_formatted = f"{currency}{total:.2f}"
            
            # Determine tag based on status
            tag = status.lower()
            
            invoices_tree.insert('', tk.END, values=(
                inv_id, inv_number, date_formatted, due_date_formatted, 
                total_formatted, status
            ), tags=(tag,))
        
        # Configure tags for status colors
        invoices_tree.tag_configure('paid', background='#d4edda')
        invoices_tree.tag_configure('unpaid', background='#fff3cd')
        invoices_tree.tag_configure('partial', background='#d1ecf1')
        invoices_tree.tag_configure('overdue', background='#f8d7da')
        
        # Bind double-click to view invoice
        invoices_tree.bind("<Double-1>", lambda event: self.view_invoice_from_customer(invoices_tree))
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        view_invoice_button = ttk.Button(button_frame, text="View Invoice", 
                                        command=lambda: self.view_invoice_from_customer(invoices_tree))
        view_invoice_button.pack(side=tk.LEFT, padx=(0, 10))
        
        edit_button = ttk.Button(button_frame, text="Edit Customer", 
                                command=lambda: self.edit_customer_from_view(customer['id'], dialog))
        edit_button.pack(side=tk.LEFT, padx=(0, 10))
        
        close_button = ttk.Button(button_frame, text="Close", 
                                 command=dialog.destroy)
        close_button.pack(side=tk.LEFT)
    
    def create_invoice_for_customer(self, customer_id, dialog):
        """Create a new invoice for a specific customer"""
        # Close the customer view dialog
        dialog.destroy()
        
        # Show the create invoice dialog with the customer pre-selected
        self.show_create_invoice_dialog_for_customer(customer_id)
    
    def show_create_invoice_dialog_for_customer(self, customer_id):
        """Show dialog to create a new invoice with a pre-selected customer"""
        # This is similar to show_create_invoice_dialog but with the customer pre-selected
        # Create a new top-level window
        dialog = tk.Toplevel(self.parent)
        dialog.title("Create New Invoice")
        dialog.geometry("900x700")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create main frame
        main_frame = ttk.Frame(dialog, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create form frame
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Invoice header
        header_frame = ttk.LabelFrame(form_frame, text="Invoice Information")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Left column
        left_col = ttk.Frame(header_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Invoice number
        ttk.Label(left_col, text="Invoice Number:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Get next invoice number
        next_invoice_number = self.generate_invoice_number()
        
        invoice_number_var = tk.StringVar(value=next_invoice_number)
        invoice_number_entry = ttk.Entry(left_col, textvariable=invoice_number_var, width=20)
        invoice_number_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Invoice date
        ttk.Label(left_col, text="Invoice Date:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        
        invoice_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        invoice_date_entry = ttk.Entry(left_col, textvariable=invoice_date_var, width=20)
        invoice_date_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Due date
        ttk.Label(left_col, text="Due Date:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        
        # Calculate default due date (e.g., 30 days from now)
        default_due_days = int(self.get_setting('default_due_days'))
        default_due_date = (datetime.now() + timedelta(days=default_due_days)).strftime('%Y-%m-%d')
        
        due_date_var = tk.StringVar(value=default_due_date)
        due_date_entry = ttk.Entry(left_col, textvariable=due_date_var, width=20)
        due_date_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        # Right column
        right_col = ttk.Frame(header_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Customer selection
        ttk.Label(right_col, text="Customer:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Get customers from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM customers ORDER BY name")
        customers = [(row[0], row[1]) for row in cursor.fetchall()]
        
        # Get the name of the pre-selected customer
        cursor.execute("SELECT name FROM customers WHERE id = ?", (customer_id,))
        selected_customer_name = cursor.fetchone()[0]
        
        conn.close()
        
        # Create a dictionary to map customer names to IDs
        customer_dict = {customer[1]: customer[0] for customer in customers}
        
        customer_var = tk.StringVar(value=selected_customer_name)
        customer_combo = ttk.Combobox(right_col, textvariable=customer_var, 
                                     values=[customer[1] for customer in customers], width=30)
        customer_combo.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Add new customer button
        add_customer_button = ttk.Button(right_col, text="Add New", 
                                        command=lambda: self.show_add_customer_dialog(dialog))
        add_customer_button.grid(row=0, column=2, padx=(5, 0), pady=(0, 10))
        
        # Tax rate
        ttk.Label(right_col, text="Tax Rate (%):").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        
        default_tax_rate = self.get_setting('default_tax_rate')
        tax_rate_var = tk.StringVar(value=default_tax_rate)
        tax_rate_entry = ttk.Entry(right_col, textvariable=tax_rate_var, width=10)
        tax_rate_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Discount rate
        ttk.Label(right_col, text="Discount (%):").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        
        discount_rate_var = tk.StringVar(value="0")
        discount_rate_entry = ttk.Entry(right_col, textvariable=discount_rate_var, width=10)
        discount_rate_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        # Items section
        items_frame = ttk.LabelFrame(main_frame, text="Invoice Items")
        items_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create treeview for items
        columns = ("id", "item", "description", "quantity", "price", "total")
        items_tree = ttk.Treeview(items_frame, columns=columns, show="headings", height=10)
        
        # Define headings
        items_tree.heading("id", text="ID")
        items_tree.heading("item", text="Item")
        items_tree.heading("description", text="Description")
        items_tree.heading("quantity", text="Quantity")
        items_tree.heading("price", text="Unit Price")
        items_tree.heading("total", text="Total")
        
        # Define columns
        items_tree.column("id", width=50, anchor=tk.CENTER)
        items_tree.column("item", width=200)
        items_tree.column("description", width=250)
        items_tree.column("quantity", width=80, anchor=tk.CENTER)
        items_tree.column("price", width=100, anchor=tk.E)
        items_tree.column("total", width=100, anchor=tk.E)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, command=items_tree.yview)
        items_tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Item action buttons
        item_buttons_frame = ttk.Frame(main_frame)
        item_buttons_frame.pack(fill=tk.X, pady=(0, 20))
        
        add_item_button = ttk.Button(item_buttons_frame, text="Add Item", 
                                    command=lambda: self.show_add_invoice_item_dialog(items_tree))
        add_item_button.pack(side=tk.LEFT, padx=(0, 10))
        
        edit_item_button = ttk.Button(item_buttons_frame, text="Edit Item", 
                                     command=lambda: self.edit_invoice_item(items_tree))
        edit_item_button.pack(side=tk.LEFT, padx=(0, 10))
        
        remove_item_button = ttk.Button(item_buttons_frame, text="Remove Item", 
                                       style="Danger.TButton", 
                                       command=lambda: self.remove_invoice_item(items_tree))
        remove_item_button.pack(side=tk.LEFT)
        
        # Totals section
        totals_frame = ttk.Frame(main_frame)
        totals_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Create a frame for the totals on the right
        totals_right = ttk.Frame(totals_frame)
        totals_right.pack(side=tk.RIGHT)
        
        # Subtotal
        ttk.Label(totals_right, text="Subtotal:").grid(row=0, column=0, sticky=tk.E, pady=(0, 5))
        subtotal_var = tk.StringVar(value="0.00")
        subtotal_label = ttk.Label(totals_right, textvariable=subtotal_var, width=15, anchor=tk.E)
        subtotal_label.grid(row=0, column=1, sticky=tk.E, pady=(0, 5))
        
        # Tax
        ttk.Label(totals_right, text="Tax:").grid(row=1, column=0, sticky=tk.E, pady=(0, 5))
        tax_var = tk.StringVar(value="0.00")
        tax_label = ttk.Label(totals_right, textvariable=tax_var, width=15, anchor=tk.E)
        tax_label.grid(row=1, column=1, sticky=tk.E, pady=(0, 5))
        
        # Discount
        ttk.Label(totals_right, text="Discount:").grid(row=2, column=0, sticky=tk.E, pady=(0, 5))
        discount_var = tk.StringVar(value="0.00")
        discount_label = ttk.Label(totals_right, textvariable=discount_var, width=15, anchor=tk.E)
        discount_label.grid(row=2, column=1, sticky=tk.E, pady=(0, 5))
        
        # Total
        ttk.Label(totals_right, text="Total:", font=("Helvetica", 10, "bold")).grid(row=3, column=0, sticky=tk.E, pady=(5, 0))
        total_var = tk.StringVar(value="0.00")
        total_label = ttk.Label(totals_right, textvariable=total_var, width=15, anchor=tk.E, font=("Helvetica", 10, "bold"))
        total_label.grid(row=3, column=1, sticky=tk.E, pady=(5, 0))
        
        # Notes section
        notes_frame = ttk.LabelFrame(main_frame, text="Notes")
        notes_frame.pack(fill=tk.X, pady=(0, 20))
        
        notes_text = tk.Text(notes_frame, height=3, width=50)
        notes_text.pack(fill=tk.X, padx=10, pady=10)
        
        # Function to calculate totals
        def calculate_totals():
            # Get all items
            items = []
            for item_id in items_tree.get_children():
                item_values = items_tree.item(item_id, 'values')
                items.append(item_values)
            
            # Calculate subtotal
            subtotal = sum(float(item[5].replace(self.get_setting('currency_symbol'), '')) for item in items)
            
            # Calculate tax
            try:
                tax_rate = float(tax_rate_var.get())
                tax_amount = subtotal * (tax_rate / 100)
            except ValueError:
                tax_rate = 0
                tax_amount = 0
            
            # Calculate discount
            try:
                discount_rate = float(discount_rate_var.get())
                discount_amount = subtotal * (discount_rate / 100)
            except ValueError:
                discount_rate = 0
                discount_amount = 0
            
            # Calculate total
            total = subtotal + tax_amount - discount_amount
            
            # Update labels
            currency = self.get_setting('currency_symbol')
            subtotal_var.set(f"{currency}{subtotal:.2f}")
            tax_var.set(f"{currency}{tax_amount:.2f}")
            discount_var.set(f"{currency}{discount_amount:.2f}")
            total_var.set(f"{currency}{total:.2f}")
            
            return subtotal, tax_amount, discount_amount, total
        
        # Bind tax and discount entries to recalculate totals
        tax_rate_var.trace("w", lambda name, index, mode: calculate_totals())
        discount_rate_var.trace("w", lambda name, index, mode: calculate_totals())
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        save_button = ttk.Button(button_frame, text="Save Invoice", 
                                command=lambda: self.save_invoice(
                                    invoice_number_var.get(),
                                    customer_dict.get(customer_var.get()),
                                    invoice_date_var.get(),
                                    due_date_var.get(),
                                    tax_rate_var.get(),
                                    discount_rate_var.get(),
                                    items_tree,
                                    notes_text.get("1.0", tk.END).strip(),
                                    calculate_totals,
                                    dialog
                                ))
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        save_print_button = ttk.Button(button_frame, text="Save & Print", 
                                      command=lambda: self.save_and_print_invoice(
                                          invoice_number_var.get(),
                                          customer_dict.get(customer_var.get()),
                                          invoice_date_var.get(),
                                          due_date_var.get(),
                                          tax_rate_var.get(),
                                          discount_rate_var.get(),
                                          items_tree,
                                          notes_text.get("1.0", tk.END).strip(),
                                          calculate_totals,
                                          dialog
                                      ))
        save_print_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT)
    
    def view_invoice_from_customer(self, invoices_tree):
        """View an invoice from the customer view dialog"""
        # Get selected invoice
        selected = invoices_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select an invoice to view")
            return
        
        # Get invoice ID
        invoice_id = invoices_tree.item(selected[0], 'values')[0]
        
        # Close the customer view dialog (parent of the invoices_tree)
        parent_dialog = invoices_tree.master.master.master
        parent_dialog.destroy()
        
        # Select the invoice in the main invoices tree
        for item in self.invoices_tree.get_children():
            if self.invoices_tree.item(item, 'values')[0] == invoice_id:
                self.invoices_tree.selection_set(item)
                break
        
        # Show the invoice view dialog
        self.show_view_invoice_dialog()
    
    def edit_customer_from_view(self, customer_id, dialog):
        """Edit a customer from the view dialog"""
        # Close the view dialog
        dialog.destroy()
        
        # Get customer data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT name, email, phone, address, tax_id
        FROM customers
        WHERE id = ?
        ''', (customer_id,))
        
        customer = cursor.fetchone()
        conn.close()
        
        if not customer:
            messagebox.showerror("Error", "Customer not found")
            return
        
        name, email, phone, address, tax_id = customer
        
        # Create a new top-level window
        edit_dialog = tk.Toplevel(self.parent)
        edit_dialog.title("Edit Customer")
        edit_dialog.geometry("500x400")
        edit_dialog.transient(self.parent)
        edit_dialog.grab_set()
        
        # Make dialog modal
        edit_dialog.focus_set()
        
        # Create form frame
        form_frame = ttk.Frame(edit_dialog, padding="20 20 20 20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        name_entry = ttk.Entry(form_frame, width=40)
        name_entry.insert(0, name)
        name_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        email_entry = ttk.Entry(form_frame, width=40)
        email_entry.insert(0, email if email else "")
        email_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Phone:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        phone_entry = ttk.Entry(form_frame, width=40)
        phone_entry.insert(0, phone if phone else "")
        phone_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Address:").grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        address_entry = ttk.Entry(form_frame, width=40)
        address_entry.insert(0, address if address else "")
        address_entry.grid(row=3, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Tax ID:").grid(row=4, column=0, sticky=tk.W, pady=(0, 10))
        tax_id_entry = ttk.Entry(form_frame, width=40)
        tax_id_entry.insert(0, tax_id if tax_id else "")
        tax_id_entry.grid(row=4, column=1, sticky=tk.W, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))
        
        save_button = ttk.Button(button_frame, text="Save", 
                                command=lambda: self.update_customer_and_view(
                                    customer_id,
                                    name_entry.get(),
                                    email_entry.get(),
                                    phone_entry.get(),
                                    address_entry.get(),
                                    tax_id_entry.get(),
                                    edit_dialog
                                ))
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=edit_dialog.destroy)
        cancel_button.pack(side=tk.LEFT)
    
    def update_customer_and_view(self, customer_id, name, email, phone, address, tax_id, dialog):
        """Update a customer and then show the view dialog again"""
        # Validate inputs
        if not name:
            messagebox.showerror("Error", "Customer name is required", parent=dialog)
            return
        
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Error", "Invalid email format", parent=dialog)
            return
        
        # Update in database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE customers
            SET name = ?, email = ?, phone = ?, address = ?, tax_id = ?
            WHERE id = ?
            ''', (name, email, phone, address, tax_id, customer_id))
            
            conn.commit()
            messagebox.showinfo("Success", "Customer updated successfully", parent=dialog)
            
            # Close dialog
            dialog.destroy()
            
            # Refresh customers list
            self.load_customers()
            
            # Show the view dialog again
            self.show_view_customer_dialog()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to update customer: {str(e)}", parent=dialog)
        
        finally:
            conn.close()
    
    def delete_customer(self):
        """Delete a customer"""
        # Get selected customer
        selected = self.customers_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a customer to delete")
            return
        
        # Get customer ID and name
        customer_values = self.customers_tree.item(selected[0], 'values')
        customer_id = customer_values[0]
        customer_name = customer_values[1]
        
        # Check if customer has invoices
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM invoices WHERE customer_id = ?", (customer_id,))
        invoice_count = cursor.fetchone()[0]
        
        if invoice_count > 0:
            conn.close()
            messagebox.showerror("Error", 
                               f"Cannot delete customer '{customer_name}' because they have {invoice_count} invoice(s).\n\n"
                               "Delete all invoices for this customer first.")
            return
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Delete", 
                                     f"Are you sure you want to delete customer '{customer_name}'?\n\nThis action cannot be undone.")
        if not confirm:
            conn.close()
            return
        
        # Delete from database
        try:
            cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
            conn.commit()
            messagebox.showinfo("Success", f"Customer '{customer_name}' deleted successfully")
            
            # Refresh customers list
            self.load_customers()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to delete customer: {str(e)}")
        
        finally:
            conn.close()
    
    def setup_payments_tab(self):
        """Set up the payments tab with payment listing and management"""
        # Create frame for payments content
        payments_content = ttk.Frame(self.payments_tab, style="TFrame")
        payments_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Search and filter bar
        filter_frame = ttk.Frame(payments_content, style="TFrame")
        filter_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Date range
        ttk.Label(filter_frame, text="From:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Create date variables
        payment_from_date_var = tk.StringVar()
        payment_to_date_var = tk.StringVar()
        
        # Set default dates (last 30 days)
        today = datetime.now()
        thirty_days_ago = today - timedelta(days=30)
        
        payment_from_date_var.set(thirty_days_ago.strftime('%Y-%m-%d'))
        payment_to_date_var.set(today.strftime('%Y-%m-%d'))
        
        from_date_entry = ttk.Entry(filter_frame, textvariable=payment_from_date_var, width=12)
        from_date_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(filter_frame, text="To:").pack(side=tk.LEFT, padx=(0, 5))
        to_date_entry = ttk.Entry(filter_frame, textvariable=payment_to_date_var, width=12)
        to_date_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # Payment method filter
        ttk.Label(filter_frame, text="Method:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Get payment methods
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM payment_gateways WHERE is_active = 1")
        payment_methods = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Add "All" option
        payment_methods = ["All"] + payment_methods
        
        payment_method_var = tk.StringVar(value="All")
        method_combo = ttk.Combobox(filter_frame, textvariable=payment_method_var, 
                                   values=payment_methods, state="readonly", width=15)
        method_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # Filter button
        filter_button = ttk.Button(filter_frame, text="Filter", 
                                  command=lambda: self.load_payments(
                                      payment_from_date_var.get(),
                                      payment_to_date_var.get(),
                                      payment_method_var.get()
                                  ))
        filter_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Reset button
        reset_button = ttk.Button(filter_frame, text="Reset", 
                                 command=lambda: self.reset_payment_filters(
                                     payment_from_date_var,
                                     payment_to_date_var,
                                     payment_method_var
                                 ))
        reset_button.pack(side=tk.LEFT)
        
        # Payments table
        table_frame = ttk.Frame(payments_content, style="TFrame")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview
        columns = ("id", "date", "invoice", "customer", "amount", "method", "reference", "recorded_by")
        self.payments_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Define headings
        self.payments_tree.heading("id", text="ID")
        self.payments_tree.heading("date", text="Payment Date")
        self.payments_tree.heading("invoice", text="Invoice #")
        self.payments_tree.heading("customer", text="Customer")
        self.payments_tree.heading("amount", text="Amount")
        self.payments_tree.heading("method", text="Payment Method")
        self.payments_tree.heading("reference", text="Reference")
        self.payments_tree.heading("recorded_by", text="Recorded By")
        
        # Define columns
        self.payments_tree.column("id", width=50, anchor=tk.CENTER)
        self.payments_tree.column("date", width=150, anchor=tk.CENTER)
        self.payments_tree.column("invoice", width=100, anchor=tk.CENTER)
        self.payments_tree.column("customer", width=200)
        self.payments_tree.column("amount", width=100, anchor=tk.E)
        self.payments_tree.column("method", width=150)
        self.payments_tree.column("reference", width=150)
        self.payments_tree.column("recorded_by", width=150)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.payments_tree.yview)
        self.payments_tree.configure(yscroll=y_scrollbar.set)
        
        x_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.payments_tree.xview)
        self.payments_tree.configure(xscroll=x_scrollbar.set)
        
        # Pack widgets
        self.payments_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind double-click to view invoice
        self.payments_tree.bind("<Double-1>", lambda event: self.view_invoice_from_payment())
        
        # Action buttons
        action_frame = ttk.Frame(payments_content, style="TFrame")
        action_frame.pack(fill=tk.X, pady=(20, 0))
        
        view_invoice_button = ttk.Button(action_frame, text="View Invoice", 
                                        command=self.view_invoice_from_payment)
        view_invoice_button.pack(side=tk.LEFT, padx=(0, 10))
        
        delete_button = ttk.Button(action_frame, text="Delete Payment", 
                                  style="Danger.TButton", command=self.delete_payment_from_list)
        delete_button.pack(side=tk.LEFT)
        
        # Load payments with default filters
        self.load_payments(
            payment_from_date_var.get(),
            payment_to_date_var.get(),
            payment_method_var.get()
        )
    
    def load_payments(self, from_date, to_date, payment_method):
        """Load payments into the treeview based on filters"""
        # Clear existing items
        for item in self.payments_tree.get_children():
            self.payments_tree.delete(item)
        
        # Validate dates
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
            # Add time to make it end of day
            to_date_obj = to_date_obj.replace(hour=23, minute=59, second=59)
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
            return
        
        # Build query based on filters
        query = '''
        SELECT p.id, p.payment_date, i.invoice_number, c.name as customer_name,
               p.amount, p.payment_method, p.reference_number, u.username as recorded_by
        FROM payments p
        JOIN invoices i ON p.invoice_id = i.id
        JOIN customers c ON i.customer_id = c.id
        JOIN users u ON p.recorded_by = u.id
        WHERE p.payment_date BETWEEN ? AND ?
        '''
        
        params = [from_date_obj.isoformat(), to_date_obj.isoformat()]
        
        if payment_method != "All":
            query += " AND p.payment_method = ?"
            params.append(payment_method)
        
        query += " ORDER BY p.payment_date DESC"
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        payments = cursor.fetchall()
        conn.close()
        
        # Get currency symbol
        currency = self.get_setting('currency_symbol')
        
        # Insert into treeview
        for payment in payments:
            payment_id, date, invoice_number, customer, amount, method, reference, recorded_by = payment
            
            # Format date
            try:
                date_formatted = datetime.fromisoformat(date).strftime('%Y-%m-%d %H:%M')
            except:
                date_formatted = date
            
            # Format amount
            amount_formatted = f"{currency}{amount:.2f}"
            
            self.payments_tree.insert('', tk.END, values=(
                payment_id, date_formatted, invoice_number, customer,
                amount_formatted, method, reference or "", recorded_by
            ))
    
    def reset_payment_filters(self, from_date_var, to_date_var, method_var):
        """Reset payment filters to default values"""
        # Reset date range to last 30 days
        today = datetime.now()
        thirty_days_ago = today - timedelta(days=30)
        
        from_date_var.set(thirty_days_ago.strftime('%Y-%m-%d'))
        to_date_var.set(today.strftime('%Y-%m-%d'))
        
        # Reset method
        method_var.set("All")
        
        # Reload payments
        self.load_payments(
            from_date_var.get(),
            to_date_var.get(),
            method_var.get()
        )
    
    def view_invoice_from_payment(self):
        """View the invoice associated with a payment"""
        # Get selected payment
        selected = self.payments_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a payment to view its invoice")
            return
        
        # Get payment ID
        payment_id = self.payments_tree.item(selected[0], 'values')[0]
        
        # Get invoice ID from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT invoice_id FROM payments WHERE id = ?", (payment_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            messagebox.showerror("Error", "Invoice not found")
            return
        
        invoice_id = result[0]
        
        # Select the invoice in the main invoices tree
        for item in self.invoices_tree.get_children():
            if self.invoices_tree.item(item, 'values')[0] == str(invoice_id):
                self.invoices_tree.selection_set(item)
                break
        
        # Switch to invoices tab
        self.billing_notebook.select(self.invoices_tab)
        
        # Show the invoice view dialog
        self.show_view_invoice_dialog()
    
    def delete_payment_from_list(self):
        """Delete a payment from the payments list"""
        # Get selected payment
        selected = self.payments_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a payment to delete")
            return
        
        # Get payment ID
        payment_values = self.payments_tree.item(selected[0], 'values')
        payment_id = payment_values[0]
        invoice_number = payment_values[2]
        amount = payment_values[4]
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Delete", 
                                     f"Are you sure you want to delete the {amount} payment for Invoice #{invoice_number}?\n\n"
                                     "This action cannot be undone.")
        if not confirm:
            return
        
        # Get invoice ID from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT invoice_id FROM payments WHERE id = ?", (payment_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            messagebox.showerror("Error", "Payment not found")
            return
        
        invoice_id = result[0]
        
        try:
            # Delete payment
            cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
            
            # Update invoice status
            # Calculate total paid
            cursor.execute("SELECT SUM(amount) FROM payments WHERE invoice_id = ?", (invoice_id,))
            total_paid = cursor.fetchone()[0] or 0
            
            # Get invoice total
            cursor.execute("SELECT total_amount FROM invoices WHERE id = ?", (invoice_id,))
            total_amount = cursor.fetchone()[0]
            
            # Determine new status
            if total_paid >= total_amount:
                new_status = "Paid"
            elif total_paid > 0:
                new_status = "Partial"
            else:
                new_status = "Unpaid"
            
            cursor.execute("UPDATE invoices SET status = ? WHERE id = ?", (new_status, invoice_id))
            
            conn.commit()
            messagebox.showinfo("Success", "Payment deleted successfully")
            
            # Refresh payments list
            self.load_payments(
                self.date_from_var.get(),
                self.date_to_var.get(),
                "All"
            )
            
            # Refresh invoices list
            self.load_invoices()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to delete payment: {str(e)}")
        finally:
            conn.close()
    
    def setup_billing_reports_tab(self):
        """Set up the billing reports tab with reporting options"""
        # Create frame for reports content
        reports_content = ttk.Frame(self.billing_reports_tab, style="TFrame")
        reports_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(reports_content, text="Generate Billing Reports", 
                               style="Header.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Report options
        options_frame = ttk.LabelFrame(reports_content, text="Report Options", style="TFrame")
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Report type
        ttk.Label(options_frame, text="Report Type:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        
        report_type_var =  tk.StringVar(value="Sales Summary")
        report_types = [
            "Sales Summary", 
            "Customer Sales", 
            "Payment Collection",
            "Outstanding Invoices",
            "Tax Report"
        ]
        
        report_type_combo = ttk.Combobox(options_frame, textvariable=report_type_var, 
                                        values=report_types, state="readonly", width=30)
        report_type_combo.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Date range
        ttk.Label(options_frame, text="Date Range:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        
        date_frame = ttk.Frame(options_frame, style="TFrame")
        date_frame.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Create date variables for reports
        report_from_date_var = tk.StringVar()
        report_to_date_var = tk.StringVar()
        
        # Set default dates (last 30 days)
        today = datetime.now()
        thirty_days_ago = today - timedelta(days=30)
        
        report_from_date_var.set(thirty_days_ago.strftime('%Y-%m-%d'))
        report_to_date_var.set(today.strftime('%Y-%m-%d'))
        
        ttk.Label(date_frame, text="From:").pack(side=tk.LEFT, padx=(0, 5))
        from_date_entry = ttk.Entry(date_frame, textvariable=report_from_date_var, width=12)
        from_date_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(date_frame, text="To:").pack(side=tk.LEFT, padx=(0, 5))
        to_date_entry = ttk.Entry(date_frame, textvariable=report_to_date_var, width=12)
        to_date_entry.pack(side=tk.LEFT)
        
        # Format options
        ttk.Label(options_frame, text="Format:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        
        report_format_var = tk.StringVar(value="Preview")
        format_frame = ttk.Frame(options_frame, style="TFrame")
        format_frame.grid(row=2, column=1, sticky=tk.W, padx=10, pady=10)
        
        ttk.Radiobutton(format_frame, text="Preview", variable=report_format_var, 
                       value="Preview").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(format_frame, text="Save as CSV", variable=report_format_var, 
                       value="CSV").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(format_frame, text="Save as PDF", variable=report_format_var, 
                       value="PDF").pack(side=tk.LEFT)
        
        # Generate button
        generate_button = ttk.Button(options_frame, text="Generate Report", 
                                    command=lambda: self.generate_billing_report(
                                        report_type_var.get(),
                                        report_from_date_var.get(),
                                        report_to_date_var.get(),
                                        report_format_var.get()
                                    ))
        generate_button.grid(row=3, column=0, columnspan=2, pady=20)
        
        # Report preview area
        preview_frame = ttk.LabelFrame(reports_content, text="Report Preview", style="TFrame")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create treeview for report preview
        self.billing_report_tree = ttk.Treeview(preview_frame)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.billing_report_tree.yview)
        self.billing_report_tree.configure(yscroll=y_scrollbar.set)
        
        x_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.billing_report_tree.xview)
        self.billing_report_tree.configure(xscroll=x_scrollbar.set)
        
        # Pack widgets
        self.billing_report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def generate_billing_report(self, report_type, from_date, to_date, report_format):
        """Generate a billing report based on selected options"""
        # Validate dates
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
            # Add time to make it end of day
            to_date_obj = to_date_obj.replace(hour=23, minute=59, second=59)
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
            return
        
        # Clear existing report
        for item in self.billing_report_tree.get_children():
            self.billing_report_tree.delete(item)
        
        # Generate report based on type
        if report_type == "Sales Summary":
            self.generate_sales_summary_report(from_date_obj, to_date_obj)
        elif report_type == "Customer Sales":
            self.generate_customer_sales_report(from_date_obj, to_date_obj)
        elif report_type == "Payment Collection":
            self.generate_payment_collection_report(from_date_obj, to_date_obj)
        elif report_type == "Outstanding Invoices":
            self.generate_outstanding_invoices_report()
        elif report_type == "Tax Report":
            self.generate_tax_report(from_date_obj, to_date_obj)
        
        # If CSV or PDF format is selected, save to file
        if report_format == "CSV":
            self.save_billing_report_as_csv(report_type)
        elif report_format == "PDF":
            self.save_billing_report_as_pdf(report_type, from_date, to_date)
    
    def generate_sales_summary_report(self, from_date, to_date):
        """Generate a sales summary report"""
        # Configure columns
        columns = ("period", "invoices", "sales", "tax", "discount", "net_sales", "paid", "outstanding")
        self.billing_report_tree.configure(columns=columns, show="headings")
        
        # Define headings
        self.billing_report_tree.heading("period", text="Period")
        self.billing_report_tree.heading("invoices", text="Invoices")
        self.billing_report_tree.heading("sales", text="Gross Sales")
        self.billing_report_tree.heading("tax", text="Tax")
        self.billing_report_tree.heading("discount", text="Discounts")
        self.billing_report_tree.heading("net_sales", text="Net Sales")
        self.billing_report_tree.heading("paid", text="Amount Paid")
        self.billing_report_tree.heading("outstanding", text="Outstanding")
        
        # Define columns
        self.billing_report_tree.column("period", width=100)
        self.billing_report_tree.column("invoices", width=80, anchor=tk.CENTER)
        self.billing_report_tree.column("sales", width=120, anchor=tk.E)
        self.billing_report_tree.column("tax", width=100, anchor=tk.E)
        self.billing_report_tree.column("discount", width=100, anchor=tk.E)
        self.billing_report_tree.column("net_sales", width=120, anchor=tk.E)
        self.billing_report_tree.column("paid", width=120, anchor=tk.E)
        self.billing_report_tree.column("outstanding", width=120, anchor=tk.E)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        # Determine if we should group by month or day based on date range
        days_diff = (to_date - from_date).days
        if days_diff > 60:  # If more than 60 days, group by month
            group_by = "month"
            date_format = "%Y-%m"
            period_format = "%b %Y"
        else:
            group_by = "day"
            date_format = "%Y-%m-%d"
            period_format = "%Y-%m-%d"
        
        # Get sales data grouped by period
        if group_by == "month":
            cursor.execute('''
            SELECT 
                strftime('%Y-%m', invoice_date) as period,
                COUNT(*) as invoice_count,
                SUM(subtotal) as gross_sales,
                SUM(tax_amount) as tax,
                SUM(discount_amount) as discount,
                SUM(total_amount) as net_sales
            FROM invoices
            WHERE invoice_date BETWEEN ? AND ?
            GROUP BY period
            ORDER BY period
            ''', (from_date.isoformat(), to_date.isoformat()))
        else:
            cursor.execute('''
            SELECT 
                strftime('%Y-%m-%d', invoice_date) as period,
                COUNT(*) as invoice_count,
                SUM(subtotal) as gross_sales,
                SUM(tax_amount) as tax,
                SUM(discount_amount) as discount,
                SUM(total_amount) as net_sales
            FROM invoices
            WHERE invoice_date BETWEEN ? AND ?
            GROUP BY period
            ORDER BY period
            ''', (from_date.isoformat(), to_date.isoformat()))
        
        sales_data = cursor.fetchall()
        
        # Get payment data grouped by invoice date and period
        if group_by == "month":
            cursor.execute('''
            SELECT 
                strftime('%Y-%m', i.invoice_date) as period,
                SUM(p.amount) as amount_paid
            FROM payments p
            JOIN invoices i ON p.invoice_id = i.id
            WHERE i.invoice_date BETWEEN ? AND ?
            GROUP BY period
            ORDER BY period
            ''', (from_date.isoformat(), to_date.isoformat()))
        else:
            cursor.execute('''
            SELECT 
                strftime('%Y-%m-%d', i.invoice_date) as period,
                SUM(p.amount) as amount_paid
            FROM payments p
            JOIN invoices i ON p.invoice_id = i.id
            WHERE i.invoice_date BETWEEN ? AND ?
            GROUP BY period
            ORDER BY period
            ''', (from_date.isoformat(), to_date.isoformat()))
        
        payment_data = cursor.fetchall()
        
        # Create a dictionary to map periods to payment amounts
        payment_dict = {row[0]: row[1] for row in payment_data}
        
        conn.close()
        
        # Get currency symbol
        currency = self.get_setting('currency_symbol')
        
        # Insert data into treeview
        total_invoices = 0
        total_gross_sales = 0
        total_tax = 0
        total_discount = 0
        total_net_sales = 0
        total_paid = 0
        total_outstanding = 0
        
        for row in sales_data:
            period, invoice_count, gross_sales, tax, discount, net_sales = row
            
            # Format period
            try:
                period_obj = datetime.strptime(period, date_format)
                period_formatted = period_obj.strftime(period_format)
            except:
                period_formatted = period
            
            # Get amount paid for this period
            amount_paid = payment_dict.get(period, 0) or 0
            
            # Calculate outstanding
            outstanding = net_sales - amount_paid
            
            # Format values
            gross_sales_formatted = f"{currency}{gross_sales:.2f}"
            tax_formatted = f"{currency}{tax:.2f}"
            discount_formatted = f"{currency}{discount:.2f}"
            net_sales_formatted = f"{currency}{net_sales:.2f}"
            paid_formatted = f"{currency}{amount_paid:.2f}"
            outstanding_formatted = f"{currency}{outstanding:.2f}"
            
            # Insert into treeview
            self.billing_report_tree.insert('', tk.END, values=(
                period_formatted, invoice_count, gross_sales_formatted, tax_formatted,
                discount_formatted, net_sales_formatted, paid_formatted, outstanding_formatted
            ))
            
            # Update totals
            total_invoices += invoice_count
            total_gross_sales += gross_sales
            total_tax += tax
            total_discount += discount
            total_net_sales += net_sales
            total_paid += amount_paid
            total_outstanding += outstanding
        
        # Add total row
        self.billing_report_tree.insert('', tk.END, values=(
            "TOTAL", total_invoices, 
            f"{currency}{total_gross_sales:.2f}", 
            f"{currency}{total_tax:.2f}",
            f"{currency}{total_discount:.2f}", 
            f"{currency}{total_net_sales:.2f}",
            f"{currency}{total_paid:.2f}", 
            f"{currency}{total_outstanding:.2f}"
        ), tags=('total',))
        
        # Configure tag for total row
        self.billing_report_tree.tag_configure('total', font=('Helvetica', 10, 'bold'))
    
    def generate_customer_sales_report(self, from_date, to_date):
        """Generate a customer sales report"""
        # Configure columns
        columns = ("customer", "invoices", "sales", "tax", "discount", "net_sales", "paid", "outstanding")
        self.billing_report_tree.configure(columns=columns, show="headings")
        
        # Define headings
        self.billing_report_tree.heading("customer", text="Customer")
        self.billing_report_tree.heading("invoices", text="Invoices")
        self.billing_report_tree.heading("sales", text="Gross Sales")
        self.billing_report_tree.heading("tax", text="Tax")
        self.billing_report_tree.heading("discount", text="Discounts")
        self.billing_report_tree.heading("net_sales", text="Net Sales")
        self.billing_report_tree.heading("paid", text="Amount Paid")
        self.billing_report_tree.heading("outstanding", text="Outstanding")
        
        # Define columns
        self.billing_report_tree.column("customer", width=200)
        self.billing_report_tree.column("invoices", width=80, anchor=tk.CENTER)
        self.billing_report_tree.column("sales", width=120, anchor=tk.E)
        self.billing_report_tree.column("tax", width=100, anchor=tk.E)
        self.billing_report_tree.column("discount", width=100, anchor=tk.E)
        self.billing_report_tree.column("net_sales", width=120, anchor=tk.E)
        self.billing_report_tree.column("paid", width=120, anchor=tk.E)
        self.billing_report_tree.column("outstanding", width=120, anchor=tk.E)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        # Get sales data grouped by customer
        cursor.execute('''
        SELECT 
            c.name as customer,
            COUNT(i.id) as invoice_count,
            SUM(i.subtotal) as gross_sales,
            SUM(i.tax_amount) as tax,
            SUM(i.discount_amount) as discount,
            SUM(i.total_amount) as net_sales
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.invoice_date BETWEEN ? AND ?
        GROUP BY c.id
        ORDER BY net_sales DESC
        ''', (from_date.isoformat(), to_date.isoformat()))
        
        sales_data = cursor.fetchall()
        
        # Get payment data grouped by customer
        cursor.execute('''
        SELECT 
            c.name as customer,
            SUM(p.amount) as amount_paid
        FROM payments p
        JOIN invoices i ON p.invoice_id = i.id
        JOIN customers c ON i.customer_id = c.id
        WHERE i.invoice_date BETWEEN ? AND ?
        GROUP BY c.id
        ORDER BY c.name
        ''', (from_date.isoformat(), to_date.isoformat()))
        
        payment_data = cursor.fetchall()
        
        # Create a dictionary to map customers to payment amounts
        payment_dict = {row[0]: row[1] for row in payment_data}
        
        conn.close()
        
        # Get currency symbol
        currency = self.get_setting('currency_symbol')
        
        # Insert data into treeview
        total_invoices = 0
        total_gross_sales = 0
        total_tax = 0
        total_discount = 0
        total_net_sales = 0
        total_paid = 0
        total_outstanding = 0
        
        for row in sales_data:
            customer, invoice_count, gross_sales, tax, discount, net_sales = row
            
            # Get amount paid for this customer
            amount_paid = payment_dict.get(customer, 0) or 0
            
            # Calculate outstanding
            outstanding = net_sales - amount_paid
            
            # Format values
            gross_sales_formatted = f"{currency}{gross_sales:.2f}"
            tax_formatted = f"{currency}{tax:.2f}"
            discount_formatted = f"{currency}{discount:.2f}"
            net_sales_formatted = f"{currency}{net_sales:.2f}"
            paid_formatted = f"{currency}{amount_paid:.2f}"
            outstanding_formatted = f"{currency}{outstanding:.2f}"
            
            # Insert into treeview
            self.billing_report_tree.insert('', tk.END, values=(
                customer, invoice_count, gross_sales_formatted, tax_formatted,
                discount_formatted, net_sales_formatted, paid_formatted, outstanding_formatted
            ))
            
            # Update totals
            total_invoices += invoice_count
            total_gross_sales += gross_sales
            total_tax += tax
            total_discount += discount
            total_net_sales += net_sales
            total_paid += amount_paid
            total_outstanding += outstanding
        
        # Add total row
        self.billing_report_tree.insert('', tk.END, values=(
            "TOTAL", total_invoices, 
            f"{currency}{total_gross_sales:.2f}", 
            f"{currency}{total_tax:.2f}",
            f"{currency}{total_discount:.2f}", 
            f"{currency}{total_net_sales:.2f}",
            f"{currency}{total_paid:.2f}", 
            f"{currency}{total_outstanding:.2f}"
        ), tags=('total',))
        
        # Configure tag for total row
        self.billing_report_tree.tag_configure('total', font=('Helvetica', 10, 'bold'))
    
    def generate_payment_collection_report(self, from_date, to_date):
        """Generate a payment collection report"""
        # Configure columns
        columns = ("date", "invoice", "customer", "amount", "method", "reference", "recorded_by")
        self.billing_report_tree.configure(columns=columns, show="headings")
        
        # Define headings
        self.billing_report_tree.heading("date", text="Payment Date")
        self.billing_report_tree.heading("invoice", text="Invoice #")
        self.billing_report_tree.heading("customer", text="Customer")
        self.billing_report_tree.heading("amount", text="Amount")
        self.billing_report_tree.heading("method", text="Payment Method")
        self.billing_report_tree.heading("reference", text="Reference")
        self.billing_report_tree.heading("recorded_by", text="Recorded By")
        
        # Define columns
        self.billing_report_tree.column("date", width=150, anchor=tk.CENTER)
        self.billing_report_tree.column("invoice", width=100, anchor=tk.CENTER)
        self.billing_report_tree.column("customer", width=200)
        self.billing_report_tree.column("amount", width=120, anchor=tk.E)
        self.billing_report_tree.column("method", width=150)
        self.billing_report_tree.column("reference", width=150)
        self.billing_report_tree.column("recorded_by", width=150)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            p.payment_date, i.invoice_number, c.name as customer,
            p.amount, p.payment_method, p.reference_number, u.username as recorded_by
        FROM payments p
        JOIN invoices i ON p.invoice_id = i.id
        JOIN customers c ON i.customer_id = c.id
        JOIN users u ON p.recorded_by = u.id
        WHERE p.payment_date BETWEEN ? AND ?
        ORDER BY p.payment_date DESC
        ''', (from_date.isoformat(), to_date.isoformat()))
        
        payments = cursor.fetchall()
        
        # Get total by payment method
        cursor.execute('''
        SELECT 
            p.payment_method, SUM(p.amount) as total
        FROM payments p
        WHERE p.payment_date BETWEEN ? AND ?
        GROUP BY p.payment_method
        ORDER BY total DESC
        ''', (from_date.isoformat(), to_date.isoformat()))
        
        payment_totals = cursor.fetchall()
        
        conn.close()
        
        # Get currency symbol
        currency = self.get_setting('currency_symbol')
        
        # Insert data into treeview
        total_amount = 0
        
        for payment in payments:
            date, invoice_number, customer, amount, method, reference, recorded_by = payment
            
            # Format date
            try:
                date_formatted = datetime.fromisoformat(date).strftime('%Y-%m-%d %H:%M')
            except:
                date_formatted = date
            
            # Format amount
            amount_formatted = f"{currency}{amount:.2f}"
            
            # Insert into treeview
            self.billing_report_tree.insert('', tk.END, values=(
                date_formatted, invoice_number, customer, amount_formatted,
                method, reference or "", recorded_by
            ))
            
            # Update total
            total_amount += amount
        
        # Add separator
        self.billing_report_tree.insert('', tk.END, values=("", "", "", "", "", "", ""), tags=('separator',))
        
        # Add total row
        self.billing_report_tree.insert('', tk.END, values=(
            "", "", "TOTAL", f"{currency}{total_amount:.2f}", "", "", ""
        ), tags=('total',))
        
        # Add payment method breakdown
        self.billing_report_tree.insert('', tk.END, values=("", "", "", "", "", "", ""), tags=('separator',))
        self.billing_report_tree.insert('', tk.END, values=(
            "", "", "PAYMENT METHOD BREAKDOWN", "", "", "", ""
        ), tags=('header',))
        
        for method, total in payment_totals:
            self.billing_report_tree.insert('', tk.END, values=(
                "", "", method, f"{currency}{total:.2f}", 
                f"{(total / total_amount) * 100:.2f}%", "", ""
            ))
        
        # Configure tags
        self.billing_report_tree.tag_configure('total', font=('Helvetica', 10, 'bold'))
        self.billing_report_tree.tag_configure('header', font=('Helvetica', 10, 'bold'))
        self.billing_report_tree.tag_configure('separator', background='#f0f0f0')
    
    def generate_outstanding_invoices_report(self):
        """Generate a report of outstanding invoices"""
        # Configure columns
        columns = ("invoice", "customer", "date", "due_date", "days_overdue", "total", "paid", "balance")
        self.billing_report_tree.configure(columns=columns, show="headings")
        
        # Define headings
        self.billing_report_tree.heading("invoice", text="Invoice #")
        self.billing_report_tree.heading("customer", text="Customer")
        self.billing_report_tree.heading("date", text="Invoice Date")
        self.billing_report_tree.heading("due_date", text="Due Date")
        self.billing_report_tree.heading("days_overdue", text="Days Overdue")
        self.billing_report_tree.heading("total", text="Total Amount")
        self.billing_report_tree.heading("paid", text="Amount Paid")
        self.billing_report_tree.heading("balance", text="Balance")
        
        # Define columns
        self.billing_report_tree.column("invoice", width=100, anchor=tk.CENTER)
        self.billing_report_tree.column("customer", width=200)
        self.billing_report_tree.column("date", width=120, anchor=tk.CENTER)
        self.billing_report_tree.column("due_date", width=120, anchor=tk.CENTER)
        self.billing_report_tree.column("days_overdue", width=100, anchor=tk.CENTER)
        self.billing_report_tree.column("total", width=120, anchor=tk.E)
        self.billing_report_tree.column("paid", width=120, anchor=tk.E)
        self.billing_report_tree.column("balance", width=120, anchor=tk.E)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        # Get outstanding invoices
        cursor.execute('''
        SELECT 
            i.id, i.invoice_number, c.name as customer,
            i.invoice_date, i.due_date, i.total_amount,
            COALESCE((SELECT SUM(amount) FROM payments WHERE invoice_id = i.id), 0) as amount_paid
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.status IN ('Unpaid', 'Partial', 'Overdue')
        ORDER BY i.due_date
        ''')
        
        invoices = cursor.fetchall()
        conn.close()
        
        # Get currency symbol
        currency = self.get_setting('currency_symbol')
        
        # Current date for overdue calculation
        today = datetime.now().date()
        
        # Insert data into treeview
        total_outstanding = 0
        
        for invoice in invoices:
            inv_id, inv_number, customer, date, due_date, total, paid = invoice
            
            # Calculate balance
            balance = total - paid
            
            # Format dates
            try:
                date_formatted = datetime.fromisoformat(date).strftime('%Y-%m-%d')
                due_date_obj = datetime.fromisoformat(due_date)
                due_date_formatted = due_date_obj.strftime('%Y-%m-%d')
                
                # Calculate days overdue
                days_overdue = (today - due_date_obj.date()).days
                if days_overdue < 0:
                    days_overdue_formatted = ""
                else:
                    days_overdue_formatted = str(days_overdue)
            except:
                date_formatted = date
                due_date_formatted = due_date
                days_overdue_formatted = ""
            
            # Format amounts
            total_formatted = f"{currency}{total:.2f}"
            paid_formatted = f"{currency}{paid:.2f}"
            balance_formatted = f"{currency}{balance:.2f}"
            
            # Determine tag based on overdue status
            if days_overdue_formatted and int(days_overdue_formatted) > 30:
                tag = 'critical'
            elif days_overdue_formatted and int(days_overdue_formatted) > 0:
                tag = 'overdue'
            else:
                tag = 'normal'
            
            # Insert into treeview
            self.billing_report_tree.insert('', tk.END, values=(
                inv_number, customer, date_formatted, due_date_formatted,
                days_overdue_formatted, total_formatted, paid_formatted, balance_formatted
            ), tags=(tag,))
            
            # Update total
            total_outstanding += balance
        
        # Add total row
        self.billing_report_tree.insert('', tk.END, values=(
            "", "TOTAL", "", "", "", "", "", f"{currency}{total_outstanding:.2f}"
        ), tags=('total',))
        
        # Configure tags
        self.billing_report_tree.tag_configure('total', font=('Helvetica', 10, 'bold'))
        self.billing_report_tree.tag_configure('overdue', background='#fff3cd')
        self.billing_report_tree.tag_configure('critical', background='#f8d7da')
    
    def generate_tax_report(self, from_date, to_date):
        """Generate a tax report"""
        # Configure columns
        columns = ("period", "taxable_sales", "tax_rate", "tax_amount")
        self.billing_report_tree.configure(columns=columns, show="headings")
        
        # Define headings
        self.billing_report_tree.heading("period", text="Period")
        self.billing_report_tree.heading("taxable_sales", text="Taxable Sales")
        self.billing_report_tree.heading("tax_rate", text="Tax Rate")
        self.billing_report_tree.heading("tax_amount", text="Tax Amount")
        
        # Define columns
        self.billing_report_tree.column("period", width=150)
        self.billing_report_tree.column("taxable_sales", width=150, anchor=tk.E)
        self.billing_report_tree.column("tax_rate", width=100, anchor=tk.CENTER)
        self.billing_report_tree.column("tax_amount", width=150, anchor=tk.E)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        # Determine if we should group by month or day based on date range
        days_diff = (to_date - from_date).days
        if days_diff > 60:  # If more than 60 days, group by month
            group_by = "month"
            date_format = "%Y-%m"
            period_format = "%b %Y"
        else:
            group_by = "day"
            date_format = "%Y-%m-%d"
            period_format = "%Y-%m-%d"
        
        # Get tax data grouped by period and tax rate
        if group_by == "month":
            cursor.execute('''
            SELECT 
                strftime('%Y-%m', invoice_date) as period,
                tax_rate,
                SUM(subtotal) as taxable_sales,
                SUM(tax_amount) as tax_amount
            FROM invoices
            WHERE invoice_date BETWEEN ? AND ? AND tax_rate > 0
            GROUP BY period, tax_rate
            ORDER BY period, tax_rate
            ''', (from_date.isoformat(), to_date.isoformat()))
        else:
            cursor.execute('''
            SELECT 
                strftime('%Y-%m-%d', invoice_date) as period,
                tax_rate,
                SUM(subtotal) as taxable_sales,
                SUM(tax_amount) as tax_amount
            FROM invoices
            WHERE invoice_date BETWEEN ? AND ? AND tax_rate > 0
            GROUP BY period, tax_rate
            ORDER BY period, tax_rate
            ''', (from_date.isoformat(), to_date.isoformat()))
        
        tax_data = cursor.fetchall()
        conn.close()
        
        # Get currency symbol
        currency = self.get_setting('currency_symbol')
        
        # Insert data into treeview
        total_taxable_sales = 0
        total_tax_amount = 0
        
        for row in tax_data:
            period, tax_rate, taxable_sales, tax_amount = row
            
            # Format period
            try:
                period_obj = datetime.strptime(period, date_format)
                period_formatted = period_obj.strftime(period_format)
            except:
                period_formatted = period
            
            # Format values
            taxable_sales_formatted = f"{currency}{taxable_sales:.2f}"
            tax_rate_formatted = f"{tax_rate:.2f}%"
            tax_amount_formatted = f"{currency}{tax_amount:.2f}"
            
            # Insert into treeview
            self.billing_report_tree.insert('', tk.END, values=(
                period_formatted, taxable_sales_formatted, tax_rate_formatted, tax_amount_formatted
            ))
            
            # Update totals
            total_taxable_sales += taxable_sales
            total_tax_amount += tax_amount
        
        # Add total row
        self.billing_report_tree.insert('', tk.END, values=(
            "TOTAL", f"{currency}{total_taxable_sales:.2f}", "", f"{currency}{total_tax_amount:.2f}"
        ), tags=('total',))
        
        # Configure tag for total row
        self.billing_report_tree.tag_configure('total', font=('Helvetica', 10, 'bold'))
    
    def save_billing_report_as_csv(self, report_type):
        """Save the current billing report as a CSV file"""
        # Get column headings
        columns = self.billing_report_tree["columns"]
        headers = [self.billing_report_tree.heading(col)["text"] for col in columns]
        
        # Get data from treeview
        data = []
        for item_id in self.billing_report_tree.get_children():
            values = self.billing_report_tree.item(item_id)["values"]
            data.append(values)
        
        # Ask user for save location
        file_path = tk.filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"{report_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        
        if not file_path:
            return
        
        # Write to CSV
        try:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                writer.writerows(data)
            
            messagebox.showinfo("Success", f"Report saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save report: {str(e)}")
    
    def save_billing_report_as_pdf(self, report_type, from_date, to_date):
        """Save the current billing report as a PDF file"""
        # Get column headings
        columns = self.billing_report_tree["columns"]
        headers = [self.billing_report_tree.heading(col)["text"] for col in columns]
        
        # Get data from treeview
        data = []
        for item_id in self.billing_report_tree.get_children():
            values = self.billing_report_tree.item(item_id)["values"]
            data.append(values)
        
        # Ask user for save location
        file_path = tk.filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=f"{report_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        
        if not file_path:
            return
        
        # Create PDF
        doc = SimpleDocTemplate(
            file_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Center', alignment=1))
        styles.add(ParagraphStyle(name='Right', alignment=2))
        
        # Create content
        content = []
        
        # Add title
        content.append(Paragraph(f"<b>{report_type}</b>", styles['Heading1']))
        
        # Add date range
        content.append(Paragraph(f"Period: {from_date} to {to_date}", styles['Normal']))
        content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        
        # Add company info
        company_name = self.get_setting('company_name')
        content.append(Paragraph(f"Company: {company_name}", styles['Normal']))
        
        content.append(Spacer(1, 20))
        
        # Create table data
        table_data = [headers]
        for row in data:
            table_data.append(row)
        
        # Create table
        table = Table(table_data)
        
        # Add style to table
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        
        # Add style for total row
        if len(data) > 0 and "TOTAL" in str(data[-1]):
            style.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
            style.add('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey)
        
        table.setStyle(style)
        content.append(table)
        
        # Build PDF
        doc.build(content)
        
        messagebox.showinfo("Success", f"Report saved to {file_path}")
    
    def setup_billing_settings_tab(self):
        """Set up the billing settings tab"""
        # Create frame for settings content
        settings_content = ttk.Frame(self.billing_settings_tab, style="TFrame")
        settings_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create notebook for settings sections
        settings_notebook = ttk.Notebook(settings_content)
        settings_notebook.pack(fill=tk.BOTH, expand=True)
        
        # General settings tab
        general_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(general_tab, text="General")
        
        # Company settings tab
        company_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(company_tab, text="Company")
        
        # Invoice settings tab
        invoice_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(invoice_tab, text="Invoice")
        
        # Payment settings tab
        payment_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(payment_tab, text="Payment Methods")
        
        # Email settings tab
        email_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(email_tab, text="Email")
        
        # Setup tabs
        self.setup_general_settings_tab(general_tab)
        self.setup_company_settings_tab(company_tab)
        self.setup_invoice_settings_tab(invoice_tab)
        self.setup_payment_settings_tab(payment_tab)
        self.setup_email_settings_tab(email_tab)
    
    def setup_general_settings_tab(self, parent):
        """Set up the general settings tab"""
        # Create frame for general settings content
        general_content = ttk.Frame(parent, padding="20 20 20 20")
        general_content.pack(fill=tk.BOTH, expand=True)
        
        # Currency settings
        currency_frame = ttk.LabelFrame(general_content, text="Currency Settings")
        currency_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(currency_frame, text="Currency Symbol:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        
        currency_symbol_var = tk.StringVar(value=self.get_setting('currency_symbol'))
        currency_symbol_entry = ttk.Entry(currency_frame, textvariable=currency_symbol_var, width=10)
        currency_symbol_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Tax settings
        tax_frame = ttk.LabelFrame(general_content, text="Tax Settings")
        tax_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(tax_frame, text="Default Tax Rate (%):").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        
        default_tax_rate_var = tk.StringVar(value=self.get_setting('default_tax_rate'))
        default_tax_rate_entry = ttk.Entry(tax_frame, textvariable=default_tax_rate_var, width=10)
        default_tax_rate_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Save button
        save_button = ttk.Button(general_content, text="Save Settings", 
                                command=lambda: self.save_general_settings(
                                    currency_symbol_var.get(),
                                    default_tax_rate_var.get()
                                ))
        save_button.pack(pady=20)
    
    def save_general_settings(self, currency_symbol, default_tax_rate):
        """Save general settings to the database"""
        # Validate inputs
        if not currency_symbol:
            messagebox.showerror("Error", "Currency symbol is required")
            return
        
        try:
            tax_rate = float(default_tax_rate)
            if tax_rate < 0:
                raise ValueError("Tax rate must be a non-negative number")
        except ValueError:
            messagebox.showerror("Error", "Tax rate must be a valid number")
            return
        
        # Save to database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE billing_settings SET setting_value = ? WHERE setting_name = ?", 
                          (currency_symbol, 'currency_symbol'))
            
            cursor.execute("UPDATE billing_settings SET setting_value = ? WHERE setting_name = ?", 
                          (default_tax_rate, 'default_tax_rate'))
            
            conn.commit()
            messagebox.showinfo("Success", "Settings saved successfully")
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
        
        finally:
            conn.close()
    
    def setup_company_settings_tab(self, parent):
        """Set up the company settings tab"""
        # Create frame for company settings content
        company_content = ttk.Frame(parent, padding="20 20 20 20")
        company_content.pack(fill=tk.BOTH, expand=True)
        
        # Company information
        company_frame = ttk.LabelFrame(company_content, text="Company Information")
        company_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Company name
        ttk.Label(company_frame, text="Company Name:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        
        company_name_var = tk.StringVar(value=self.get_setting('company_name'))
        company_name_entry = ttk.Entry(company_frame, textvariable=company_name_var, width=40)
        company_name_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Address
        ttk.Label(company_frame, text="Address:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        
        company_address_var = tk.StringVar(value=self.get_setting('company_address'))
        company_address_entry = ttk.Entry(company_frame, textvariable=company_address_var, width=40)
        company_address_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Phone
        ttk.Label(company_frame, text="Phone:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        
        company_phone_var = tk.StringVar(value=self.get_setting('company_phone'))
        company_phone_entry = ttk.Entry(company_frame, textvariable=company_phone_var, width=40)
        company_phone_entry.grid(row=2, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Email
        ttk.Label(company_frame, text="Email:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)
        
        company_email_var = tk.StringVar(value=self.get_setting('company_email'))
        company_email_entry = ttk.Entry(company_frame, textvariable=company_email_var, width=40)
        company_email_entry.grid(row=3, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Website
        ttk.Label(company_frame, text="Website:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=10)
        
        company_website_var = tk.StringVar(value=self.get_setting('company_website'))
        company_website_entry = ttk.Entry(company_frame, textvariable=company_website_var, width=40)
        company_website_entry.grid(row=4, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Tax ID
        ttk.Label(company_frame, text="Tax ID:").grid(row=5, column=0, sticky=tk.W, padx=10, pady=10)
        
        company_tax_id_var = tk.StringVar(value=self.get_setting('company_tax_id'))
        company_tax_id_entry = ttk.Entry(company_frame, textvariable=company_tax_id_var, width=40)
        company_tax_id_entry.grid(row=5, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Save button
        save_button = ttk.Button(company_content, text="Save Settings", 
                                command=lambda: self.save_company_settings(
                                    company_name_var.get(),
                                    company_address_var.get(),
                                    company_phone_var.get(),
                                    company_email_var.get(),
                                    company_website_var.get(),
                                    company_tax_id_var.get()
                                ))
        save_button.pack(pady=20)
    
    def save_company_settings(self, name, address, phone, email, website, tax_id):
        """Save company settings to the database"""
        # Validate inputs
        if not name:
            messagebox.showerror("Error", "Company name is required")
            return
        
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Error", "Invalid email format")
            return
        
        # Save to database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE billing_settings SET setting_value = ? WHERE setting_name = ?", 
                          (name, 'company_name'))
            
            cursor.execute("UPDATE billing_settings SET setting_value = ? WHERE setting_name = ?", 
                          (address, 'company_address'))
            
            cursor.execute("UPDATE billing_settings SET setting_value = ? WHERE setting_name = ?", 
                          (phone, 'company_phone'))
            
            cursor.execute("UPDATE billing_settings SET setting_value = ? WHERE setting_name = ?", 
                          (email, 'company_email'))
            
            cursor.execute("UPDATE billing_settings SET setting_value = ? WHERE setting_name = ?", 
                          (website, 'company_website'))
            
            cursor.execute("UPDATE billing_settings SET setting_value = ? WHERE setting_name = ?", 
                          (tax_id, 'company_tax_id'))
            
            conn.commit()
            messagebox.showinfo("Success", "Company information saved successfully")
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
        
        finally:
            conn.close()
    
    def setup_invoice_settings_tab(self, parent):
        """Set up the invoice settings tab"""
        # Create frame for invoice settings content
        invoice_content = ttk.Frame(parent, padding="20 20 20 20")
        invoice_content.pack(fill=tk.BOTH, expand=True)
        
        # Invoice numbering
        numbering_frame = ttk.LabelFrame(invoice_content, text="Invoice Numbering")
        numbering_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Invoice prefix
        ttk.Label(numbering_frame, text="Invoice Prefix:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        
        invoice_prefix_var = tk.StringVar(value=self.get_setting('invoice_prefix'))
        invoice_prefix_entry = ttk.Entry(numbering_frame, textvariable=invoice_prefix_var, width=20)
        invoice_prefix_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Starting number
        ttk.Label(numbering_frame, text="Next Invoice Number:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        
        # Get the highest invoice number from the database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT invoice_number FROM invoices ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Extract the numeric part of the last invoice number
            last_number = result[0]
            prefix = self.get_setting('invoice_prefix')
            if prefix and last_number.startswith(prefix):
                last_number = last_number[len(prefix):]
            
            try:
                # Increment the number
                next_number = int(last_number) + 1
            except ValueError:
                # If conversion fails, use the starting number
                next_number = int(self.get_setting('invoice_starting_number'))
        else:
            # No invoices yet, use the starting number
            next_number = int(self.get_setting('invoice_starting_number'))
        
        invoice_number_var = tk.StringVar(value=str(next_number))
        invoice_number_entry = ttk.Entry(numbering_frame, textvariable=invoice_number_var, width=20)
        invoice_number_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Due date settings
        due_frame = ttk.LabelFrame(invoice_content, text="Due Date Settings")
        due_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Default due days
        ttk.Label(due_frame, text="Default Due Days:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        
        due_days_var = tk.StringVar(value=self.get_setting('default_due_days'))
        due_days_entry = ttk.Entry(due_frame, textvariable=due_days_var, width=10)
        due_days_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Reminder days
        ttk.Label(due_frame, text="Reminder Days Before Due:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        
        reminder_days_var = tk.StringVar(value=self.get_setting('reminder_days_before'))
        reminder_days_entry = ttk.Entry(due_frame, textvariable=reminder_days_var, width=20)
        reminder_days_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)
        ttk.Label(due_frame, text="(comma-separated, e.g. 3,7,14)").grid(row=1, column=2, sticky=tk.W, padx=10, pady=10)
        
        # Save button
        save_button = ttk.Button(invoice_content, text="Save Settings", 
                                command=lambda: self.save_invoice_settings(
                                    invoice_prefix_var.get(),
                                    invoice_number_var.get(),
                                    due_days_var.get(),
                                    reminder_days_var.get()
                                ))
        save_button.pack(pady=20)
    
    def save_invoice_settings(self, prefix, starting_number, due_days, reminder_days):
        """Save invoice settings to the database"""
        # Validate inputs
        try:
            starting_number = int(starting_number)
            if starting_number < 1:
                raise ValueError("Starting number must be a positive integer")
        except ValueError:
            messagebox.showerror("Error", "Starting number must be a valid positive integer")
            return
        
        try:
            due_days = int(due_days)
            if due_days < 0:
                raise ValueError("Due days must be a non-negative integer")
        except ValueError:
            messagebox.showerror("Error", "Due days must be a valid non-negative integer")
            return
        
        # Validate reminder days format (comma-separated integers)
        if reminder_days:
            try:
                for day in reminder_days.split(','):
                    day_int = int(day.strip())
                    if day_int < 0:
                        raise ValueError("Reminder days must be non-negative integers")
            except ValueError:
                messagebox.showerror("Error", "Reminder days must be comma-separated non-negative integers")
                return
        
        # Save to database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE billing_settings SET setting_value = ? WHERE setting_name = ?", 
                          (prefix, 'invoice_prefix'))
            
            cursor.execute("UPDATE billing_settings SET setting_value = ? WHERE setting_name = ?", 
                          (str(starting_number), 'invoice_starting_number'))
            
            cursor.execute("UPDATE billing_settings SET setting_value = ? WHERE setting_name = ?", 
                          (str(due_days), 'default_due_days'))
            
            cursor.execute("UPDATE billing_settings SET setting_value = ? WHERE setting_name = ?", 
                          (reminder_days, 'reminder_days_before'))
            
            conn.commit()
            messagebox.showinfo("Success", "Invoice settings saved successfully")
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
        
        finally:
            conn.close()
    
    def setup_payment_settings_tab(self, parent):
        """Set up the payment methods settings tab"""
        # Create frame for payment settings content
        payment_content = ttk.Frame(parent, padding="20 20 20 20")
        payment_content.pack(fill=tk.BOTH, expand=True)
        
        # Payment methods
        methods_frame = ttk.LabelFrame(payment_content, text="Payment Methods")
        methods_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create treeview for payment methods
        columns = ("id", "name", "active")
        self.payment_methods_tree = ttk.Treeview(methods_frame, columns=columns, show="headings", height=10)
        
        # Define headings
        self.payment_methods_tree.heading("id", text="ID")
        self.payment_methods_tree.heading("name", text="Payment Method")
        self.payment_methods_tree.heading("active", text="Active")
        
        # Define columns
        self.payment_methods_tree.column("id", width=50, anchor=tk.CENTER)
        self.payment_methods_tree.column("name", width=200)
        self.payment_methods_tree.column("active", width=100, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(methods_frame, orient=tk.VERTICAL, command=self.payment_methods_tree.yview)
        self.payment_methods_tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        self.payment_methods_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Load payment methods
        self.load_payment_methods()
        
        # Action buttons
        button_frame = ttk.Frame(payment_content)
        button_frame.pack(fill=tk.X)
        
        add_button = ttk.Button(button_frame, text="Add Method", 
                               command=self.show_add_payment_method_dialog)
        add_button.pack(side=tk.LEFT, padx=(0, 10))
        
        edit_button = ttk.Button(button_frame, text="Edit Method", 
                                command=self.show_edit_payment_method_dialog)
        edit_button.pack(side=tk.LEFT, padx=(0, 10))
        
        toggle_button = ttk.Button(button_frame, text="Toggle Active", 
                                  command=self.toggle_payment_method_active)
        toggle_button.pack(side=tk.LEFT, padx=(0, 10))
        
        delete_button = ttk.Button(button_frame, text="Delete Method", 
                                  style="Danger.TButton", command=self.delete_payment_method)
        delete_button.pack(side=tk.LEFT)
    
    def load_payment_methods(self):
        """Load payment methods into the treeview"""
        # Clear existing items
        for item in self.payment_methods_tree.get_children():
            self.payment_methods_tree.delete(item)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, is_active FROM payment_gateways ORDER BY name")
        methods = cursor.fetchall()
        conn.close()
        
        # Insert into treeview
        for method in methods:
            method_id, name, is_active = method
            
            # Format active status
            active_status = "Yes" if is_active else "No"
            
            # Determine tag based on active status
            tag = 'active' if is_active else 'inactive'
            
            self.payment_methods_tree.insert('', tk.END, values=(
                method_id, name, active_status
            ), tags=(tag,))
        
        # Configure tags
        self.payment_methods_tree.tag_configure('active', background='#d4edda')
        self.payment_methods_tree.tag_configure('inactive', background='#f8d7da')
    
    def show_add_payment_method_dialog(self):
        """Show dialog to add a new payment method"""
        # Create a new top-level window
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add Payment Method")
        dialog.geometry("400x200")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create form frame
        form_frame = ttk.Frame(dialog, padding="20 20 20 20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields
        ttk.Label(form_frame, text="Method Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Active status
        active_var = tk.BooleanVar(value=True)
        active_check = ttk.Checkbutton(form_frame, text="Active", variable=active_var)
        active_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 20))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=2, column=0, columnspan=2)
        
        save_button = ttk.Button(button_frame, text="Save", 
                                command=lambda: self.save_payment_method(
                                    name_entry.get(),
                                    active_var.get(),
                                    dialog
                                ))
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT)
    
    def save_payment_method(self, name, is_active, dialog):
        """Save a new payment method to the database"""
        # Validate inputs
        if not name:
            messagebox.showerror("Error", "Method name is required", parent=dialog)
            return
        
        # Check if method already exists
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM payment_gateways WHERE name = ?", (name,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            messagebox.showerror("Error", "Payment method already exists", parent=dialog)
            return
        
        # Insert into database
        try:
            cursor.execute('''
            INSERT INTO payment_gateways (name, api_key, secret_key, is_active)
            VALUES (?, ?, ?, ?)
            ''', (name, "", "", is_active))
            
            conn.commit()
            messagebox.showinfo("Success", "Payment method added successfully", parent=dialog)
            
            # Close dialog and refresh payment methods
            dialog.destroy()
            self.load_payment_methods()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to add payment method: {str(e)}", parent=dialog)
        
        finally:
            conn.close()
    
    def show_edit_payment_method_dialog(self):
        """Show dialog to edit an existing payment method"""
        # Get selected method
        selected = self.payment_methods_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a payment method to edit")
            return
        
        # Get method ID
        method_id = self.payment_methods_tree.item(selected[0], 'values')[0]
        
        # Get method data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, is_active FROM payment_gateways WHERE id = ?", (method_id,))
        method = cursor.fetchone()
        conn.close()
        
        if not method:
            messagebox.showerror("Error", "Payment method not found")
            return
        
        name, is_active = method
        
        # Create a new top-level window
        dialog = tk.Toplevel(self.parent)
        dialog.title("Edit Payment Method")
        dialog.geometry("400x200")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create form frame
        form_frame = ttk.Frame(dialog, padding="20 20 20 20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields
        ttk.Label(form_frame, text="Method Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.insert(0, name)
        name_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Active status
        active_var = tk.BooleanVar(value=is_active)
        active_check = ttk.Checkbutton(form_frame, text="Active", variable=active_var)
        active_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 20))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=2, column=0, columnspan=2)
        
        save_button = ttk.Button(button_frame, text="Save", 
                                command=lambda: self.update_payment_method(
                                    method_id,
                                    name_entry.get(),
                                    active_var.get(),
                                    dialog
                                ))
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT)
    
    def update_payment_method(self, method_id, name, is_active, dialog):
        """Update an existing payment method in the database"""
        # Validate inputs
        if not name:
            messagebox.showerror("Error", "Method name is required", parent=dialog)
            return
        
        # Update in database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE payment_gateways
            SET name = ?, is_active = ?
            WHERE id = ?
            ''', (name, is_active, method_id))
            
            conn.commit()
            messagebox.showinfo("Success", "Payment method updated successfully", parent=dialog)
            
            # Close dialog and refresh payment methods
            dialog.destroy()
            self.load_payment_methods()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to update payment method: {str(e)}")
        
        finally:
            conn.close()
    
    def toggle_payment_method_active(self):
        """Toggle the active status of a payment method"""
        # Get selected method
        selected = self.payment_methods_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a payment method to toggle")
            return
        
        # Get method ID and active status
        method_id = self.payment_methods_tree.item(selected[0], 'values')[0]
        active_status = self.payment_methods_tree.item(selected[0], 'values')[2]
        
        # Determine new active status
        is_active = (active_status == "No")
        
        # Update in database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE payment_gateways SET is_active = ? WHERE id = ?", (is_active, method_id))
            conn.commit()
            messagebox.showinfo("Success", "Payment method status updated successfully")
            
            # Refresh payment methods
            self.load_payment_methods()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to update payment method status: {str(e)}")
        
        finally:
            conn.close()
    
    def delete_payment_method(self):
        """Delete a payment method"""
        # Get selected method
        selected = self.payment_methods_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a payment method to delete")
            return
        
        # Get method ID and name
        method_values = self.payment_methods_tree.item(selected[0], 'values')
        method_id = method_values[0]
        method_name = method_values[1]
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Delete", 
                                     f"Are you sure you want to delete payment method '{method_name}'?\n\nThis action cannot be undone.")
        if not confirm:
            return
        
        # Delete from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM payment_gateways WHERE id = ?", (method_id,))
            conn.commit()
            messagebox.showinfo("Success", f"Payment method '{method_name}' deleted successfully")
            
            # Refresh payment methods
            self.load_payment_methods()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to delete payment method: {str(e)}")
        
        finally:
            conn.close()
    
    def setup_email_settings_tab(self, parent):
        """Set up the email settings tab"""
        # Create frame for email settings content
        email_content = ttk.Frame(parent, padding="20 20 20 20")
        email_content.pack(fill=tk.BOTH, expand=True)
        
        # SMTP settings
        smtp_frame = ttk.LabelFrame(email_content, text="SMTP Settings")
        smtp_frame.pack(fill=tk.X, pady=(0, 20))
        
        # SMTP server
        ttk.Label(smtp_frame, text="SMTP Server:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        
        smtp_server_var = tk.StringVar(value=self.get_setting('smtp_server'))
        smtp_server_entry = ttk.Entry(smtp_frame, textvariable=smtp_server_var, width=40)
        smtp_server_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)
        
        # SMTP port
        ttk.Label(smtp_frame, text="SMTP Port:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        
        smtp_port_var = tk.StringVar(value=self.get_setting('smtp_port'))
        smtp_port_entry = ttk.Entry(smtp_frame, textvariable=smtp_port_var, width=10)
        smtp_port_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)
        
        # SMTP username
        ttk.Label(smtp_frame, text="SMTP Username:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        
        smtp_username_var = tk.StringVar(value=self.get_setting('smtp_username'))
        smtp_username_entry = ttk.Entry(smtp_frame, textvariable=smtp_username_var, width=40)
        smtp_username_entry.grid(row=2, column=1, sticky=tk.W, padx=10, pady=10)
        
        # SMTP password
        ttk.Label(smtp_frame, text="SMTP Password:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)
        
        smtp_password_var = tk.StringVar(value=self.get_setting('smtp_password'))
        smtp_password_entry = ttk.Entry(smtp_frame, textvariable=smtp_password_var, width=40, show="*")
        smtp_password_entry.grid(row=3, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Test email button
        test_button = ttk.Button(smtp_frame, text="Send Test Email", 
                                command=lambda: self.send_test_email(
                                    smtp_server_var.get(),
                                    smtp_port_var.get(),
                                    smtp_username_var.get(),
                                    smtp_password_var.get()
                                ))
        test_button.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Save button
        save_button = ttk.Button(email_content, text="Save Settings", 
                                command=lambda: self.save_email_settings(
                                    smtp_server_var.get(),
                                    smtp_port_var.get(),
                                    smtp_username_var.get(),
                                    smtp_password_var.get()
                                ))
        save_button.pack(pady=20)
    
    def save_email_settings(self, server, port, username, password):
        """Save email settings to the database"""
        # Validate inputs
        if not server:
            messagebox.showerror("Error", "SMTP server is required")
            return
        
        try:
            port = int(port)
            if port < 1 or port > 65535:
                raise ValueError("Port must be a valid port number (1-65535)")
        except ValueError:
            messagebox.showerror("Error", "SMTP port must be a valid number between 1 and 65535")
            return
        
        if not username:
            messagebox.showerror("Error", "SMTP username is required")
            return
        
        if not password:
            messagebox.showerror("Error", "SMTP password is required")
            return
        
        # Save to database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE billing_settings SET setting_value = ? WHERE setting_name = ?", 
                          (server, 'smtp_server'))
            
            cursor.execute("UPDATE billing_settings SET setting_value = ? WHERE setting_name = ?", 
                          (str(port), 'smtp_port'))
            
            cursor.execute("UPDATE billing_settings SET setting_value = ? WHERE setting_name = ?", 
                          (username, 'smtp_username'))
            
            cursor.execute("UPDATE billing_settings SET setting_value = ? WHERE setting_name = ?", 
                          (password, 'smtp_password'))
            
            conn.commit()
            messagebox.showinfo("Success", "Email settings saved successfully")
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
        
        finally:
            conn.close()
    
    def send_test_email(self, server, port, username, password):
        """Send a test email to verify SMTP settings"""
        # Validate inputs
        if not server:
            messagebox.showerror("Error", "SMTP server is required")
            return
        
        try:
            port = int(port)
            if port < 1 or port > 65535:
                raise ValueError("Port must be a valid port number (1-65535)")
        except ValueError:
            messagebox.showerror("Error", "SMTP port must be a valid number between 1 and 65535")
            return
        
        if not username:
            messagebox.showerror("Error", "SMTP username is required")
            return
        
        if not password:
            messagebox.showerror("Error", "SMTP password is required")
            return
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = username
        msg['Subject'] = "Test Email from Inventory System"
        msg.attach(MIMEText("This is a test email to verify your SMTP settings.", 'plain'))
        
        # Send email in a separate thread
        def send_email_thread():
            try:
                # Connect to SMTP server
                server_obj = smtplib.SMTP(server, port)
                server_obj.starttls()
                
                # Login
                server_obj.login(username, password)
                
                # Send email
                server_obj.send_message(msg)
                server_obj.quit()
                
                # Show success message
                messagebox.showinfo("Success", "Test email sent successfully!")
                
            except Exception as e:
                # Show error message
                messagebox.showerror("Error", f"Failed to send test email: {str(e)}")
        
        # Start the email sending in a separate thread
        email_thread = threading.Thread(target=send_email_thread)
        email_thread.daemon = True
        email_thread.start()
    
    def get_setting(self, setting_name):
        """Get a setting value from the database"""
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT setting_value FROM billing_settings WHERE setting_name = ?", (setting_name,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            return ""

if __name__ == '__main__':
    # Create a dummy root window for testing
    root = tk.Tk()
    root.title("Billing System Test")
    root.geometry("1200x800")
    
    # Dummy current user
    current_user = {
        "id": 1,
        "username": "admin",
        "role": "admin"
    }
    
    # Create a notebook for tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Billing tab
    billing_tab = ttk.Frame(notebook)
    notebook.add(billing_tab, text="Billing")
    
    # Initialize billing system
    billing_system = BillingSystem(billing_tab, current_user)
    
    root.mainloop()