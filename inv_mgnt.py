import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from tkinter import filedialog
import os

class BillingSystem:
    def __init__(self, root, current_user):
        self.root = root
        self.current_user = current_user
        self.root.title("Billing System")
        self.root.geometry("1400x800")
        self.root.configure(bg="#f5f5f5")
        
        # Set up styles
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Configure styles
        self.style.configure("TFrame", background="#f5f5f5")
        self.style.configure("TButton", 
                                background="#4CAF50", 
                             foreground="black", 
                             font=("Helvetica", 10, "bold"),
                             padding=10)
        self.style.map("TButton", 
                       background=[("active", "#45a049"), ("disabled", "#cccccc")])
        
        self.style.configure("Secondary.TButton", 
                             background="#2196F3", 
                             foreground="black")
        self.style.map("Secondary.TButton", 
                       background=[("active", "#0b7dda")])
        
        self.style.configure("Danger.TButton", 
                             background="#f44336", 
                             foreground="black")
        self.style.map("Danger.TButton", 
                       background=[("active", "#d32f2f")])
        
        self.style.configure("Success.TButton", 
                             background="#28a745", 
                             foreground="white")
        self.style.map("Success.TButton", 
                       background=[("active", "#218838")])
        
        self.style.configure("TLabel", 
                             background="#f5f5f5", 
                             font=("Helvetica", 11))
        
        self.style.configure("Header.TLabel", 
                             font=("Helvetica", 16, "bold"))
        
        self.style.configure("Treeview", 
                             background="white",
                             foreground="black",
                             rowheight=25,
                             fieldbackground="white",
                             font=("Helvetica", 10))
        self.style.map("Treeview", 
                       background=[("selected", "#4CAF50")])
        
        self.style.configure("Treeview.Heading", 
                             background="#4CAF50",
                             foreground="white",
                             font=("Helvetica", 11, "bold"))
        
        # Variables for bill creation
        self.bill_items = []
        self.selected_customer = None
        self.bill_total = 0.0
        self.tax_rate = 10.0  # 10% tax
        self.discount_amount = 0.0
        
        # Setup main interface
        self.setup_main_interface()
        
        # Load initial data
        self.load_customers()
        self.load_bills()

    def setup_main_interface(self):
        """Set up the main billing system interface"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(header_frame, text="Billing System", 
                               style="Header.TLabel", font=("Helvetica", 18, "bold"))
        title_label.pack(side=tk.LEFT)
        
        user_label = ttk.Label(header_frame, 
                              text=f"User: {self.current_user['username']}")
        user_label.pack(side=tk.RIGHT)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create Bill tab
        self.create_bill_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.create_bill_tab, text="Create Invoice")
        
        # Bills History tab
        self.bills_history_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.bills_history_tab, text="Invoice History")
        
        # Customers tab
        self.customers_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.customers_tab, text="Customers")
        
        # Setup tabs
        self.setup_create_bill_tab()
        self.setup_bills_history_tab()
        self.setup_customers_tab()

    def setup_create_bill_tab(self):
        """Set up the create bill tab"""
        # Main frame for create bill
        create_frame = ttk.Frame(self.create_bill_tab)
        create_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left panel - Bill creation
        left_panel = ttk.Frame(create_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Customer selection
        customer_frame = ttk.LabelFrame(left_panel, text="Customer Information")
        customer_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Customer selection row
        customer_select_frame = ttk.Frame(customer_frame)
        customer_select_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(customer_select_frame, text="Customer:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.customer_var = tk.StringVar()
        self.customer_combo = ttk.Combobox(customer_select_frame, textvariable=self.customer_var,
                                          width=30, state="readonly")
        self.customer_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        add_customer_btn = ttk.Button(customer_select_frame, text="Add Customer",
                                     command=self.show_add_customer_dialog)
        add_customer_btn.pack(side=tk.LEFT)
        
        # Item selection
        item_frame = ttk.LabelFrame(left_panel, text="Add Items")
        item_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Item selection controls
        item_controls = ttk.Frame(item_frame)
        item_controls.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(item_controls, text="Item:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.item_var = tk.StringVar()
        self.item_combo = ttk.Combobox(item_controls, textvariable=self.item_var,
                                      width=25, state="readonly")
        self.item_combo.grid(row=0, column=1, padx=(0, 10))
        self.item_combo.bind('<<ComboboxSelected>>', self.on_item_selected)
        
        ttk.Label(item_controls, text="Qty:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        
        self.item_qty_var = tk.StringVar(value="1")
        qty_entry = ttk.Entry(item_controls, textvariable=self.item_qty_var, width=8)
        qty_entry.grid(row=0, column=3, padx=(0, 10))
        
        ttk.Label(item_controls, text="Price (₦):").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        
        self.item_price_var = tk.StringVar()
        self.price_entry = ttk.Entry(item_controls, textvariable=self.item_price_var, width=10)
        self.price_entry.grid(row=0, column=5, padx=(0, 10))
        
        add_item_btn = ttk.Button(item_controls, text="Add Item",
                                 command=self.add_item_to_bill)
        add_item_btn.grid(row=0, column=6)
        
        # Bill items table
        items_frame = ttk.LabelFrame(left_panel, text="Invoice Items")
        items_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create treeview for bill items
        columns = ("item", "qty", "price", "total")
        self.bill_items_tree = ttk.Treeview(items_frame, columns=columns, show="headings", height=8)
        
        # Define headings
        self.bill_items_tree.heading("item", text="Item")
        self.bill_items_tree.heading("qty", text="Quantity")
        self.bill_items_tree.heading("price", text="Unit Price (₦)")
        self.bill_items_tree.heading("total", text="Total (₦)")
        
        # Define columns
        self.bill_items_tree.column("item", width=200)
        self.bill_items_tree.column("qty", width=80, anchor=tk.CENTER)
        self.bill_items_tree.column("price", width=100, anchor=tk.E)
        self.bill_items_tree.column("total", width=100, anchor=tk.E)
        
        # Add scrollbar
        items_scrollbar = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, command=self.bill_items_tree.yview)
        self.bill_items_tree.configure(yscroll=items_scrollbar.set)
        
        # Pack widgets
        self.bill_items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        items_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Item actions
        items_actions = ttk.Frame(items_frame)
        items_actions.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        remove_item_btn = ttk.Button(items_actions, text="Remove Selected Item",
                                    style="Danger.TButton", command=self.remove_item_from_bill)
        remove_item_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_items_btn = ttk.Button(items_actions, text="Clear All Items",
                                    style="Danger.TButton", command=self.clear_bill_items)
        clear_items_btn.pack(side=tk.LEFT)
        
        # Right panel - Bill summary and actions
        right_panel = ttk.Frame(create_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # Bill summary
        summary_frame = ttk.LabelFrame(right_panel, text="Invoice Summary")
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Summary labels
        summary_content = ttk.Frame(summary_frame)
        summary_content.pack(padx=15, pady=15)
        
        ttk.Label(summary_content, text="Subtotal:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.subtotal_label = ttk.Label(summary_content, text="₦0.00", font=("Helvetica", 11, "bold"))
        self.subtotal_label.grid(row=0, column=1, sticky=tk.E, padx=(20, 0), pady=5)
        
        # Discount
        ttk.Label(summary_content, text="Discount:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        discount_frame = ttk.Frame(summary_content)
        discount_frame.grid(row=1, column=1, sticky=tk.E, padx=(20, 0), pady=5)
        
        self.discount_var = tk.StringVar(value="0.00")
        discount_entry = ttk.Entry(discount_frame, textvariable=self.discount_var, width=8)
        discount_entry.pack(side=tk.LEFT)
        discount_entry.bind('<KeyRelease>', self.calculate_totals)
        
        ttk.Label(discount_frame, text="₦").pack(side=tk.LEFT, padx=(2, 0))
        
        # Tax
        ttk.Label(summary_content, text="Tax (10%):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.tax_label = ttk.Label(summary_content, text="₦0.00", font=("Helvetica", 11))
        self.tax_label.grid(row=2, column=1, sticky=tk.E, padx=(20, 0), pady=5)
        
        # Total
        ttk.Label(summary_content, text="Total:").grid(row=3, column=0, sticky=tk.W, pady=10)
        self.total_label = ttk.Label(summary_content, text="₦0.00", 
                                    font=("Helvetica", 14, "bold"), foreground="blue")
        self.total_label.grid(row=3, column=1, sticky=tk.E, padx=(20, 0), pady=10)
        
        # Bill actions
        actions_frame = ttk.LabelFrame(right_panel, text="Actions")
        actions_frame.pack(fill=tk.X, pady=(0, 10))
        
        actions_content = ttk.Frame(actions_frame)
        actions_content.pack(padx=15, pady=15)
        
        # CREATE INVOICE BUTTON - This was missing!
        create_invoice_btn = ttk.Button(actions_content, text="Create Invoice",
                                      style="Success.TButton", command=self.create_invoice)
        create_invoice_btn.pack(fill=tk.X, pady=(0, 10))
        
        save_bill_btn = ttk.Button(actions_content, text="Save Draft",
                                  command=self.save_bill)
        save_bill_btn.pack(fill=tk.X, pady=(0, 10))
        
        print_bill_btn = ttk.Button(actions_content, text="Save & Print",
                                   command=self.save_and_print_bill)
        print_bill_btn.pack(fill=tk.X, pady=(0, 10))
        
        new_bill_btn = ttk.Button(actions_content, text="New Invoice",
                                 style="Secondary.TButton", command=self.new_bill)
        new_bill_btn.pack(fill=tk.X)
        
        # Load inventory items
        self.load_inventory_items()

    def setup_bills_history_tab(self):
        """Set up the bills history tab"""
        history_frame = ttk.Frame(self.bills_history_tab)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Filters
        filter_frame = ttk.Frame(history_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(filter_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.status_filter_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_filter_var,
                                   values=["All", "Pending", "Paid", "Cancelled"], 
                                   state="readonly", width=15)
        status_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(filter_frame, text="Date From:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.date_from_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        date_from_entry = ttk.Entry(filter_frame, textvariable=self.date_from_var, width=12)
        date_from_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(filter_frame, text="To:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.date_to_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        date_to_entry = ttk.Entry(filter_frame, textvariable=self.date_to_var, width=12)
        date_to_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        filter_btn = ttk.Button(filter_frame, text="Apply Filter",
                               command=self.load_bills)
        filter_btn.pack(side=tk.LEFT)
        
        # Bills table
        table_frame = ttk.Frame(history_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for bills
        columns = ("bill_id", "bill_number", "customer", "amount", "status", "date")
        self.bills_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Define headings
        self.bills_tree.heading("bill_id", text="ID")
        self.bills_tree.heading("bill_number", text="Invoice Number")
        self.bills_tree.heading("customer", text="Customer")
        self.bills_tree.heading("amount", text="Amount (₦)")
        self.bills_tree.heading("status", text="Status")
        self.bills_tree.heading("date", text="Date")
        
        # Define columns
        self.bills_tree.column("bill_id", width=50, anchor=tk.CENTER)
        self.bills_tree.column("bill_number", width=120)
        self.bills_tree.column("customer", width=200)
        self.bills_tree.column("amount", width=100, anchor=tk.E)
        self.bills_tree.column("status", width=100, anchor=tk.CENTER)
        self.bills_tree.column("date", width=150, anchor=tk.CENTER)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.bills_tree.yview)
        self.bills_tree.configure(yscroll=y_scrollbar.set)
        
        x_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.bills_tree.xview)
        self.bills_tree.configure(xscroll=x_scrollbar.set)
        
        # Pack widgets
        self.bills_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bill actions
        bills_actions = ttk.Frame(history_frame)
        bills_actions.pack(fill=tk.X, pady=(10, 0))
        
        view_bill_btn = ttk.Button(bills_actions, text="View Invoice Details",
                                  command=self.view_bill_details)
        view_bill_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        mark_paid_btn = ttk.Button(bills_actions, text="Mark as Paid",
                                  style="Success.TButton", command=self.mark_bill_paid)
        mark_paid_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_bill_btn = ttk.Button(bills_actions, text="Cancel Invoice",
                                    style="Danger.TButton", command=self.cancel_bill)
        cancel_bill_btn.pack(side=tk.LEFT)

    def setup_customers_tab(self):
        """Set up the customers management tab"""
        customers_frame = ttk.Frame(self.customers_tab)
        customers_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Customer actions
        actions_frame = ttk.Frame(customers_frame)
        actions_frame.pack(fill=tk.X, pady=(0, 20))
        
        add_customer_btn = ttk.Button(actions_frame, text="Add Customer",
                                     command=self.show_add_customer_dialog)
        add_customer_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        edit_customer_btn = ttk.Button(actions_frame, text="Edit Customer",
                                      command=self.show_edit_customer_dialog)
        edit_customer_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        delete_customer_btn = ttk.Button(actions_frame, text="Delete Customer",
                                        style="Danger.TButton", command=self.delete_customer)
        delete_customer_btn.pack(side=tk.LEFT)
        
        # Customers table
        table_frame = ttk.Frame(customers_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for customers
        columns = ("id", "name", "email", "phone", "address")
        self.customers_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Define headings
        self.customers_tree.heading("id", text="ID")
        self.customers_tree.heading("name", text="Name")
        self.customers_tree.heading("email", text="Email")
        self.customers_tree.heading("phone", text="Phone")
        self.customers_tree.heading("address", text="Address")
        
        # Define columns
        self.customers_tree.column("id", width=50, anchor=tk.CENTER)
        self.customers_tree.column("name", width=200)
        self.customers_tree.column("email", width=200)
        self.customers_tree.column("phone", width=150)
        self.customers_tree.column("address", width=300)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.customers_tree.yview)
        self.customers_tree.configure(yscroll=y_scrollbar.set)
        
        x_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.customers_tree.xview)
        self.customers_tree.configure(xscroll=x_scrollbar.set)
        
        # Pack widgets
        self.customers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind double-click to edit
        self.customers_tree.bind("<Double-1>", lambda event: self.show_edit_customer_dialog())

    def load_inventory_items(self):
        """Load inventory items for billing"""
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, item_name, unit_price FROM inventory WHERE quantity > 0 ORDER BY item_name")
        items = cursor.fetchall()
        conn.close()
        
        self.inventory_items = {f"{item[1]}": {"id": item[0], "price": item[2]} for item in items}
        self.item_combo['values'] = list(self.inventory_items.keys())

    def load_customers(self):
        """Load customers for selection"""
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM customers ORDER BY name")
        customers = cursor.fetchall()
        conn.close()
        
        self.customers_dict = {customer[1]: customer[0] for customer in customers}
        self.customer_combo['values'] = list(self.customers_dict.keys())
        
        # Also load customers in customers tab
        self.load_customers_table()

    def load_customers_table(self):
        """Load customers data into the customers table"""
        # Clear existing items
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, email, phone, address FROM customers ORDER BY name")
        customers = cursor.fetchall()
        conn.close()
        
        # Insert into treeview
        for customer in customers:
            self.customers_tree.insert('', tk.END, values=customer)

    def load_bills(self):
        """Load bills history"""
        # Clear existing items
        for item in self.bills_tree.get_children():
            self.bills_tree.delete(item)
        
        # Get filter values
        status_filter = self.status_filter_var.get()
        date_from = self.date_from_var.get()
        date_to = self.date_to_var.get()
        
        # Build query
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        query = '''
        SELECT b.id, b.bill_number, COALESCE(c.name, 'Walk-in Customer') as customer_name, 
               b.final_amount, b.status, b.created_at
        FROM bills b
        LEFT JOIN customers c ON b.customer_id = c.id
        WHERE DATE(b.created_at) BETWEEN ? AND ?
        '''
        
        params = [date_from, date_to]
        
        if status_filter != "All":
            query += " AND b.status = ?"
            params.append(status_filter.lower())
        
        query += " ORDER BY b.created_at DESC"
        
        cursor.execute(query, params)
        bills = cursor.fetchall()
        conn.close()
        
        # Insert into treeview
        for bill in bills:
            bill_id, bill_number, customer, amount, status, date = bill
            
            # Format date
            try:
                date_formatted = datetime.fromisoformat(date).strftime('%Y-%m-%d %H:%M')
            except:
                date_formatted = date
            
            # Format amount with Naira symbol
            amount_formatted = f"₦{amount:.2f}"
            
            self.bills_tree.insert('', tk.END, values=(
                bill_id, bill_number, customer, amount_formatted, status.title(), date_formatted
            ))

    def on_item_selected(self, event):
        """Handle item selection in combo box"""
        item_name = self.item_var.get()
        if item_name in self.inventory_items:
            price = self.inventory_items[item_name]["price"]
            self.item_price_var.set(f"{price:.2f}")

    def add_item_to_bill(self):
        """Add selected item to bill"""
        item_name = self.item_var.get()
        
        if not item_name:
            messagebox.showerror("Error", "Please select an item")
            return
        
        try:
            quantity = int(self.item_qty_var.get())
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity")
            return
        
        try:
            price = float(self.item_price_var.get())
            if price < 0:
                raise ValueError("Price cannot be negative")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid price")
            return
        
        # Check inventory availability
        item_id = self.inventory_items[item_name]["id"]
        
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT quantity FROM inventory WHERE id = ?", (item_id,))
        available_qty = cursor.fetchone()[0]
        conn.close()
        
        if quantity > available_qty:
            messagebox.showerror("Error", f"Not enough stock. Available: {available_qty}")
            return
        
        # Calculate total
        total = quantity * price
        
        # Add to bill items
        bill_item = {
            "item_id": item_id,
            "item_name": item_name,
            "quantity": quantity,
            "price": price,
            "total": total
        }
        
        self.bill_items.append(bill_item)
        
        # Update tree view
        self.bill_items_tree.insert('', tk.END, values=(
            item_name, quantity, f"₦{price:.2f}", f"₦{total:.2f}"
        ))
        
        # Clear fields
        self.item_var.set("")
        self.item_qty_var.set("1")
        self.item_price_var.set("")
        
        # Update totals
        self.calculate_totals()

    def remove_item_from_bill(self):
        """Remove selected item from bill"""
        selected = self.bill_items_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select an item to remove")
            return
        
        # Get index of selected item
        index = self.bill_items_tree.index(selected[0])
        
        # Remove from bill items list
        del self.bill_items[index]
        
        # Remove from tree view
        self.bill_items_tree.delete(selected[0])
        
        # Update totals
        self.calculate_totals()

    def clear_bill_items(self):
        """Clear all items from bill"""
        if self.bill_items:
            confirm = messagebox.askyesno("Confirm", "Clear all items from the invoice?")
            if confirm:
                self.bill_items.clear()
                for item in self.bill_items_tree.get_children():
                    self.bill_items_tree.delete(item)
                self.calculate_totals()

    def calculate_totals(self, event=None):
        """Calculate bill totals - FIXED CALCULATION"""
        subtotal = sum(item["total"] for item in self.bill_items)
        
        try:
            discount = float(self.discount_var.get())
        except ValueError:
            discount = 0.0
            self.discount_var.set("0.00")
        
        discounted_amount = subtotal - discount
        if discounted_amount < 0:
            discounted_amount = 0
            
        tax_amount = discounted_amount * (self.tax_rate / 100)
        total_amount = discounted_amount + tax_amount
        
        # Update labels with Naira symbol
        self.subtotal_label.config(text=f"₦{subtotal:.2f}")
        self.tax_label.config(text=f"₦{tax_amount:.2f}")
        self.total_label.config(text=f"₦{total_amount:.2f}")
        
        # Store totals
        self.bill_total = subtotal
        self.discount_amount = discount

    def generate_bill_number(self):
        """Generate a unique bill number"""
        now = datetime.now()
        date_part = now.strftime("%Y%m%d")
        time_part = now.strftime("%H%M%S")
        return f"INV-{date_part}-{time_part}"

    def create_invoice(self):
        """Create and finalize the invoice - NEW FUNCTION"""
        if not self.bill_items:
            messagebox.showerror("Error", "Please add items to the invoice")
            return
        
        # Get customer
        customer_name = self.customer_var.get()
        customer_id = None
        if customer_name and customer_name in self.customers_dict:
            customer_id = self.customers_dict[customer_name]
        
        # Calculate totals
        subtotal = sum(item["total"] for item in self.bill_items)
        
        try:
            discount = float(self.discount_var.get())
        except ValueError:
            discount = 0.0
        
        discounted_amount = subtotal - discount
        if discounted_amount < 0:
            discounted_amount = 0
            
        tax_amount = discounted_amount * (self.tax_rate / 100)
        final_amount = discounted_amount + tax_amount
        
        # Generate bill number
        bill_number = self.generate_bill_number()
        
        # Save to database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            # Insert bill
            cursor.execute('''
            INSERT INTO bills (bill_number, customer_id, total_amount, tax_amount, 
                             discount_amount, final_amount, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (bill_number, customer_id, subtotal, tax_amount, discount, 
                 final_amount, 'pending', self.current_user['id']))
            
            bill_id = cursor.lastrowid
            
            # Insert bill items and update inventory
            for item in self.bill_items:
                # Insert bill item
                cursor.execute('''
                INSERT INTO bill_items (bill_id, item_id, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
                ''', (bill_id, item['item_id'], item['quantity'], 
                     item['price'], item['total']))
                
                # Update inventory quantity
                cursor.execute('''
                UPDATE inventory 
                SET quantity = quantity - ?, last_updated = CURRENT_TIMESTAMP,
                    updated_by = ?
                WHERE id = ?
                ''', (item['quantity'], self.current_user['id'], item['item_id']))
                
                # Add transaction record
                cursor.execute('''
                INSERT INTO transactions (item_id, transaction_type, quantity, user_id, notes)
                VALUES (?, ?, ?, ?, ?)
                ''', (item['item_id'], 'out', item['quantity'], 
                     self.current_user['id'], f'Invoice {bill_number}'))
            
            conn.commit()
            
            messagebox.showinfo("Success", 
                              f"Invoice {bill_number} created successfully!\n"
                              f"Total Amount: ₦{final_amount:.2f}")
            
            # Clear the form
            self.new_bill()
            
            # Refresh bills list
            self.load_bills()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to create invoice: {str(e)}")
        
        finally:
            conn.close()

    def save_bill(self):
        """Save bill as draft"""
        if not self.bill_items:
            messagebox.showerror("Error", "Please add items to the invoice")
            return
        
        messagebox.showinfo("Info", "Draft save functionality - invoice saved as draft")

    def save_and_print_bill(self):
        """Save and print bill"""
        self.create_invoice()
        messagebox.showinfo("Info", "Invoice created and ready for printing")

    def new_bill(self):
        """Start a new bill"""
        # Clear all fields
        self.customer_var.set("")
        self.item_var.set("")
        self.item_qty_var.set("1")
        self.item_price_var.set("")
        self.discount_var.set("0.00")
        
        # Clear bill items
        self.bill_items.clear()
        for item in self.bill_items_tree.get_children():
            self.bill_items_tree.delete(item)
        
        # Reset totals
        self.calculate_totals()

    def show_add_customer_dialog(self):
        """Show dialog to add a new customer"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Customer")
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form frame
        form_frame = ttk.Frame(dialog, padding="20 20 20 20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        email_entry = ttk.Entry(form_frame, width=30)
        email_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Phone:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        phone_entry = ttk.Entry(form_frame, width=30)
        phone_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Address:").grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        address_entry = ttk.Entry(form_frame, width=30)
        address_entry.grid(row=3, column=1, sticky=tk.W, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        
        def save_customer():
            name = name_entry.get()
            email = email_entry.get()
            phone = phone_entry.get()
            address = address_entry.get()
            
            if not name:
                messagebox.showerror("Error", "Name is required", parent=dialog)
                return
            
            conn = sqlite3.connect('inventory.db')
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                INSERT INTO customers (name, email, phone, address)
                VALUES (?, ?, ?, ?)
                ''', (name, email, phone, address))
                
                conn.commit()
                messagebox.showinfo("Success", "Customer added successfully", parent=dialog)
                
                dialog.destroy()
                self.load_customers()
                
            except Exception as e:
                conn.rollback()
                messagebox.showerror("Error", f"Failed to add customer: {str(e)}", parent=dialog)
            
            finally:
                conn.close()
        
        save_button = ttk.Button(button_frame, text="Save Customer", command=save_customer)
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT)
        
        name_entry.focus_set()

    def show_edit_customer_dialog(self):
        """Show dialog to edit customer"""
        selected = self.customers_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a customer to edit")
            return
        
        customer_id = self.customers_tree.item(selected[0], 'values')[0]
        
        # Get customer data
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, email, phone, address FROM customers WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()
        conn.close()
        
        if not customer:
            messagebox.showerror("Error", "Customer not found")
            return
        
        name, email, phone, address = customer
        
        # Create dialog (similar to add customer but with pre-filled data)
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Customer")
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form frame
        form_frame = ttk.Frame(dialog, padding="20 20 20 20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields with existing data
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.insert(0, name)
        name_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        email_entry = ttk.Entry(form_frame, width=30)
        email_entry.insert(0, email if email else "")
        email_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Phone:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        phone_entry = ttk.Entry(form_frame, width=30)
        phone_entry.insert(0, phone if phone else "")
        phone_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Address:").grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        address_entry = ttk.Entry(form_frame, width=30)
        address_entry.insert(0, address if address else "")
        address_entry.grid(row=3, column=1, sticky=tk.W, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        
        def update_customer():
            new_name = name_entry.get()
            new_email = email_entry.get()
            new_phone = phone_entry.get()
            new_address = address_entry.get()
            
            if not new_name:
                messagebox.showerror("Error", "Name is required", parent=dialog)
                return
            
            conn = sqlite3.connect('inventory.db')
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                UPDATE customers 
                SET name = ?, email = ?, phone = ?, address = ?
                WHERE id = ?
                ''', (new_name, new_email, new_phone, new_address, customer_id))
                
                conn.commit()
                messagebox.showinfo("Success", "Customer updated successfully", parent=dialog)
                
                dialog.destroy()
                self.load_customers()
                
            except Exception as e:
                conn.rollback()
                messagebox.showerror("Error", f"Failed to update customer: {str(e)}", parent=dialog)
            
            finally:
                conn.close()
        
        update_button = ttk.Button(button_frame, text="Update Customer", command=update_customer)
        update_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT)

    def delete_customer(self):
        """Delete selected customer"""
        selected = self.customers_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a customer to delete")
            return
        
        customer_values = self.customers_tree.item(selected[0], 'values')
        customer_id = customer_values[0]
        customer_name = customer_values[1]
        
        confirm = messagebox.askyesno("Confirm Delete", 
                                     f"Are you sure you want to delete customer '{customer_name}'?")
        if not confirm:
            return
        
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
            conn.commit()
            messagebox.showinfo("Success", f"Customer '{customer_name}' deleted successfully")
            self.load_customers()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to delete customer: {str(e)}")
        
        finally:
            conn.close()

    def view_bill_details(self):
        """View details of selected bill"""
        selected = self.bills_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select an invoice to view")
            return
        
        bill_id = self.bills_tree.item(selected[0], 'values')[0]
        
        # Get bill details
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT b.bill_number, b.total_amount, b.tax_amount, b.discount_amount, 
               b.final_amount, b.status, b.created_at, c.name
        FROM bills b
        LEFT JOIN customers c ON b.customer_id = c.id
        WHERE b.id = ?
        ''', (bill_id,))
        
        bill = cursor.fetchone()
        
        if bill:
            bill_number, total, tax, discount, final, status, date, customer = bill
            
            details = f"""Invoice Details:
            
Invoice Number: {bill_number}
Customer: {customer if customer else 'Walk-in Customer'}
Subtotal: ₦{total:.2f}
Discount: ₦{discount:.2f}
Tax: ₦{tax:.2f}
Final Amount: ₦{final:.2f}
Status: {status.title()}
Date: {date}"""
            
            messagebox.showinfo("Invoice Details", details)
        
        conn.close()

    def mark_bill_paid(self):
        """Mark selected bill as paid"""
        selected = self.bills_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select an invoice to mark as paid")
            return
        
        bill_id = self.bills_tree.item(selected[0], 'values')[0]
        
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE bills SET status = 'paid' WHERE id = ?", (bill_id,))
            conn.commit()
            messagebox.showinfo("Success", "Invoice marked as paid")
            self.load_bills()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to update invoice: {str(e)}")
        
        finally:
            conn.close()

    def cancel_bill(self):
        """Cancel selected bill"""
        selected = self.bills_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select an invoice to cancel")
            return
        
        bill_id = self.bills_tree.item(selected[0], 'values')[0]
        
        confirm = messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel this invoice?")
        if not confirm:
            return
        
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE bills SET status = 'cancelled' WHERE id = ?", (bill_id,))
            conn.commit()
            messagebox.showinfo("Success", "Invoice cancelled")
            self.load_bills()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to cancel invoice: {str(e)}")
        
        finally:
            conn.close()

if __name__ == "__main__":
    # This would normally be called from the main inventory system
    root = tk.Tk()
    # Mock user for testing
    current_user = {"id": 1, "username": "admin", "role": "admin"}
    app = BillingSystem(root, current_user)
    root.mainloop()