import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name='integrated_system.db'):
        self.db_name = db_name
        self.create_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def execute_query(self, query, params=(), fetchone=False, commit=True):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            if commit:
                conn.commit()
            if fetchone:
                return cursor.fetchone()
            return cursor.fetchall()
        except Exception as e:
            if commit:
                conn.rollback()
            raise e
        finally:
            conn.close()
    
    def create_database(self):
        # Create users table
        self.execute_query('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Create inventory table
        self.execute_query('''
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
        )''')
        
        # Create transactions table
        self.execute_query('''
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
        )''')
        
        # Create customers table
        self.execute_query('''
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
        )''')
        
        # Create invoices table
        self.execute_query('''
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
        )''')
        
        # Create invoice_items table
        self.execute_query('''
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
        )''')
        
        # Create payments table
        self.execute_query('''
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
        )''')
        
        # Create system_settings table
        self.execute_query('''
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_name TEXT UNIQUE NOT NULL,
            setting_value TEXT
        )''')
        
        # Insert default admin user if not exists
        admin_count = self.execute_query("SELECT COUNT(*) FROM users WHERE username = 'admin'", fetchone=True)[0]
        if admin_count == 0:
            self.execute_query("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                              ('admin', 'admin123', 'admin'))
        
        # Insert sample inventory data if table is empty
        inventory_count = self.execute_query("SELECT COUNT(*) FROM inventory", fetchone=True)[0]
        if inventory_count == 0:
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
            
            for item in sample_items:
                self.execute_query('''
                INSERT INTO inventory (item_name, description, category, quantity, unit_price, supplier)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', item)
        
        # Insert default settings if not exists
        settings_count = self.execute_query("SELECT COUNT(*) FROM system_settings", fetchone=True)[0]
        if settings_count == 0:
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
                ('currency_symbol', 'N'),
                ('reminder_days_before', '3,7,14')
            ]
            for setting in default_settings:
                self.execute_query('''
                INSERT INTO system_settings (setting_name, setting_value)
                VALUES (?, ?)
                ''', setting)
    
    def get_setting(self, setting_name):
        """Get a system setting value"""
        result = self.execute_query(
            "SELECT setting_value FROM system_settings WHERE setting_name = ?", 
            (setting_name,), 
            fetchone=True
        )
        
        if result:
            return result[0]
        else:
            # Default values
            defaults = {
                'currency_symbol': 'N',
                'default_tax_rate': '7.5',
                'default_due_days': '30',
                'invoice_prefix': 'INV-',
                'invoice_starting_number': '1001'
            }
            return defaults.get(setting_name, '')
    
    def update_setting(self, setting_name, setting_value):
        """Update a system setting"""
        self.execute_query(
            "INSERT OR REPLACE INTO system_settings (setting_name, setting_value) VALUES (?, ?)",
            (setting_name, setting_value)
        )
        return True