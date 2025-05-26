import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime
import os
import re

class InventoryManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Management System")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f5f5f5")
        
        # Set app icon and theme
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
        
        self.style.configure("TEntry", 
                             font=("Helvetica", 11))
        
        # Initialize database
        self.create_database()
        
        # Variables
        self.current_user = None
        self.search_var = tk.StringVar()
        self.category_var = tk.StringVar()
        
        # Start with login screen
        self.show_login_screen()
    
    def create_database(self):
        """Create database and tables if they don't exist"""
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create inventory table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            supplier TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER,
            FOREIGN KEY (updated_by) REFERENCES users (id)
        )
        ''')
        
        # Create transactions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            notes TEXT,
            FOREIGN KEY (item_id) REFERENCES inventory (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Insert default admin user if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                          ('admin', 'admin123', 'admin'))
        
        # Insert sample inventory data if table is empty
        cursor.execute("SELECT COUNT(*) FROM inventory")
        if cursor.fetchone()[0] == 0:
            sample_items = [
                ('Laptop', 'Dell XPS 13', 'Electronics', 15, 1200.00, 'Dell Inc.'),
                ('Desk Chair', 'Ergonomic Office Chair', 'Furniture', 25, 150.00, 'Office Supplies Co.'),
                ('Printer Paper', 'A4 80gsm 500 sheets', 'Office Supplies', 100, 5.99, 'Paper World'),
                ('Smartphone', 'iPhone 13 Pro', 'Electronics', 10, 999.00, 'Apple Inc.'),
                ('Whiteboard', '48x36 inches', 'Office Supplies', 5, 45.00, 'Office Supplies Co.'),
                ('Coffee Maker', 'Professional Espresso Machine', 'Appliances', 3, 299.99, 'Kitchen Essentials'),
                ('Monitor', '27-inch 4K Display', 'Electronics', 20, 350.00, 'Samsung Electronics'),
                ('Desk', 'Standing Desk Adjustable', 'Furniture', 8, 450.00, 'Furniture Plus'),
                ('Keyboard', 'Mechanical RGB Keyboard', 'Electronics', 30, 89.99, 'Logitech'),
                ('Mouse', 'Wireless Ergonomic Mouse', 'Electronics', 40, 45.00, 'Logitech')
            ]
            
            cursor.executemany('''
            INSERT INTO inventory (item_name, description, category, quantity, unit_price, supplier)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', sample_items)
        
        conn.commit()
        conn.close()
    
    def show_login_screen(self):
        """Display the login screen"""
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create login frame
        login_frame = ttk.Frame(self.root, padding="30 30 30 30")
        login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title
        title_label = ttk.Label(login_frame, text="Inventory Management System", 
                               style="Header.TLabel", font=("Helvetica", 20, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))
        
        # Username
        ttk.Label(login_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        self.username_entry = ttk.Entry(login_frame, width=30, font=("Helvetica", 12))
        self.username_entry.grid(row=1, column=1, pady=(0, 10), ipady=5)
        
        # Password
        ttk.Label(login_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=(0, 20))
        self.password_entry = ttk.Entry(login_frame, width=30, show="*", font=("Helvetica", 12))
        self.password_entry.grid(row=2, column=1, pady=(0, 20), ipady=5)
        
        # Login button
        login_button = ttk.Button(login_frame, text="Login", command=self.login)
        login_button.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        # Register link
        register_link = ttk.Label(login_frame, text="Don't have an account? Register", 
                                 foreground="blue", cursor="hand2")
        register_link.grid(row=4, column=0, columnspan=2)
        register_link.bind("<Button-1>", lambda e: self.show_register_screen())
        
        # Set focus to username entry
        self.username_entry.focus()
        
        # Bind Enter key to login
        self.root.bind("<Return>", lambda event: self.login())
    
    def show_register_screen(self):
        """Display the registration screen"""
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create register frame
        register_frame = ttk.Frame(self.root, padding="30 30 30 30")
        register_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title
        title_label = ttk.Label(register_frame, text="Register New User", 
                               style="Header.TLabel", font=("Helvetica", 20, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))
        
        # Username
        ttk.Label(register_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        self.reg_username_entry = ttk.Entry(register_frame, width=30, font=("Helvetica", 12))
        self.reg_username_entry.grid(row=1, column=1, pady=(0, 10), ipady=5)
        
        # Password
        ttk.Label(register_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        self.reg_password_entry = ttk.Entry(register_frame, width=30, show="*", font=("Helvetica", 12))
        self.reg_password_entry.grid(row=2, column=1, pady=(0, 10), ipady=5)
        
        # Confirm Password
        ttk.Label(register_frame, text="Confirm Password:").grid(row=3, column=0, sticky=tk.W, pady=(0, 20))
        self.reg_confirm_entry = ttk.Entry(register_frame, width=30, show="*", font=("Helvetica", 12))
        self.reg_confirm_entry.grid(row=3, column=1, pady=(0, 20), ipady=5)
        
        # Role selection
        ttk.Label(register_frame, text="Role:").grid(row=4, column=0, sticky=tk.W, pady=(0, 20))
        self.role_var = tk.StringVar(value="user")
        role_frame = ttk.Frame(register_frame)
        role_frame.grid(row=4, column=1, sticky=tk.W, pady=(0, 20))
        
        ttk.Radiobutton(role_frame, text="User", variable=self.role_var, value="user").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(role_frame, text="Admin", variable=self.role_var, value="admin").pack(side=tk.LEFT)
        
        # Buttons
        button_frame = ttk.Frame(register_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(0, 10))
        
        register_button = ttk.Button(button_frame, text="Register", command=self.register)
        register_button.pack(side=tk.LEFT, padx=(0, 10))
        
        back_button = ttk.Button(button_frame, text="Back to Login", 
                                style="Secondary.TButton", command=self.show_login_screen)
        back_button.pack(side=tk.LEFT)
        
        # Set focus to username entry
        self.reg_username_entry.focus()
    
    def login(self):
        """Authenticate user and show main application if successful"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, role FROM users WHERE username = ? AND password = ?", 
                      (username, password))
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            self.current_user = {"id": user[0], "username": user[1], "role": user[2]}
            self.show_main_application()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")
    
    def register(self):
        """Register a new user"""
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()
        confirm = self.reg_confirm_entry.get()
        role = self.role_var.get()
        
        # Validate inputs
        if not username or not password or not confirm:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long")
            return
        
        # Check if username already exists
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            messagebox.showerror("Error", "Username already exists")
            return
        
        # Insert new user
        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                          (username, password, role))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Registration successful! You can now login.")
            self.show_login_screen()
        except Exception as e:
            conn.close()
            messagebox.showerror("Error", f"Registration failed: {str(e)}")
    
    def show_main_application(self):
        """Display the main application interface"""
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Unbind previous events
        self.root.unbind("<Return>")
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header frame
        header_frame = ttk.Frame(self.main_frame, style="TFrame")
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # App title
        title_label = ttk.Label(header_frame, text="Inventory Management System", 
                               style="Header.TLabel", font=("Helvetica", 18, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # User info and logout
        user_frame = ttk.Frame(header_frame, style="TFrame")
        user_frame.pack(side=tk.RIGHT)
        
        user_label = ttk.Label(user_frame, 
                              text=f"Logged in as: {self.current_user['username']} ({self.current_user['role']})")
        user_label.pack(side=tk.LEFT, padx=(0, 10))
        
        logout_button = ttk.Button(user_frame, text="Logout", 
                                  style="Secondary.TButton", command=self.logout)
        logout_button.pack(side=tk.LEFT)
        
        # Create content frame with tabs
        self.tab_control = ttk.Notebook(self.main_frame)
        self.tab_control.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Dashboard tab
        self.dashboard_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.dashboard_tab, text="Dashboard")
        
        # Inventory tab
        self.inventory_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.inventory_tab, text="Inventory")
        
        # Transactions tab
        self.transactions_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.transactions_tab, text="Transactions")
        
        # Reports tab
        self.reports_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.reports_tab, text="Reports")
        
        # Admin tab (only for admin users)
        if self.current_user["role"] == "admin":
            self.admin_tab = ttk.Frame(self.tab_control)
            self.tab_control.add(self.admin_tab, text="Admin")
        
        # Initialize tabs
        self.setup_dashboard_tab()
        self.setup_inventory_tab()
        self.setup_transactions_tab()
        self.setup_reports_tab()
        
        if self.current_user["role"] == "admin":
            self.setup_admin_tab()
        
        # Status bar
        status_bar = ttk.Frame(self.main_frame, relief=tk.SUNKEN, style="TFrame")
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        status_label = ttk.Label(status_bar, text="Ready")
        status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        date_label = ttk.Label(status_bar, text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        date_label.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # Update date/time every second
        def update_time():
            date_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.root.after(1000, update_time)
        
        update_time()
    
    def setup_dashboard_tab(self):
        """Set up the dashboard tab with summary information"""
        # Create frame for dashboard content
        dashboard_content = ttk.Frame(self.dashboard_tab, style="TFrame")
        dashboard_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Welcome message
        welcome_frame = ttk.Frame(dashboard_content, style="TFrame")
        welcome_frame.pack(fill=tk.X, pady=(0, 20))
        
        welcome_label = ttk.Label(welcome_frame, 
                                 text=f"Welcome, {self.current_user['username']}!", 
                                 font=("Helvetica", 16, "bold"))
        welcome_label.pack(anchor=tk.W)
        
        date_label = ttk.Label(welcome_frame, 
                              text=f"Today is {datetime.now().strftime('%A, %B %d, %Y')}")
        date_label.pack(anchor=tk.W)
        
        # Stats cards
        stats_frame = ttk.Frame(dashboard_content, style="TFrame")
        stats_frame.pack(fill=tk.X, pady=20)
        
        # Get stats from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        # Total items
        cursor.execute("SELECT SUM(quantity) FROM inventory")
        total_items = cursor.fetchone()[0] or 0
        
        # Total value
        cursor.execute("SELECT SUM(quantity * unit_price) FROM inventory")
        total_value = cursor.fetchone()[0] or 0
        
        # Low stock items
        cursor.execute("SELECT COUNT(*) FROM inventory WHERE quantity < 10")
        low_stock = cursor.fetchone()[0] or 0
        
        # Categories count
        cursor.execute("SELECT COUNT(DISTINCT category) FROM inventory")
        categories = cursor.fetchone()[0] or 0
        
        conn.close()
        
        # Create stat cards
        self.create_stat_card(stats_frame, "Total Items", f"{total_items:,}", "#4CAF50", 0, 0)
        self.create_stat_card(stats_frame, "Inventory Value", f"N{total_value:,.2f}", "#2196F3", 0, 1)
        self.create_stat_card(stats_frame, "Low Stock Items", f"{low_stock}", "#f44336" if low_stock > 0 else "#4CAF50", 1, 0)
        self.create_stat_card(stats_frame, "Categories", f"{categories}", "#FF9800", 1, 1)
        
        # Recent activity
        activity_frame = ttk.LabelFrame(dashboard_content, text="Recent Activity", style="TFrame")
        activity_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # Create treeview for recent transactions
        columns = ("date", "item", "type", "quantity", "user")
        self.activity_tree = ttk.Treeview(activity_frame, columns=columns, show="headings", height=6)
        
        # Define headings
        self.activity_tree.heading("date", text="Date")
        self.activity_tree.heading("item", text="Item")
        self.activity_tree.heading("type", text="Transaction Type")
        self.activity_tree.heading("quantity", text="Quantity")
        self.activity_tree.heading("user", text="User")
        
        # Define columns
        self.activity_tree.column("date", width=150)
        self.activity_tree.column("item", width=200)
        self.activity_tree.column("type", width=150)
        self.activity_tree.column("quantity", width=100)
        self.activity_tree.column("user", width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(activity_frame, orient=tk.VERTICAL, command=self.activity_tree.yview)
        self.activity_tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        self.activity_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load recent transactions
        self.load_recent_transactions()
        
        # Quick actions
        actions_frame = ttk.LabelFrame(dashboard_content, text="Quick Actions", style="TFrame")
        actions_frame.pack(fill=tk.X, pady=20)
        
        add_item_btn = ttk.Button(actions_frame, text="Add New Item", 
                                 command=lambda: self.tab_control.select(self.inventory_tab))
        add_item_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        stock_in_btn = ttk.Button(actions_frame, text="Stock In", 
                                 command=lambda: self.show_transaction_dialog("in"))
        stock_in_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        stock_out_btn = ttk.Button(actions_frame, text="Stock Out", 
                                  command=lambda: self.show_transaction_dialog("out"))
        stock_out_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        report_btn = ttk.Button(actions_frame, text="Generate Report", 
                               command=lambda: self.tab_control.select(self.reports_tab))
        report_btn.pack(side=tk.LEFT, padx=10, pady=10)
    
    def create_stat_card(self, parent, title, value, color, row, col):
        """Create a statistics card for the dashboard"""
        card = ttk.Frame(parent, style="TFrame", relief=tk.RAISED)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Configure grid weights
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)
        
        # Card content
        value_label = ttk.Label(card, text=value, font=("Helvetica", 24, "bold"))
        value_label.pack(pady=(20, 5))
        
        title_label = ttk.Label(card, text=title, font=("Helvetica", 12))
        title_label.pack(pady=(5, 20))
        
        # Add colored indicator
        indicator = ttk.Frame(card, height=5, style="TFrame")
        indicator.pack(fill=tk.X, side=tk.BOTTOM)
        indicator.configure(style="TFrame")
        
        # We can't directly set background color with ttk, so we'll use a Canvas
        canvas = tk.Canvas(indicator, height=5, bg=color, highlightthickness=0)
        canvas.pack(fill=tk.X)
    
    def load_recent_transactions(self):
        """Load recent transactions for the dashboard"""
        # Clear existing items
        for item in self.activity_tree.get_children():
            self.activity_tree.delete(item)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT t.transaction_date, i.item_name, t.transaction_type, t.quantity, u.username
        FROM transactions t
        JOIN inventory i ON t.item_id = i.id
        JOIN users u ON t.user_id = u.id
        ORDER BY t.transaction_date DESC
        LIMIT 10
        ''')
        
        transactions = cursor.fetchall()
        conn.close()
        
        # Insert into treeview
        for tx in transactions:
            date = datetime.fromisoformat(tx['transaction_date']).strftime('%Y-%m-%d %H:%M')
            
            # Format transaction type
            tx_type = tx['transaction_type'].capitalize()
            
            # Format quantity with sign
            quantity = f"+{tx['quantity']}" if tx['transaction_type'] == 'in' else f"-{tx['quantity']}"
            
            self.activity_tree.insert('', tk.END, values=(
                date, tx['item_name'], tx_type, quantity, tx['username']
            ))
    
    def setup_inventory_tab(self):
        """Set up the inventory tab with item listing and management"""
        # Create frame for inventory content
        inventory_content = ttk.Frame(self.inventory_tab, style="TFrame")
        inventory_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Search and filter bar
        search_frame = ttk.Frame(inventory_content, style="TFrame")
        search_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Search
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # Category filter
        ttk.Label(search_frame, text="Category:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Get categories from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM inventory ORDER BY category")
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Add "All" option
        categories = ["All"] + categories
        
        category_combo = ttk.Combobox(search_frame, textvariable=self.category_var, 
                                     values=categories, state="readonly", width=20)
        category_combo.current(0)
        category_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # Search button
        search_button = ttk.Button(search_frame, text="Search", 
                                  command=self.search_inventory)
        search_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Reset button
        reset_button = ttk.Button(search_frame, text="Reset", 
                                 command=self.reset_inventory_search)
        reset_button.pack(side=tk.LEFT)
        
        # Action buttons
        action_frame = ttk.Frame(inventory_content, style="TFrame")
        action_frame.pack(fill=tk.X, pady=(0, 20))
        
        add_button = ttk.Button(action_frame, text="Add New Item", 
                               command=self.show_add_item_dialog)
        add_button.pack(side=tk.LEFT, padx=(0, 10))
        
        edit_button = ttk.Button(action_frame, text="Edit Item", 
                                command=self.show_edit_item_dialog)
        edit_button.pack(side=tk.LEFT, padx=(0, 10))
        
        delete_button = ttk.Button(action_frame, text="Delete Item", 
                                  style="Danger.TButton", command=self.delete_item)
        delete_button.pack(side=tk.LEFT)
        
        # Inventory table
        table_frame = ttk.Frame(inventory_content, style="TFrame")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview
        columns = ("id", "name", "description", "category", "quantity", "price", "value", "supplier", "last_updated")
        self.inventory_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Define headings
        self.inventory_tree.heading("id", text="ID")
        self.inventory_tree.heading("name", text="Item Name")
        self.inventory_tree.heading("description", text="Description")
        self.inventory_tree.heading("category", text="Category")
        self.inventory_tree.heading("quantity", text="Quantity")
        self.inventory_tree.heading("price", text="Unit Price")
        self.inventory_tree.heading("value", text="Total Value")
        self.inventory_tree.heading("supplier", text="Supplier")
        self.inventory_tree.heading("last_updated", text="Last Updated")
        
        # Define columns
        self.inventory_tree.column("id", width=50, anchor=tk.CENTER)
        self.inventory_tree.column("name", width=150)
        self.inventory_tree.column("description", width=200)
        self.inventory_tree.column("category", width=100)
        self.inventory_tree.column("quantity", width=80, anchor=tk.CENTER)
        self.inventory_tree.column("price", width=100, anchor=tk.E)
        self.inventory_tree.column("value", width=120, anchor=tk.E)
        self.inventory_tree.column("supplier", width=150)
        self.inventory_tree.column("last_updated", width=150, anchor=tk.CENTER)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscroll=y_scrollbar.set)
        
        x_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.inventory_tree.xview)
        self.inventory_tree.configure(xscroll=x_scrollbar.set)
        
        # Pack widgets
        self.inventory_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load inventory data
        self.load_inventory()
        
        # Bind double-click to edit
        self.inventory_tree.bind("<Double-1>", lambda event: self.show_edit_item_dialog())
        
        # Bind search entry to update on keypress
        self.search_var.trace("w", lambda name, index, mode: self.search_inventory())
        self.category_var.trace("w", lambda name, index, mode: self.search_inventory())
    
    def load_inventory(self):
        """Load inventory data into the treeview"""
        # Clear existing items
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, item_name, description, category, quantity, unit_price, supplier, last_updated
        FROM inventory
        ORDER BY item_name
        ''')
        
        inventory_items = cursor.fetchall()
        conn.close()
        
        # Insert into treeview
        for item in inventory_items:
            item_id, name, desc, category, qty, price, supplier, updated = item
            
            # Calculate total value
            total_value = qty * price
            
            # Format price and value
            price_formatted = f"N{price:.2f}"
            value_formatted = f"N{total_value:.2f}"
            
            # Format date
            try:
                date_formatted = datetime.fromisoformat(updated).strftime('%Y-%m-%d %H:%M')
            except:
                date_formatted = updated
            
            self.inventory_tree.insert('', tk.END, values=(
                item_id, name, desc, category, qty, price_formatted, 
                value_formatted, supplier, date_formatted
            ))
    
    def search_inventory(self):
        """Search and filter inventory items"""
        search_term = self.search_var.get().lower()
        category = self.category_var.get()
        
        # Clear existing items
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        if category == "All":
            cursor.execute('''
            SELECT id, item_name, description, category, quantity, unit_price, supplier, last_updated
            FROM inventory
            WHERE LOWER(item_name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(supplier) LIKE ?
            ORDER BY item_name
            ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        else:
            cursor.execute('''
            SELECT id, item_name, description, category, quantity, unit_price, supplier, last_updated
            FROM inventory
            WHERE (LOWER(item_name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(supplier) LIKE ?)
            AND category = ?
            ORDER BY item_name
            ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', category))
        
        inventory_items = cursor.fetchall()
        conn.close()
        
        # Insert into treeview
        for item in inventory_items:
            item_id, name, desc, category, qty, price, supplier, updated = item
            
            # Calculate total value
            total_value = qty * price
            
            # Format price and value
            price_formatted = f"N{price:.2f}"
            value_formatted = f"N{total_value:.2f}"
            
            # Format date
            try:
                date_formatted = datetime.fromisoformat(updated).strftime('%Y-%m-%d %H:%M')
            except:
                date_formatted = updated
            
            self.inventory_tree.insert('', tk.END, values=(
                item_id, name, desc, category, qty, price_formatted, 
                value_formatted, supplier, date_formatted
            ))
    
    def reset_inventory_search(self):
        """Reset search and filter fields"""
        self.search_var.set("")
        self.category_var.set("All")
        self.load_inventory()
    
    def show_add_item_dialog(self):
        """Show dialog to add a new inventory item"""
        # Create a new top-level window
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Item")
        dialog.geometry("500x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create form frame
        form_frame = ttk.Frame(dialog, padding="20 20 20 20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields
        ttk.Label(form_frame, text="Item Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        desc_entry = ttk.Entry(form_frame, width=30)
        desc_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Category:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        
        # Get existing categories
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM inventory ORDER BY category")
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        category_var = tk.StringVar()
        category_combo = ttk.Combobox(form_frame, textvariable=category_var, values=categories, width=28)
        category_combo.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Quantity:").grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        qty_entry = ttk.Entry(form_frame, width=30)
        qty_entry.grid(row=3, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Unit Price:").grid(row=4, column=0, sticky=tk.W, pady=(0, 10))
        price_entry = ttk.Entry(form_frame, width=30)
        price_entry.grid(row=4, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Supplier:").grid(row=5, column=0, sticky=tk.W, pady=(0, 10))
        supplier_entry = ttk.Entry(form_frame, width=30)
        supplier_entry.grid(row=5, column=1, sticky=tk.W, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(20, 0))
        
        save_button = ttk.Button(button_frame, text="Save", 
                                command=lambda: self.save_new_item(
                                    name_entry.get(),
                                    desc_entry.get(),
                                    category_var.get(),
                                    qty_entry.get(),
                                    price_entry.get(),
                                    supplier_entry.get(),
                                    dialog
                                ))
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT)
        
        # Set focus to first field
        name_entry.focus_set()
    
    def save_new_item(self, name, description, category, quantity, price, supplier, dialog):
        """Save a new inventory item to the database"""
        # Validate inputs
        if not name:
            messagebox.showerror("Error", "Item name is required", parent=dialog)
            return
        
        if not category:
            messagebox.showerror("Error", "Category is required", parent=dialog)
            return
        
        try:
            quantity = int(quantity)
            if quantity < 0:
                raise ValueError("Quantity must be a positive number")
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive number", parent=dialog)
            return
        
        try:
            price = float(price)
            if price < 0:
                raise ValueError("Price must be a positive number")
        except ValueError:
            messagebox.showerror("Error", "Price must be a positive number", parent=dialog)
            return
        
        # Insert into database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO inventory (item_name, description, category, quantity, unit_price, supplier, updated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, description, category, quantity, price, supplier, self.current_user["id"]))
            
            # Get the ID of the new item
            item_id = cursor.lastrowid
            
            # Add transaction record
            cursor.execute('''
            INSERT INTO transactions (item_id, transaction_type, quantity, user_id, notes)
            VALUES (?, ?, ?, ?, ?)
            ''', (item_id, 'in', quantity, self.current_user["id"], "Initial stock"))
            
            conn.commit()
            messagebox.showinfo("Success", "Item added successfully", parent=dialog)
            
            # Close dialog and refresh inventory
            dialog.destroy()
            self.load_inventory()
            self.load_recent_transactions()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to add item: {str(e)}", parent=dialog)
        
        finally:
            conn.close()
    
    def show_edit_item_dialog(self):
        """Show dialog to edit an existing inventory item"""
        # Get selected item
        selected = self.inventory_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select an item to edit")
            return
        
        # Get item ID
        item_id = self.inventory_tree.item(selected[0], 'values')[0]
        
        # Get item data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT item_name, description, category, quantity, unit_price, supplier
        FROM inventory
        WHERE id = ?
        ''', (item_id,))
        
        item = cursor.fetchone()
        conn.close()
        
        if not item:
            messagebox.showerror("Error", "Item not found")
            return
        
        name, description, category, quantity, price, supplier = item
        
        # Create a new top-level window
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Item")
        dialog.geometry("500x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create form frame
        form_frame = ttk.Frame(dialog, padding="20 20 20 20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields
        ttk.Label(form_frame, text="Item Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.insert(0, name)
        name_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        desc_entry = ttk.Entry(form_frame, width=30)
        desc_entry.insert(0, description if description else "")
        desc_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Category:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        
        # Get existing categories
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM inventory ORDER BY category")
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        category_var = tk.StringVar(value=category)
        category_combo = ttk.Combobox(form_frame, textvariable=category_var, values=categories, width=28)
        category_combo.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Quantity:").grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        qty_entry = ttk.Entry(form_frame, width=30)
        qty_entry.insert(0, quantity)
        qty_entry.grid(row=3, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Unit Price:").grid(row=4, column=0, sticky=tk.W, pady=(0, 10))
        price_entry = ttk.Entry(form_frame, width=30)
        price_entry.insert(0, price)
        price_entry.grid(row=4, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Supplier:").grid(row=5, column=0, sticky=tk.W, pady=(0, 10))
        supplier_entry = ttk.Entry(form_frame, width=30)
        supplier_entry.insert(0, supplier if supplier else "")
        supplier_entry.grid(row=5, column=1, sticky=tk.W, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(20, 0))
        
        save_button = ttk.Button(button_frame, text="Save", 
                                command=lambda: self.update_item(
                                    item_id,
                                    name_entry.get(),
                                    desc_entry.get(),
                                    category_var.get(),
                                    qty_entry.get(),
                                    price_entry.get(),
                                    supplier_entry.get(),
                                    dialog
                                ))
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT)
    
    def update_item(self, item_id, name, description, category, quantity, price, supplier, dialog):
        """Update an existing inventory item in the database"""
        # Validate inputs
        if not name:
            messagebox.showerror("Error", "Item name is required", parent=dialog)
            return
        
        if not category:
            messagebox.showerror("Error", "Category is required", parent=dialog)
            return
        
        try:
            quantity = int(quantity)
            if quantity < 0:
                raise ValueError("Quantity must be a positive number")
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive number", parent=dialog)
            return
        
        try:
            price = float(price)
            if price < 0:
                raise ValueError("Price must be a positive number")
        except ValueError:
            messagebox.showerror("Error", "Price must be a positive number", parent=dialog)
            return
        
        # Get current quantity to check if it changed
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT quantity FROM inventory WHERE id = ?", (item_id,))
        current_qty = cursor.fetchone()[0]
        
        try:
            # Update inventory item
            cursor.execute('''
            UPDATE inventory
            SET item_name = ?, description = ?, category = ?, quantity = ?, 
                unit_price = ?, supplier = ?, last_updated = CURRENT_TIMESTAMP,
                updated_by = ?
            WHERE id = ?
            ''', (name, description, category, quantity, price, supplier, 
                 self.current_user["id"], item_id))
            
            # If quantity changed, add a transaction record
            if quantity != current_qty:
                qty_diff = quantity - current_qty
                tx_type = 'in' if qty_diff > 0 else 'out'
                
                cursor.execute('''
                INSERT INTO transactions (item_id, transaction_type, quantity, user_id, notes)
                VALUES (?, ?, ?, ?, ?)
                ''', (item_id, tx_type, abs(qty_diff), self.current_user["id"], "Manual adjustment"))
            
            conn.commit()
            messagebox.showinfo("Success", "Item updated successfully", parent=dialog)
            
            # Close dialog and refresh inventory
            dialog.destroy()
            self.load_inventory()
            self.load_recent_transactions()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to update item: {str(e)}", parent=dialog)
        
        finally:
            conn.close()
    
    def delete_item(self):
        """Delete an inventory item"""
        # Get selected item
        selected = self.inventory_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select an item to delete")
            return
        
        # Get item ID and name
        item_values = self.inventory_tree.item(selected[0], 'values')
        item_id = item_values[0]
        item_name = item_values[1]
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Delete", 
                                     f"Are you sure you want to delete '{item_name}'?\n\nThis action cannot be undone.")
        if not confirm:
            return
        
        # Delete from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            # First delete related transactions
            cursor.execute("DELETE FROM transactions WHERE item_id = ?", (item_id,))
            
            # Then delete the item
            cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
            
            conn.commit()
            messagebox.showinfo("Success", f"Item '{item_name}' deleted successfully")
            
            # Refresh inventory
            self.load_inventory()
            self.load_recent_transactions()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to delete item: {str(e)}")
        
        finally:
            conn.close()
    
    def show_transaction_dialog(self, transaction_type):
        """Show dialog to add a stock in/out transaction"""
        # Create a new top-level window
        dialog = tk.Toplevel(self.root)
        dialog.title("Stock " + ("In" if transaction_type == "in" else "Out"))
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create form frame
        form_frame = ttk.Frame(dialog, padding="20 20 20 20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields
        ttk.Label(form_frame, text="Item:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Get items from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, item_name FROM inventory ORDER BY item_name")
        items = [(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()
        
        # Create a dictionary to map item names to IDs
        item_dict = {item[1]: item[0] for item in items}
        
        item_var = tk.StringVar()
        item_combo = ttk.Combobox(form_frame, textvariable=item_var, 
                                 values=[item[1] for item in items], width=28)
        item_combo.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Quantity:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        qty_entry = ttk.Entry(form_frame, width=30)
        qty_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Notes:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        notes_entry = ttk.Entry(form_frame, width=30)
        notes_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))
        
        save_button = ttk.Button(button_frame, text="Save", 
                                command=lambda: self.save_transaction(
                                    item_dict.get(item_var.get()),
                                    transaction_type,
                                    qty_entry.get(),
                                    notes_entry.get(),
                                    dialog
                                ))
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT)
    
    def save_transaction(self, item_id, transaction_type, quantity, notes, dialog):
        """Save a stock transaction to the database"""
        # Validate inputs
        if not item_id:
            messagebox.showerror("Error", "Please select an item", parent=dialog)
            return
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be a positive number")
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive number", parent=dialog)
            return
        
        # Get current quantity
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT quantity FROM inventory WHERE id = ?", (item_id,))
        current_qty = cursor.fetchone()[0]
        
        # For stock out, check if there's enough quantity
        if transaction_type == "out" and quantity > current_qty:
            messagebox.showerror("Error", 
                               f"Not enough stock. Current quantity: {current_qty}", 
                               parent=dialog)
            conn.close()
            return
        
        try:
            # Update inventory quantity
            new_qty = current_qty + quantity if transaction_type == "in" else current_qty - quantity
            
            cursor.execute('''
            UPDATE inventory
            SET quantity = ?, last_updated = CURRENT_TIMESTAMP, updated_by = ?
            WHERE id = ?
            ''', (new_qty, self.current_user["id"], item_id))
            
            # Add transaction record
            cursor.execute('''
            INSERT INTO transactions (item_id, transaction_type, quantity, user_id, notes)
            VALUES (?, ?, ?, ?, ?)
            ''', (item_id, transaction_type, quantity, self.current_user["id"], notes))
            
            conn.commit()
            messagebox.showinfo("Success", "Transaction recorded successfully", parent=dialog)
            
            # Close dialog and refresh inventory
            dialog.destroy()
            self.load_inventory()
            self.load_recent_transactions()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Failed to record transaction: {str(e)}", parent=dialog)
        
        finally:
            conn.close()
    
    def setup_transactions_tab(self):
        """Set up the transactions tab with transaction history"""
        # Create frame for transactions content
        transactions_content = ttk.Frame(self.transactions_tab, style="TFrame")
        transactions_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Search and filter bar
        filter_frame = ttk.Frame(transactions_content, style="TFrame")
        filter_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Date range
        ttk.Label(filter_frame, text="From:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Create date variables
        self.from_date_var = tk.StringVar()
        self.to_date_var = tk.StringVar()
        
        # Set default dates (last 30 days)
        today = datetime.now()
        thirty_days_ago = today - datetime.timedelta(days=30)
        
        self.from_date_var.set(thirty_days_ago.strftime('%Y-%m-%d'))
        self.to_date_var.set(today.strftime('%Y-%m-%d'))
        
        from_date_entry = ttk.Entry(filter_frame, textvariable=self.from_date_var, width=12)
        from_date_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(filter_frame, text="To:").pack(side=tk.LEFT, padx=(0, 5))
        to_date_entry = ttk.Entry(filter_frame, textvariable=self.to_date_var, width=12)
        to_date_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # Transaction type filter
        ttk.Label(filter_frame, text="Type:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.tx_type_var = tk.StringVar(value="All")
        tx_type_combo = ttk.Combobox(filter_frame, textvariable=self.tx_type_var, 
                                    values=["All", "In", "Out"], state="readonly", width=10)
        tx_type_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # Item filter
        ttk.Label(filter_frame, text="Item:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Get items from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, item_name FROM inventory ORDER BY item_name")
        items = [(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()
        
        # Create a dictionary to map item names to IDs
        self.item_dict = {item[1]: item[0] for item in items}
        self.item_dict["All Items"] = 0
        
        self.tx_item_var = tk.StringVar(value="All Items")
        tx_item_combo = ttk.Combobox(filter_frame, textvariable=self.tx_item_var, 
                                    values=["All Items"] + [item[1] for item in items], 
                                    state="readonly", width=20)
        tx_item_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # Filter button
        filter_button = ttk.Button(filter_frame, text="Filter", 
                                  command=self.load_transactions)
        filter_button.pack(side=tk.LEFT)
        
        # Transactions table
        table_frame = ttk.Frame(transactions_content, style="TFrame")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Create treeview
        columns = ("id", "date", "item", "type", "quantity", "user", "notes")
        self.transactions_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Define headings
        self.transactions_tree.heading("id", text="ID")
        self.transactions_tree.heading("date", text="Date")
        self.transactions_tree.heading("item", text="Item")
        self.transactions_tree.heading("type", text="Type")
        self.transactions_tree.heading("quantity", text="Quantity")
        self.transactions_tree.heading("user", text="User")
        self.transactions_tree.heading("notes", text="Notes")
        
        # Define columns
        self.transactions_tree.column("id", width=50, anchor=tk.CENTER)
        self.transactions_tree.column("date", width=150, anchor=tk.CENTER)
        self.transactions_tree.column("item", width=200)
        self.transactions_tree.column("type", width=100, anchor=tk.CENTER)
        self.transactions_tree.column("quantity", width=100, anchor=tk.CENTER)
        self.transactions_tree.column("user", width=150)
        self.transactions_tree.column("notes", width=200)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.transactions_tree.yview)
        self.transactions_tree.configure(yscroll=y_scrollbar.set)
        
        x_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.transactions_tree.xview)
        self.transactions_tree.configure(xscroll=x_scrollbar.set)
        
        # Pack widgets
        self.transactions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load transaction data
        self.load_transactions()
    
    def load_transactions(self):
        """Load transaction data into the treeview"""
        # Clear existing items
        for item in self.transactions_tree.get_children():
            self.transactions_tree.delete(item)
        
        # Get filter values
        from_date = self.from_date_var.get()
        to_date = self.to_date_var.get()
        tx_type = self.tx_type_var.get()
        item_name = self.tx_item_var.get()
        
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
        SELECT t.id, t.transaction_date, i.item_name, t.transaction_type, 
               t.quantity, u.username, t.notes
        FROM transactions t
        JOIN inventory i ON t.item_id = i.id
        JOIN users u ON t.user_id = u.id
        WHERE t.transaction_date BETWEEN ? AND ?
        '''
        
        params = [from_date_obj.isoformat(), to_date_obj.isoformat()]
        
        if tx_type != "All":
            query += " AND t.transaction_type = ?"
            params.append(tx_type.lower())
        
        if item_name != "All Items":
            query += " AND t.item_id = ?"
            params.append(self.item_dict[item_name])
        
        query += " ORDER BY t.transaction_date DESC"
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        transactions = cursor.fetchall()
        conn.close()
        
        # Insert into treeview
        for tx in transactions:
            tx_id, date, item, tx_type, qty, user, notes = tx
            
            # Format date
            try:
                date_formatted = datetime.fromisoformat(date).strftime('%Y-%m-%d %H:%M')
            except:
                date_formatted = date
            
            # Format transaction type
            tx_type_formatted = tx_type.capitalize()
            
            # Format quantity with sign
            qty_formatted = f"+{qty}" if tx_type == 'in' else f"-{qty}"
            
            self.transactions_tree.insert('', tk.END, values=(
                tx_id, date_formatted, item, tx_type_formatted, qty_formatted, user, notes
            ))
    
    def setup_reports_tab(self):
        """Set up the reports tab with reporting options"""
        # Create frame for reports content
        reports_content = ttk.Frame(self.reports_tab, style="TFrame")
        reports_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(reports_content, text="Generate Reports", 
                               style="Header.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Report options
        options_frame = ttk.LabelFrame(reports_content, text="Report Options", style="TFrame")
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Report type
        ttk.Label(options_frame, text="Report Type:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        
        self.report_type_var = tk.StringVar(value="Inventory Summary")
        report_types = [
            "Inventory Summary", 
            "Low Stock Items", 
            "Inventory Value by Category",
            "Transaction History",
            "Item Movement"
        ]
        
        report_type_combo = ttk.Combobox(options_frame, textvariable=self.report_type_var, 
                                        values=report_types, state="readonly", width=30)
        report_type_combo.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Date range
        ttk.Label(options_frame, text="Date Range:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        
        date_frame = ttk.Frame(options_frame, style="TFrame")
        date_frame.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Create date variables for reports
        self.report_from_date_var = tk.StringVar()
        self.report_to_date_var = tk.StringVar()
        
        # Set default dates (last 30 days)
        today = datetime.now()
        thirty_days_ago = today - datetime.timedelta(days=30)
        
        self.report_from_date_var.set(thirty_days_ago.strftime('%Y-%m-%d'))
        self.report_to_date_var.set(today.strftime('%Y-%m-%d'))
        
        ttk.Label(date_frame, text="From:").pack(side=tk.LEFT, padx=(0, 5))
        from_date_entry = ttk.Entry(date_frame, textvariable=self.report_from_date_var, width=12)
        from_date_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(date_frame, text="To:").pack(side=tk.LEFT, padx=(0, 5))
        to_date_entry = ttk.Entry(date_frame, textvariable=self.report_to_date_var, width=12)
        to_date_entry.pack(side=tk.LEFT)
        
        # Format options
        ttk.Label(options_frame, text="Format:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        
        self.report_format_var = tk.StringVar(value="Preview")
        format_frame = ttk.Frame(options_frame, style="TFrame")
        format_frame.grid(row=2, column=1, sticky=tk.W, padx=10, pady=10)
        
        ttk.Radiobutton(format_frame, text="Preview", variable=self.report_format_var, 
                       value="Preview").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(format_frame, text="Save as CSV", variable=self.report_format_var, 
                       value="CSV").pack(side=tk.LEFT)
        
        # Generate button
        generate_button = ttk.Button(options_frame, text="Generate Report", 
                                    command=self.generate_report)
        generate_button.grid(row=3, column=0, columnspan=2, pady=20)
        
        # Report preview area
        preview_frame = ttk.LabelFrame(reports_content, text="Report Preview", style="TFrame")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create treeview for report preview
        self.report_tree = ttk.Treeview(preview_frame)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.report_tree.yview)
        self.report_tree.configure(yscroll=y_scrollbar.set)
        
        x_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.report_tree.xview)
        self.report_tree.configure(xscroll=x_scrollbar.set)
        
        # Pack widgets
        self.report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def generate_report(self):
        """Generate a report based on selected options"""
        report_type = self.report_type_var.get()
        report_format = self.report_format_var.get()
        from_date = self.report_from_date_var.get()
        to_date = self.report_to_date_var.get()
        
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
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        
        # Configure columns based on report type
        if report_type == "Inventory Summary":
            self.setup_inventory_summary_report()
        elif report_type == "Low Stock Items":
            self.setup_low_stock_report()
        elif report_type == "Inventory Value by Category":
            self.setup_category_value_report()
        elif report_type == "Transaction History":
            self.setup_transaction_history_report(from_date_obj, to_date_obj)
        elif report_type == "Item Movement":
            self.setup_item_movement_report(from_date_obj, to_date_obj)
        
        # If CSV format is selected, save to file
        if report_format == "CSV":
            self.save_report_as_csv(report_type)
    
    def setup_inventory_summary_report(self):
        """Set up and generate inventory summary report"""
        # Configure columns
        columns = ("id", "name", "category", "quantity", "price", "value")
        self.report_tree.configure(columns=columns, show="headings")
        
        # Define headings
        self.report_tree.heading("id", text="ID")
        self.report_tree.heading("name", text="Item Name")
        self.report_tree.heading("category", text="Category")
        self.report_tree.heading("quantity", text="Quantity")
        self.report_tree.heading("price", text="Unit Price")
        self.report_tree.heading("value", text="Total Value")
        
        # Define columns
        self.report_tree.column("id", width=50, anchor=tk.CENTER)
        self.report_tree.column("name", width=200)
        self.report_tree.column("category", width=150)
        self.report_tree.column("quantity", width=100, anchor=tk.CENTER)
        self.report_tree.column("price", width=100, anchor=tk.E)
        self.report_tree.column("value", width=150, anchor=tk.E)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, item_name, category, quantity, unit_price
        FROM inventory
        ORDER BY category, item_name
        ''')
        
        items = cursor.fetchall()
        conn.close()
        
        # Insert into treeview
        total_value = 0
        for item in items:
            item_id, name, category, qty, price = item
            
            # Calculate total value
            value = qty * price
            total_value += value
            
            # Format price and value
            price_formatted = f"N{price:.2f}"
            value_formatted = f"N{value:.2f}"
            
            self.report_tree.insert('', tk.END, values=(
                item_id, name, category, qty, price_formatted, value_formatted
            ))
        
        # Add total row
        self.report_tree.insert('', tk.END, values=(
            "", "TOTAL", "", "", "", f"N{total_value:.2f}"
        ), tags=('total',))
        
        # Configure tag for total row
        self.report_tree.tag_configure('total', font=('Helvetica', 10, 'bold'))
    
    def setup_low_stock_report(self):
        """Set up and generate low stock items report"""
        # Configure columns
        columns = ("id", "name", "category", "quantity", "min_level", "status")
        self.report_tree.configure(columns=columns, show="headings")
        
        # Define headings
        self.report_tree.heading("id", text="ID")
        self.report_tree.heading("name", text="Item Name")
        self.report_tree.heading("category", text="Category")
        self.report_tree.heading("quantity", text="Current Quantity")
        self.report_tree.heading("min_level", text="Min Level")
        self.report_tree.heading("status", text="Status")
        
        # Define columns
        self.report_tree.column("id", width=50, anchor=tk.CENTER)
        self.report_tree.column("name", width=200)
        self.report_tree.column("category", width=150)
        self.report_tree.column("quantity", width=120, anchor=tk.CENTER)
        self.report_tree.column("min_level", width=100, anchor=tk.CENTER)
        self.report_tree.column("status", width=100, anchor=tk.CENTER)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, item_name, category, quantity
        FROM inventory
        WHERE quantity < 10
        ORDER BY quantity
        ''')
        
        items = cursor.fetchall()
        conn.close()
        
        # Insert into treeview
        for item in items:
            item_id, name, category, qty = item
            
            # Set minimum level (for demonstration)
            min_level = 10
            
            # Determine status
            if qty == 0:
                status = "Out of Stock"
                tag = 'critical'
            elif qty < 5:
                status = "Critical"
                tag = 'critical'
            else:
                status = "Low"
                tag = 'warning'
            
            self.report_tree.insert('', tk.END, values=(
                item_id, name, category, qty, min_level, status
            ), tags=(tag,))
        
        # Configure tags
        self.report_tree.tag_configure('critical', background='#ffcccc')
        self.report_tree.tag_configure('warning', background='#ffffcc')
    
    def setup_category_value_report(self):
        """Set up and generate inventory value by category report"""
        # Configure columns
        columns = ("category", "item_count", "total_quantity", "total_value", "percentage")
        self.report_tree.configure(columns=columns, show="headings")
        
        # Define headings
        self.report_tree.heading("category", text="Category")
        self.report_tree.heading("item_count", text="Number of Items")
        self.report_tree.heading("total_quantity", text="Total Quantity")
        self.report_tree.heading("total_value", text="Total Value")
        self.report_tree.heading("percentage", text="% of Total Value")
        
        # Define columns
        self.report_tree.column("category", width=150)
        self.report_tree.column("item_count", width=120, anchor=tk.CENTER)
        self.report_tree.column("total_quantity", width=120, anchor=tk.CENTER)
        self.report_tree.column("total_value", width=150, anchor=tk.E)
        self.report_tree.column("percentage", width=150, anchor=tk.CENTER)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            category,
            COUNT(*) as item_count,
            SUM(quantity) as total_quantity,
            SUM(quantity * unit_price) as total_value
        FROM inventory
        GROUP BY category
        ORDER BY total_value DESC
        ''')
        
        categories = cursor.fetchall()
        
        # Get total inventory value
        cursor.execute('SELECT SUM(quantity * unit_price) FROM inventory')
        total_inventory_value = cursor.fetchone()[0] or 0
        
        conn.close()
        
        # Insert into treeview
        for category in categories:
            cat_name, item_count, total_qty, total_value = category
            
            # Calculate percentage
            percentage = (total_value / total_inventory_value) * 100 if total_inventory_value > 0 else 0
            
            # Format values
            value_formatted = f"N{total_value:.2f}"
            percentage_formatted = f"{percentage:.2f}%"
            
            self.report_tree.insert('', tk.END, values=(
                cat_name, item_count, total_qty, value_formatted, percentage_formatted
            ))
        
        # Add total row
        self.report_tree.insert('', tk.END, values=(
            "TOTAL", sum(cat[1] for cat in categories), 
            sum(cat[2] for cat in categories), 
            f"N{total_inventory_value:.2f}", "100.00%"
        ), tags=('total',))
        
        # Configure tag for total row
        self.report_tree.tag_configure('total', font=('Helvetica', 10, 'bold'))
    
    def setup_transaction_history_report(self, from_date, to_date):
        """Set up and generate transaction history report"""
        # Configure columns
        columns = ("date", "item", "type", "quantity", "user", "notes")
        self.report_tree.configure(columns=columns, show="headings")
        
        # Define headings
        self.report_tree.heading("date", text="Date")
        self.report_tree.heading("item", text="Item")
        self.report_tree.heading("type", text="Transaction Type")
        self.report_tree.heading("quantity", text="Quantity")
        self.report_tree.heading("user", text="User")
        self.report_tree.heading("notes", text="Notes")
        
        # Define columns
        self.report_tree.column("date", width=150, anchor=tk.CENTER)
        self.report_tree.column("item", width=200)
        self.report_tree.column("type", width=120, anchor=tk.CENTER)
        self.report_tree.column("quantity", width=100, anchor=tk.CENTER)
        self.report_tree.column("user", width=150)
        self.report_tree.column("notes", width=200)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT t.transaction_date, i.item_name, t.transaction_type, 
               t.quantity, u.username, t.notes
        FROM transactions t
        JOIN inventory i ON t.item_id = i.id
        JOIN users u ON t.user_id = u.id
        WHERE t.transaction_date BETWEEN ? AND ?
        ORDER BY t.transaction_date DESC
        ''', (from_date.isoformat(), to_date.isoformat()))
        
        transactions = cursor.fetchall()
        conn.close()
        
        # Insert into treeview
        for tx in transactions:
            date, item, tx_type, qty, user, notes = tx
            
            # Format date
            try:
                date_formatted = datetime.fromisoformat(date).strftime('%Y-%m-%d %H:%M')
            except:
                date_formatted = date
            
            # Format transaction type
            tx_type_formatted = tx_type.capitalize()
            
            # Format quantity with sign
            qty_formatted = f"+{qty}" if tx_type == 'in' else f"-{qty}"
            
            self.report_tree.insert('', tk.END, values=(
                date_formatted, item, tx_type_formatted, qty_formatted, user, notes
            ))
    
    def setup_item_movement_report(self, from_date, to_date):
        """Set up and generate item movement report"""
        # Configure columns
        columns = ("item", "starting", "in", "out", "ending", "net_change")
        self.report_tree.configure(columns=columns, show="headings")
        
        # Define headings
        self.report_tree.heading("item", text="Item")
        self.report_tree.heading("starting", text="Starting Quantity")
        self.report_tree.heading("in", text="Stock In")
        self.report_tree.heading("out", text="Stock Out")
        self.report_tree.heading("ending", text="Ending Quantity")
        self.report_tree.heading("net_change", text="Net Change")
        
        # Define columns
        self.report_tree.column("item", width=200)
        self.report_tree.column("starting", width=120, anchor=tk.CENTER)
        self.report_tree.column("in", width=100, anchor=tk.CENTER)
        self.report_tree.column("out", width=100, anchor=tk.CENTER)
        self.report_tree.column("ending", width=120, anchor=tk.CENTER)
        self.report_tree.column("net_change", width=100, anchor=tk.CENTER)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        # Get all items
        cursor.execute("SELECT id, item_name, quantity FROM inventory ORDER BY item_name")
        items = cursor.fetchall()
        
        # For each item, calculate movement
        for item in items:
            item_id, item_name, current_qty = item
            
            # Get stock in transactions
            cursor.execute('''
            SELECT SUM(quantity) FROM transactions
            WHERE item_id = ? AND transaction_type = 'in'
            AND transaction_date BETWEEN ? AND ?
            ''', (item_id, from_date.isoformat(), to_date.isoformat()))
            
            stock_in = cursor.fetchone()[0] or 0
            
            # Get stock out transactions
            cursor.execute('''
            SELECT SUM(quantity) FROM transactions
            WHERE item_id = ? AND transaction_type = 'out'
            AND transaction_date BETWEEN ? AND ?
            ''', (item_id, from_date.isoformat(), to_date.isoformat()))
            
            stock_out = cursor.fetchone()[0] or 0
            
            # Calculate starting quantity (current - in + out)
            starting_qty = current_qty - stock_in + stock_out
            
            # Calculate net change
            net_change = stock_in - stock_out
            
            # Only include items with movement
            if stock_in > 0 or stock_out > 0:
                # Format net change with sign
                net_change_formatted = f"+{net_change}" if net_change > 0 else str(net_change)
                
                self.report_tree.insert('', tk.END, values=(
                    item_name, starting_qty, stock_in, stock_out, current_qty, net_change_formatted
                ))
        
        conn.close()
    
    def save_report_as_csv(self, report_type):
        """Save the current report as a CSV file"""
        # Get column headings
        columns = self.report_tree["columns"]
        headers = [self.report_tree.heading(col)["text"] for col in columns]
        
        # Get data from treeview
        data = []
        for item_id in self.report_tree.get_children():
            values = self.report_tree.item(item_id)["values"]
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
    
    def setup_admin_tab(self):
        """Set up the admin tab with user management"""
        # Create frame for admin content
        admin_content = ttk.Frame(self.admin_tab, style="TFrame")
        admin_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create notebook for admin sections
        admin_notebook = ttk.Notebook(admin_content)
        admin_notebook.pack(fill=tk.BOTH, expand=True)
        
        # User management tab
        user_tab = ttk.Frame(admin_notebook)
        admin_notebook.add(user_tab, text="User Management")
        
        # System settings tab
        settings_tab = ttk.Frame(admin_notebook)
        admin_notebook.add(settings_tab, text="System Settings")
        
        # Database backup tab
        backup_tab = ttk.Frame(admin_notebook)
        admin_notebook.add(backup_tab, text="Database Backup")
        
        # Setup user management tab
        self.setup_user_management_tab(user_tab)
        
        # Setup system settings tab
        self.setup_system_settings_tab(settings_tab)
        
        # Setup database backup tab
        self.setup_database_backup_tab(backup_tab)
    
    def setup_user_management_tab(self, parent):
        """Set up the user management tab"""
        # Create frame for user management content
        user_content = ttk.Frame(parent, style="TFrame")
        user_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Action buttons
        action_frame = ttk.Frame(user_content, style="TFrame")
        action_frame.pack(fill=tk.X, pady=(0, 20))
        
        add_user_button = ttk.Button(action_frame, text="Add User", 
                                    command=self.show_add_user_dialog)
        add_user_button.pack(side=tk.LEFT, padx=(0, 10))
        
        edit_user_button = ttk.Button(action_frame, text="Edit User", 
                                     command=self.show_edit_user_dialog)
        edit_user_button.pack(side=tk.LEFT, padx=(0, 10))
        
        delete_user_button = ttk.Button(action_frame, text="Delete User", 
                                       style="Danger.TButton", command=self.delete_user)
        delete_user_button.pack(side=tk.LEFT)
        
        # User table
        table_frame = ttk.Frame(user_content, style="TFrame")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview
        columns = ("id", "username", "role", "created_at")
        self.users_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Define headings
        self.users_tree.heading("id", text="ID")
        self.users_tree.heading("username", text="Username")
        self.users_tree.heading("role", text="Role")
        self.users_tree.heading("created_at", text="Created At")
        
        # Define columns
        self.users_tree.column("id", width=50, anchor=tk.CENTER)
        self.users_tree.column("username", width=200)
        self.users_tree.column("role", width=100, anchor=tk.CENTER)
        self.users_tree.column("created_at", width=150, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load user data
        self.load_users()
        
        # Bind double-click to edit
        self.users_tree.bind("<Double-1>", lambda event: self.show_edit_user_dialog())
    
    def load_users(self):
        """Load user data into the treeview"""
        # Clear existing items
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        # Get data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, role, created_at FROM users ORDER BY username")
        users = cursor.fetchall()
        conn.close()
        
        # Insert into treeview
        for user in users:
            user_id, username, role, created_at = user
            
            # Format date
            try:
                date_formatted = datetime.fromisoformat(created_at).strftime('%Y-%m-%d %H:%M')
            except:
                date_formatted = created_at
            
            # Format role
            role_formatted = role.capitalize()
            
            self.users_tree.insert('', tk.END, values=(
                user_id, username, role_formatted, date_formatted
            ))
    
    def show_add_user_dialog(self):
        """Show dialog to add a new user"""
        # Create a new top-level window
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New User")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create form frame
        form_frame = ttk.Frame(dialog, padding="20 20 20 20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        username_entry = ttk.Entry(form_frame, width=30)
        username_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        password_entry = ttk.Entry(form_frame, width=30, show="*")
        password_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Confirm Password:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        confirm_entry = ttk.Entry(form_frame, width=30, show="*")
        confirm_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Role:").grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        
        role_var = tk.StringVar(value="user")
        role_frame = ttk.Frame(form_frame)
        role_frame.grid(row=3, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Radiobutton(role_frame, text="User", variable=role_var, value="user").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(role_frame, text="Admin", variable=role_var, value="admin").pack(side=tk.LEFT)
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        
        save_button = ttk.Button(button_frame, text="Save", 
                                command=lambda: self.save_new_user(
                                    username_entry.get(),
                                    password_entry.get(),
                                    confirm_entry.get(),
                                    role_var.get(),
                                    dialog
                                ))
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT)
        
        # Set focus to first field
        username_entry.focus_set()
    
    def save_new_user(self, username, password, confirm, role, dialog):
        """Save a new user to the database"""
        # Validate inputs
        if not username or not password or not confirm:
            messagebox.showerror("Error", "Please fill in all fields", parent=dialog)
            return
        
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match", parent=dialog)
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long", parent=dialog)
            return
        
        # Check if username already exists
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            messagebox.showerror("Error", "Username already exists", parent=dialog)
            return
        
        # Insert new user
        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                          (username, password, role))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "User added successfully", parent=dialog)
            
            # Close dialog and refresh users
            dialog.destroy()
            self.load_users()
        except Exception as e:
            conn.close()
            messagebox.showerror("Error", f"Failed to add user: {str(e)}", parent=dialog)
    
    def show_edit_user_dialog(self):
        """Show dialog to edit an existing user"""
        # Get selected user
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a user to edit")
            return
        
        # Get user ID
        user_id = self.users_tree.item(selected[0], 'values')[0]
        
        # Get user data from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT username, role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            messagebox.showerror("Error", "User not found")
            return
        
        username, role = user
        
        # Create a new top-level window
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit User")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create form frame
        form_frame = ttk.Frame(dialog, padding="20 20 20 20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        username_entry = ttk.Entry(form_frame, width=30)
        username_entry.insert(0, username)
        username_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="New Password:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        password_entry = ttk.Entry(form_frame, width=30, show="*")
        password_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Confirm Password:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        confirm_entry = ttk.Entry(form_frame, width=30, show="*")
        confirm_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(form_frame, text="Role:").grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        
        role_var = tk.StringVar(value=role)
        role_frame = ttk.Frame(form_frame)
        role_frame.grid(row=3, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Radiobutton(role_frame, text="User", variable=role_var, value="user").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(role_frame, text="Admin", variable=role_var, value="admin").pack(side=tk.LEFT)
        
        # Password note
        note_label = ttk.Label(form_frame, text="Leave password blank to keep current password", 
                              font=("Helvetica", 8), foreground="gray")
        note_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        save_button = ttk.Button(button_frame, text="Save", 
                                command=lambda: self.update_user(
                                    user_id,
                                    username_entry.get(),
                                    password_entry.get(),
                                    confirm_entry.get(),
                                    role_var.get(),
                                    dialog
                                ))
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                  command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT)
    
    def update_user(self, user_id, username, password, confirm, role, dialog):
        """Update an existing user in the database"""
        # Validate inputs
        if not username:
            messagebox.showerror("Error", "Username is required", parent=dialog)
            return
        
        # Check if changing password
        change_password = len(password) > 0
        
        if change_password:
            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match", parent=dialog)
                return
            
            if len(password) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters long", parent=dialog)
                return
        
        # Check if username already exists (for another user)
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ? AND id != ?", (username, user_id))
        if cursor.fetchone()[0] > 0:
            conn.close()
            messagebox.showerror("Error", "Username already exists", parent=dialog)
            return
        
        try:
            # Update user
            if change_password:
                cursor.execute("UPDATE users SET username = ?, password = ?, role = ? WHERE id = ?", 
                              (username, password, role, user_id))
            else:
                cursor.execute("UPDATE users SET username = ?, role = ? WHERE id = ?", 
                              (username, role, user_id))
            
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "User updated successfully", parent=dialog)
            
            # Close dialog and refresh users
            dialog.destroy()
            self.load_users()
        except Exception as e:
            conn.close()
            messagebox.showerror("Error", f"Failed to update user: {str(e)}", parent=dialog)
    
    def delete_user(self):
        """Delete a user"""
        # Get selected user
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a user to delete")
            return
        
        # Get user ID and name
        user_values = self.users_tree.item(selected[0], 'values')
        user_id = user_values[0]
        username = user_values[1]
        
        # Prevent deleting current user
        if int(user_id) == self.current_user["id"]:
            messagebox.showerror("Error", "You cannot delete your own account")
            return
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Delete", 
                                     f"Are you sure you want to delete user '{username}'?\n\nThis action cannot be undone.")
        if not confirm:
            return
        
        # Delete from database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", f"User '{username}' deleted successfully")
            
            # Refresh users
            self.load_users()
        except Exception as e:
            conn.close()
            messagebox.showerror("Error", f"Failed to delete user: {str(e)}")
    
    def setup_system_settings_tab(self, parent):
        """Set up the system settings tab"""
        # Create frame for settings content
        settings_content = ttk.Frame(parent, style="TFrame")
        settings_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(settings_content, text="System Settings", 
                               style="Header.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Settings form
        settings_frame = ttk.Frame(settings_content, style="TFrame")
        settings_frame.pack(fill=tk.X)
        
        # Company information
        company_frame = ttk.LabelFrame(settings_frame, text="Company Information", style="TFrame")
        company_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(company_frame, text="Company Name:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        company_name_entry = ttk.Entry(company_frame, width=40)
        company_name_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)
        company_name_entry.insert(0, "My Company")
        
        ttk.Label(company_frame, text="Address:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        address_entry = ttk.Entry(company_frame, width=40)
        address_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)
        address_entry.insert(0, "123 Main Street, City, Country")
        
        ttk.Label(company_frame, text="Phone:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        phone_entry = ttk.Entry(company_frame, width=40)
        phone_entry.grid(row=2, column=1, sticky=tk.W, padx=10, pady=10)
        phone_entry.insert(0, "+1 (555) 123-4567")
        
        ttk.Label(company_frame, text="Email:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)
        email_entry = ttk.Entry(company_frame, width=40)
        email_entry.grid(row=3, column=1, sticky=tk.W, padx=10, pady=10)
        email_entry.insert(0, "contact@mycompany.com")
        
        # Inventory settings
        inventory_frame = ttk.LabelFrame(settings_frame, text="Inventory Settings", style="TFrame")
        inventory_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(inventory_frame, text="Low Stock Threshold:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        low_stock_entry = ttk.Entry(inventory_frame, width=10)
        low_stock_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)
        low_stock_entry.insert(0, "10")
        
        ttk.Label(inventory_frame, text="Critical Stock Threshold:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        critical_stock_entry = ttk.Entry(inventory_frame, width=10)
        critical_stock_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)
        critical_stock_entry.insert(0, "5")
        
        ttk.Label(inventory_frame, text="Default Currency:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        
        currency_var = tk.StringVar(value="USD")
        currency_combo = ttk.Combobox(inventory_frame, textvariable=currency_var, 
                                     values=["USD", "EUR", "GBP", "JPY", "CAD", "AUD"], 
                                     state="readonly", width=10)
        currency_combo.grid(row=2, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Save button
        save_button = ttk.Button(settings_frame, text="Save Settings", 
                                command=lambda: messagebox.showinfo("Info", "Settings saved successfully"))
        save_button.pack(pady=20)
    
    def setup_database_backup_tab(self, parent):
        """Set up the database backup tab"""
        # Create frame for backup content
        backup_content = ttk.Frame(parent, style="TFrame")
        backup_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(backup_content, text="Database Backup and Restore", 
                               style="Header.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Backup section
        backup_frame = ttk.LabelFrame(backup_content, text="Backup Database", style="TFrame")
        backup_frame.pack(fill=tk.X, pady=(0, 20))
        
        backup_info = ttk.Label(backup_frame, 
                               text="Create a backup of your inventory database. This will save all your data to a file.")
        backup_info.pack(anchor=tk.W, padx=10, pady=(10, 20))
        
        backup_button = ttk.Button(backup_frame, text="Create Backup", 
                                  command=self.backup_database)
        backup_button.pack(padx=10, pady=(0, 20))
        
        # Restore section
        restore_frame = ttk.LabelFrame(backup_content, text="Restore Database", style="TFrame")
        restore_frame.pack(fill=tk.X, pady=(0, 20))
        
        restore_info = ttk.Label(restore_frame, 
                                text="Restore your inventory database from a backup file. This will replace all current data.")
        restore_info.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        restore_warning = ttk.Label(restore_frame, 
                                   text="Warning: This will overwrite your current database. Make sure to backup first.",
                                   foreground="red")
        restore_warning.pack(anchor=tk.W, padx=10, pady=(0, 20))
        
        restore_button = ttk.Button(restore_frame, text="Restore from Backup", 
                                   style="Danger.TButton", command=self.restore_database)
        restore_button.pack(padx=10, pady=(0, 20))
    
    def backup_database(self):
        """Create a backup of the database"""
        # Ask user for save location
        file_path = tk.filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db"), ("All files", "*.*")],
            initialfile=f"inventory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        
        if not file_path:
            return
        
        try:
            # Copy the database file
            import shutil
            shutil.copy2('inventory.db', file_path)
            
            messagebox.showinfo("Success", f"Database backup created at {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create backup: {str(e)}")
    
    def restore_database(self):
        """Restore the database from a backup"""
        # Confirm restoration
        confirm = messagebox.askyesno("Confirm Restore", 
                                     "Are you sure you want to restore the database from a backup?\n\n"
                                     "This will replace all current data and cannot be undone.")
        if not confirm:
            return
        
        # Ask user for backup file
        file_path = tk.filedialog.askopenfilename(
            filetypes=[("SQLite Database", "*.db"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # Close any open connections
            # This is a simplified approach - in a real app, you'd want to ensure all connections are closed
            
            # Copy the backup file to replace the current database
            import shutil
            shutil.copy2(file_path, 'inventory.db')
            
            messagebox.showinfo("Success", "Database restored successfully. The application will now restart.")
            
            # Restart the application
            self.logout()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore database: {str(e)}")
    
    def logout(self):
        """Log out the current user and return to login screen"""
        self.current_user = None
        self.show_login_screen()

if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryManagementSystem(root)
    root.mainloop()

