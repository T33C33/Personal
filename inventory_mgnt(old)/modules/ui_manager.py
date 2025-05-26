import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import os
import csv

class UIManager:
    def __init__(self, root, db_manager, auth_manager, inventory_manager, customer_manager, billing_manager, report_manager):
        self.root = root
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.inventory_manager = inventory_manager
        self.customer_manager = customer_manager
        self.billing_manager = billing_manager
        self.report_manager = report_manager
        
        # Set app theme
        self.setup_styles()
        
        # Variables
        self.search_var = tk.StringVar()
        self.category_var = tk.StringVar()
    
    def setup_styles(self):
        """Set up the application styles"""
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
    
    def show_login_screen(self):
        """Display the login screen"""
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create login frame
        login_frame = ttk.Frame(self.root, padding="30 30 30 30")
        login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title
        title_label = ttk.Label(login_frame, text="Integrated Management System", 
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
        
        success, message = self.auth_manager.login(username, password)
        
        if success:
            self.show_main_application()
        else:
            messagebox.showerror("Login Failed", message)
    
    def register(self):
        """Register a new user"""
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()
        confirm = self.reg_confirm_entry.get()
        role = self.role_var.get()
        
        success, message = self.auth_manager.register(username, password, confirm, role)
        
        if success:
            messagebox.showinfo("Success", message + "! You can now login.")
            self.show_login_screen()
        else:
            messagebox.showerror("Error", message)
    
    def logout(self):
        """Log out the current user and return to login screen"""
        self.auth_manager.logout()
        self.show_login_screen()
    
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
        title_label = ttk.Label(header_frame, text="Integrated Management System", 
                               style="Header.TLabel", font=("Helvetica", 18, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # User info and logout
        user_frame = ttk.Frame(header_frame, style="TFrame")
        user_frame.pack(side=tk.RIGHT)
        
        user_label = ttk.Label(user_frame, 
                              text=f"Logged in as: {self.auth_manager.current_user['username']} ({self.auth_manager.current_user['role']})")
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
        
        # Billing tab
        self.billing_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.billing_tab, text="Billing")
        
        # Customers tab
        self.customers_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.customers_tab, text="Customers")
        
        # Reports tab
        self.reports_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.reports_tab, text="Reports")
        
        # Admin tab (only for admin users)
        if self.auth_manager.current_user["role"] == "admin":
            self.admin_tab = ttk.Frame(self.tab_control)
            self.tab_control.add(self.admin_tab, text="Admin")
        
        # Initialize tabs
        self.setup_dashboard_tab()
        self.setup_inventory_tab()
        self.setup_transactions_tab()
        self.setup_billing_tab()
        self.setup_customers_tab()
        self.setup_reports_tab()
        
        if self.auth_manager.current_user["role"] == "admin":
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
                                 text=f"Welcome, {self.auth_manager.current_user['username']}!", 
                                 font=("Helvetica", 16, "bold"))
        welcome_label.pack(anchor=tk.W)
        
        date_label = ttk.Label(welcome_frame, 
                              text=f"Today is {datetime.now().strftime('%A, %B %d, %Y')}")
        date_label.pack(anchor=tk.W)
        
        # Stats cards
        stats_frame = ttk.Frame(dashboard_content, style="TFrame")
        stats_frame.pack(fill=tk.X, pady=20)
        
        # Get stats from database
        conn = self.db_manager.get_connection()
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
        
        # Total invoices
        cursor.execute("SELECT COUNT(*) FROM invoices")
        total_invoices = cursor.fetchone()[0] or 0
        
        # Total sales
        cursor.execute("SELECT SUM(total_amount) FROM invoices")
        total_sales = cursor.fetchone()[0] or 0
        
        # Outstanding invoices
        cursor.execute("SELECT COUNT(*) FROM invoices WHERE status IN ('Unpaid', 'Partial', 'Overdue')")
        outstanding_invoices = cursor.fetchone()[0] or 0
        
        conn.close()
        
        # Get currency symbol
        currency_symbol = self.db_manager.get_setting('currency_symbol')
        
        # Configure grid for stats cards
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)
        stats_frame.rowconfigure(0, weight=1)
        stats_frame.rowconfigure(1, weight=1)
        
        # Create stat cards
        self.create_stat_card(stats_frame, "Total Items", f"{total_items:,}", "#4CAF50", 0, 0)
        self.create_stat_card(stats_frame, "Inventory Value", f"{currency_symbol}{total_value:,.2f}", "#2196F3", 0, 1)
        self.create_stat_card(stats_frame, "Low Stock Items", f"{low_stock}", "#f44336" if low_stock > 0 else "#4CAF50", 0, 2)
        self.create_stat_card(stats_frame, "Total Invoices", f"{total_invoices}", "#FF9800", 1, 0)
        self.create_stat_card(stats_frame, "Total Sales", f"{currency_symbol}{total_sales:,.2f}", "#9C27B0", 1, 1)
        self.create_stat_card(stats_frame, "Outstanding Invoices", f"{outstanding_invoices}", "#f44336" if outstanding_invoices > 0 else "#4CAF50", 1, 2)
        
        # Quick actions
        actions_frame = ttk.LabelFrame(dashboard_content, text="Quick Actions", style="TFrame")
        actions_frame.pack(fill=tk.X, pady=20)
        
        add_item_btn = ttk.Button(actions_frame, text="Add New Item", 
                                 command=lambda: self.tab_control.select(self.inventory_tab))
        add_item_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        create_invoice_btn = ttk.Button(actions_frame, text="Create Invoice", 
                                       command=lambda: self.tab_control.select(self.billing_tab))
        create_invoice_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        add_customer_btn = ttk.Button(actions_frame, text="Add Customer", 
                                     command=lambda: self.tab_control.select(self.customers_tab))
        add_customer_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        report_btn = ttk.Button(actions_frame, text="Generate Report", 
                               command=lambda: self.tab_control.select(self.reports_tab))
        report_btn.pack(side=tk.LEFT, padx=10, pady=10)
    
    def create_stat_card(self, parent, title, value, color, row, col):
        """Create a statistics card for the dashboard"""
        card = ttk.Frame(parent, style="TFrame", relief=tk.RAISED)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Card content
        value_label = ttk.Label(card, text=value, font=("Helvetica", 24, "bold"))
        value_label.pack(pady=(20, 5))
        
        title_label = ttk.Label(card, text=title, font=("Helvetica", 12))
        title_label.pack(pady=(5, 20))
        
        # Add colored indicator
        indicator = ttk.Frame(card, height=5, style="TFrame")
        indicator.pack(fill=tk.X, side=tk.BOTTOM)
        
        # We can't directly set background color with ttk, so we'll use a Canvas
        canvas = tk.Canvas(indicator, height=5, bg=color, highlightthickness=0)
        canvas.pack(fill=tk.X)
    
    def setup_inventory_tab(self):
        """Set up the inventory tab with item listing and management"""
        # Implementation details for inventory tab
        pass
    
    def setup_transactions_tab(self):
        """Set up the transactions tab with transaction history"""
        # Implementation details for transactions tab
        pass
    
    def setup_billing_tab(self):
        """Set up the billing tab with invoice management"""
        # Implementation details for billing tab
        pass
    
    def setup_customers_tab(self):
        """Set up the customers tab with customer management"""
        # Implementation details for customers tab
        pass
    
    def setup_reports_tab(self):
        """Set up the reports tab with reporting options"""
        # Implementation details for reports tab
        pass
    
    def setup_admin_tab(self):
        """Set up the admin tab with system settings and user management"""
        # Implementation details for admin tab
        pass