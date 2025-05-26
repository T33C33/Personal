import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime
import random
import string

class Product:
    def __init__(self, barcode, name, price, stock=0):
        self.barcode = barcode
        self.name = name
        self.price = float(price)
        self.stock = int(stock)
    
    def to_dict(self):
        return {
            'barcode': self.barcode,
            'name': self.name,
            'price': self.price,
            'stock': self.stock
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(data['barcode'], data['name'], data['price'], data['stock'])

class CartItem:
    def __init__(self, product, quantity=1):
        self.product = product
        self.quantity = quantity
    
    def get_total(self):
        return self.product.price * self.quantity

class SelfCheckoutSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Self-Checkout System")
        self.root.geometry("1200x800")
        
        # Data storage
        self.products = {}
        self.cart = []
        self.transactions = []
        
        # Load data
        self.load_products()
        self.load_transactions()
        
        # Initialize with sample products if empty
        if not self.products:
            self.initialize_sample_products()
        
        self.setup_ui()
    
    def initialize_sample_products(self):
        """Initialize with sample products"""
        sample_products = [
            Product("1234567890123", "Apple iPhone 15", 999.99, 10),
            Product("2345678901234", "Samsung Galaxy S24", 899.99, 15),
            Product("3456789012345", "Coca Cola 500ml", 2.50, 100),
            Product("4567890123456", "Bread Loaf", 3.99, 50),
            Product("5678901234567", "Milk 1L", 4.99, 30),
            Product("6789012345678", "Laptop Dell XPS", 1299.99, 5),
            Product("7890123456789", "Wireless Mouse", 29.99, 25),
            Product("8901234567890", "Coffee Beans 1kg", 15.99, 40),
        ]
        
        for product in sample_products:
            self.products[product.barcode] = product
        
        self.save_products()
    
    def setup_ui(self):
        # Create main frames
        self.create_menu()
        self.create_main_frames()
        self.create_checkout_interface()
        self.create_product_management()
        self.create_transaction_history()
        
        # Show checkout interface by default
        self.show_checkout()
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Transaction", command=self.clear_cart)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Checkout", command=self.show_checkout)
        view_menu.add_command(label="Product Management", command=self.show_product_management)
        view_menu.add_command(label="Transaction History", command=self.show_transaction_history)
    
    def create_main_frames(self):
        # Main container
        self.main_container = ttk.Notebook(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Checkout frame
        self.checkout_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.checkout_frame, text="Checkout")
        
        # Product management frame
        self.product_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.product_frame, text="Product Management")
        
        # Transaction history frame
        self.history_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.history_frame, text="Transaction History")
    
    def create_checkout_interface(self):
        # Left side - Barcode scanning and product info
        left_frame = ttk.LabelFrame(self.checkout_frame, text="Product Scanner", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Barcode entry
        ttk.Label(left_frame, text="Barcode:").pack(anchor=tk.W)
        self.barcode_var = tk.StringVar()
        self.barcode_entry = ttk.Entry(left_frame, textvariable=self.barcode_var, font=("Arial", 14))
        self.barcode_entry.pack(fill=tk.X, pady=(0, 10))
        self.barcode_entry.bind('<Return>', self.scan_product)
        
        # Scan button
        ttk.Button(left_frame, text="Scan Product", command=self.scan_product).pack(fill=tk.X, pady=(0, 10))
        
        # Manual barcode entry buttons
        ttk.Label(left_frame, text="Quick Scan (Sample Products):").pack(anchor=tk.W, pady=(10, 5))
        
        sample_frame = ttk.Frame(left_frame)
        sample_frame.pack(fill=tk.X, pady=(0, 10))
        
        sample_barcodes = ["1234567890123", "2345678901234", "3456789012345", "4567890123456"]
        for i, barcode in enumerate(sample_barcodes):
            if barcode in self.products:
                product = self.products[barcode]
                btn = ttk.Button(sample_frame, text=f"{product.name[:15]}...", 
                               command=lambda b=barcode: self.quick_scan(b))
                btn.pack(fill=tk.X, pady=1)
        
        # Product info display
        self.product_info = tk.Text(left_frame, height=8, state=tk.DISABLED)
        self.product_info.pack(fill=tk.BOTH, expand=True)
        
        # Right side - Cart and checkout
        right_frame = ttk.LabelFrame(self.checkout_frame, text="Shopping Cart", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Cart display
        cart_container = ttk.Frame(right_frame)
        cart_container.pack(fill=tk.BOTH, expand=True)
        
        # Cart treeview
        self.cart_tree = ttk.Treeview(cart_container, columns=("name", "price", "qty", "total"), show="headings", height=15)
        self.cart_tree.heading("name", text="Product")
        self.cart_tree.heading("price", text="Price")
        self.cart_tree.heading("qty", text="Qty")
        self.cart_tree.heading("total", text="Total")
        
        self.cart_tree.column("name", width=200)
        self.cart_tree.column("price", width=80)
        self.cart_tree.column("qty", width=60)
        self.cart_tree.column("total", width=80)
        
        # Scrollbar for cart
        cart_scrollbar = ttk.Scrollbar(cart_container, orient=tk.VERTICAL, command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=cart_scrollbar.set)
        
        self.cart_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cart_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Cart operations
        cart_ops_frame = ttk.Frame(right_frame)
        cart_ops_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(cart_ops_frame, text="Remove Selected", command=self.remove_from_cart).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(cart_ops_frame, text="Update Quantity", command=self.update_quantity).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(cart_ops_frame, text="Clear Cart", command=self.clear_cart).pack(side=tk.LEFT)
        
        # Total display
        total_frame = ttk.LabelFrame(right_frame, text="Order Summary", padding=10)
        total_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.subtotal_var = tk.StringVar(value="$0.00")
        self.tax_var = tk.StringVar(value="$0.00")
        self.total_var = tk.StringVar(value="$0.00")
        
        ttk.Label(total_frame, text="Subtotal:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(total_frame, textvariable=self.subtotal_var).grid(row=0, column=1, sticky=tk.E)
        
        ttk.Label(total_frame, text="Tax (8.5%):").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(total_frame, textvariable=self.tax_var).grid(row=1, column=1, sticky=tk.E)
        
        ttk.Label(total_frame, text="Total:", font=("Arial", 12, "bold")).grid(row=2, column=0, sticky=tk.W)
        ttk.Label(total_frame, textvariable=self.total_var, font=("Arial", 12, "bold")).grid(row=2, column=1, sticky=tk.E)
        
        total_frame.columnconfigure(1, weight=1)
        
        # Checkout buttons
        checkout_frame = ttk.Frame(right_frame)
        checkout_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(checkout_frame, text="Pay Cash", command=lambda: self.process_payment("Cash")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(checkout_frame, text="Pay Card", command=lambda: self.process_payment("Card")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
    
    def create_product_management(self):
        # Product management interface
        # Top frame for product operations
        top_frame = ttk.Frame(self.product_frame)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(top_frame, text="Add Product", command=self.add_product_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Edit Product", command=self.edit_product_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Delete Product", command=self.delete_product).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Refresh", command=self.refresh_product_list).pack(side=tk.LEFT)
        
        # Product list
        list_frame = ttk.Frame(self.product_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.product_tree = ttk.Treeview(list_frame, columns=("barcode", "name", "price", "stock"), show="headings")
        self.product_tree.heading("barcode", text="Barcode")
        self.product_tree.heading("name", text="Product Name")
        self.product_tree.heading("price", text="Price")
        self.product_tree.heading("stock", text="Stock")
        
        self.product_tree.column("barcode", width=150)
        self.product_tree.column("name", width=300)
        self.product_tree.column("price", width=100)
        self.product_tree.column("stock", width=100)
        
        # Scrollbar for product list
        product_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=product_scrollbar.set)
        
        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        product_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_product_list()
    
    def create_transaction_history(self):
        # Transaction history interface
        top_frame = ttk.Frame(self.history_frame)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(top_frame, text="Refresh", command=self.refresh_transaction_history).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="View Invoice", command=self.view_invoice).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Print Invoice", command=self.print_invoice).pack(side=tk.LEFT)
        
        # Transaction list
        list_frame = ttk.Frame(self.history_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.transaction_tree = ttk.Treeview(list_frame, columns=("id", "date", "items", "total", "payment"), show="headings")
        self.transaction_tree.heading("id", text="Transaction ID")
        self.transaction_tree.heading("date", text="Date & Time")
        self.transaction_tree.heading("items", text="Items")
        self.transaction_tree.heading("total", text="Total")
        self.transaction_tree.heading("payment", text="Payment Method")
        
        self.transaction_tree.column("id", width=150)
        self.transaction_tree.column("date", width=200)
        self.transaction_tree.column("items", width=100)
        self.transaction_tree.column("total", width=100)
        self.transaction_tree.column("payment", width=120)
        
        # Scrollbar for transaction list
        transaction_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.transaction_tree.yview)
        self.transaction_tree.configure(yscrollcommand=transaction_scrollbar.set)
        
        self.transaction_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        transaction_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_transaction_history()
    
    def quick_scan(self, barcode):
        self.barcode_var.set(barcode)
        self.scan_product()
    
    def scan_product(self, event=None):
        barcode = self.barcode_var.get().strip()
        if not barcode:
            messagebox.showwarning("Warning", "Please enter a barcode")
            return
        
        if barcode in self.products:
            product = self.products[barcode]
            if product.stock > 0:
                self.add_to_cart(product)
                self.display_product_info(product)
                self.barcode_var.set("")
                self.barcode_entry.focus()
            else:
                messagebox.showwarning("Out of Stock", f"{product.name} is out of stock!")
        else:
            messagebox.showerror("Product Not Found", f"No product found with barcode: {barcode}")
    
    def display_product_info(self, product):
        self.product_info.config(state=tk.NORMAL)
        self.product_info.delete(1.0, tk.END)
        
        info = f"""Product Information:
        
Name: {product.name}
Barcode: {product.barcode}
Price: ${product.price:.2f}
Stock: {product.stock} units

Product added to cart successfully!
        """
        
        self.product_info.insert(1.0, info)
        self.product_info.config(state=tk.DISABLED)
    
    def add_to_cart(self, product):
        # Check if product already in cart
        for item in self.cart:
            if item.product.barcode == product.barcode:
                if item.quantity < product.stock:
                    item.quantity += 1
                    break
                else:
                    messagebox.showwarning("Stock Limit", f"Cannot add more {product.name}. Stock limit reached.")
                    return
        else:
            # Product not in cart, add new item
            self.cart.append(CartItem(product, 1))
        
        self.update_cart_display()
        self.update_totals()
    
    def remove_from_cart(self):
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to remove")
            return
        
        item_index = self.cart_tree.index(selected[0])
        del self.cart[item_index]
        
        self.update_cart_display()
        self.update_totals()
    
    def update_quantity(self):
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to update")
            return
        
        item_index = self.cart_tree.index(selected[0])
        cart_item = self.cart[item_index]
        
        new_qty = simpledialog.askinteger("Update Quantity", 
                                        f"Enter new quantity for {cart_item.product.name}:",
                                        initialvalue=cart_item.quantity,
                                        minvalue=1,
                                        maxvalue=cart_item.product.stock)
        
        if new_qty:
            cart_item.quantity = new_qty
            self.update_cart_display()
            self.update_totals()
    
    def clear_cart(self):
        if self.cart and messagebox.askyesno("Confirm", "Are you sure you want to clear the cart?"):
            self.cart.clear()
            self.update_cart_display()
            self.update_totals()
            
            # Clear product info
            self.product_info.config(state=tk.NORMAL)
            self.product_info.delete(1.0, tk.END)
            self.product_info.config(state=tk.DISABLED)
    
    def update_cart_display(self):
        # Clear current display
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        # Add cart items
        for cart_item in self.cart:
            self.cart_tree.insert("", tk.END, values=(
                cart_item.product.name,
                f"${cart_item.product.price:.2f}",
                cart_item.quantity,
                f"${cart_item.get_total():.2f}"
            ))
    
    def update_totals(self):
        subtotal = sum(item.get_total() for item in self.cart)
        tax = subtotal * 0.085  # 8.5% tax
        total = subtotal + tax
        
        self.subtotal_var.set(f"${subtotal:.2f}")
        self.tax_var.set(f"${tax:.2f}")
        self.total_var.set(f"${total:.2f}")
    
    def process_payment(self, payment_method):
        if not self.cart:
            messagebox.showwarning("Warning", "Cart is empty!")
            return
        
        # Calculate totals
        subtotal = sum(item.get_total() for item in self.cart)
        tax = subtotal * 0.085
        total = subtotal + tax
        
        # Handle cash payment
        if payment_method == "Cash":
            cash_amount = simpledialog.askfloat("Cash Payment", 
                                              f"Total: ${total:.2f}\nEnter cash amount:",
                                              minvalue=total)
            if cash_amount is None:
                return
            
            change = cash_amount - total
            messagebox.showinfo("Payment Successful", 
                              f"Payment received: ${cash_amount:.2f}\nChange: ${change:.2f}")
        else:
            # Card payment simulation
            if messagebox.askyesno("Card Payment", f"Process card payment of ${total:.2f}?"):
                messagebox.showinfo("Payment Successful", "Card payment processed successfully!")
            else:
                return
        
        # Create transaction record
        transaction_id = self.generate_transaction_id()
        transaction = {
            'id': transaction_id,
            'date': datetime.now().isoformat(),
            'items': [{'name': item.product.name, 'price': item.product.price, 
                      'quantity': item.quantity, 'total': item.get_total()} for item in self.cart],
            'subtotal': subtotal,
            'tax': tax,
            'total': total,
            'payment_method': payment_method
        }
        
        # Update stock
        for cart_item in self.cart:
            self.products[cart_item.product.barcode].stock -= cart_item.quantity
        
        # Save transaction
        self.transactions.append(transaction)
        self.save_transactions()
        self.save_products()
        
        # Generate and show invoice
        self.generate_invoice(transaction)
        
        # Clear cart
        self.cart.clear()
        self.update_cart_display()
        self.update_totals()
        
        messagebox.showinfo("Transaction Complete", f"Transaction {transaction_id} completed successfully!")
    
    def generate_transaction_id(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def generate_invoice(self, transaction):
        invoice_text = f"""
{'='*50}
           SELF-CHECKOUT SYSTEM
                 INVOICE
{'='*50}

Transaction ID: {transaction['id']}
Date: {datetime.fromisoformat(transaction['date']).strftime('%Y-%m-%d %H:%M:%S')}
Payment Method: {transaction['payment_method']}

{'='*50}
ITEMS:
{'='*50}
"""
        
        for item in transaction['items']:
            invoice_text += f"{item['name']:<30} x{item['quantity']:<3} ${item['total']:.2f}\n"
            invoice_text += f"  @ ${item['price']:.2f} each\n\n"
        
        invoice_text += f"""{'='*50}
Subtotal:                    ${transaction['subtotal']:.2f}
Tax (8.5%):                  ${transaction['tax']:.2f}
{'='*50}
TOTAL:                       ${transaction['total']:.2f}
{'='*50}

Thank you for shopping with us!
"""
        
        # Show invoice in a new window
        invoice_window = tk.Toplevel(self.root)
        invoice_window.title(f"Invoice - {transaction['id']}")
        invoice_window.geometry("600x500")
        
        text_widget = tk.Text(invoice_window, font=("Courier", 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, invoice_text)
        text_widget.config(state=tk.DISABLED)
        
        # Save invoice to file
        if not os.path.exists("invoices"):
            os.makedirs("invoices")
        
        with open(f"invoices/invoice_{transaction['id']}.txt", "w") as f:
            f.write(invoice_text)
    
    # Product Management Methods
    def add_product_dialog(self):
        dialog = ProductDialog(self.root, "Add Product")
        if dialog.result:
            product_data = dialog.result
            if product_data['barcode'] in self.products:
                messagebox.showerror("Error", "Product with this barcode already exists!")
                return
            
            product = Product(**product_data)
            self.products[product.barcode] = product
            self.save_products()
            self.refresh_product_list()
            messagebox.showinfo("Success", "Product added successfully!")
    
    def edit_product_dialog(self):
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a product to edit")
            return
        
        item_values = self.product_tree.item(selected[0])['values']
        barcode = item_values[0]
        product = self.products[barcode]
        
        dialog = ProductDialog(self.root, "Edit Product", product)
        if dialog.result:
            product_data = dialog.result
            
            # Update product
            product.name = product_data['name']
            product.price = product_data['price']
            product.stock = product_data['stock']
            
            self.save_products()
            self.refresh_product_list()
            messagebox.showinfo("Success", "Product updated successfully!")
    
    def delete_product(self):
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a product to delete")
            return
        
        item_values = self.product_tree.item(selected[0])['values']
        barcode = item_values[0]
        product_name = item_values[1]
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{product_name}'?"):
            del self.products[barcode]
            self.save_products()
            self.refresh_product_list()
            messagebox.showinfo("Success", "Product deleted successfully!")
    
    def refresh_product_list(self):
        # Clear current display
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        # Add products
        for product in self.products.values():
            self.product_tree.insert("", tk.END, values=(
                product.barcode,
                product.name,
                f"${product.price:.2f}",
                product.stock
            ))
    
    # Transaction History Methods
    def refresh_transaction_history(self):
        # Clear current display
        for item in self.transaction_tree.get_children():
            self.transaction_tree.delete(item)
        
        # Add transactions (most recent first)
        for transaction in reversed(self.transactions):
            date_str = datetime.fromisoformat(transaction['date']).strftime('%Y-%m-%d %H:%M:%S')
            item_count = len(transaction['items'])
            
            self.transaction_tree.insert("", tk.END, values=(
                transaction['id'],
                date_str,
                item_count,
                f"${transaction['total']:.2f}",
                transaction['payment_method']
            ))
    
    def view_invoice(self):
        selected = self.transaction_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a transaction to view")
            return
        
        item_values = self.transaction_tree.item(selected[0])['values']
        transaction_id = item_values[0]
        
        # Find transaction
        transaction = next((t for t in self.transactions if t['id'] == transaction_id), None)
        if transaction:
            self.generate_invoice(transaction)
    
    def print_invoice(self):
        selected = self.transaction_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a transaction to print")
            return
        
        item_values = self.transaction_tree.item(selected[0])['values']
        transaction_id = item_values[0]
        
        invoice_file = f"invoices/invoice_{transaction_id}.txt"
        if os.path.exists(invoice_file):
            messagebox.showinfo("Print", f"Invoice saved to: {invoice_file}\n(In a real system, this would send to printer)")
        else:
            messagebox.showerror("Error", "Invoice file not found!")
    
    # Navigation Methods
    def show_checkout(self):
        self.main_container.select(0)
    
    def show_product_management(self):
        self.main_container.select(1)
    
    def show_transaction_history(self):
        self.main_container.select(2)
        self.refresh_transaction_history()
    
    # Data Persistence Methods
    def save_products(self):
        data = {barcode: product.to_dict() for barcode, product in self.products.items()}
        with open("products.json", "w") as f:
            json.dump(data, f, indent=2)
    
    def load_products(self):
        try:
            with open("products.json", "r") as f:
                data = json.load(f)
                self.products = {barcode: Product.from_dict(product_data) 
                               for barcode, product_data in data.items()}
        except FileNotFoundError:
            self.products = {}
    
    def save_transactions(self):
        with open("transactions.json", "w") as f:
            json.dump(self.transactions, f, indent=2)
    
    def load_transactions(self):
        try:
            with open("transactions.json", "r") as f:
                self.transactions = json.load(f)
        except FileNotFoundError:
            self.transactions = []

class ProductDialog:
    def __init__(self, parent, title, product=None):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Create form
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Barcode
        ttk.Label(main_frame, text="Barcode:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.barcode_var = tk.StringVar(value=product.barcode if product else "")
        barcode_entry = ttk.Entry(main_frame, textvariable=self.barcode_var, width=30)
        barcode_entry.grid(row=0, column=1, pady=5, sticky=tk.W)
        if product:  # Disable barcode editing for existing products
            barcode_entry.config(state=tk.DISABLED)
        
        # Name
        ttk.Label(main_frame, text="Product Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=product.name if product else "")
        ttk.Entry(main_frame, textvariable=self.name_var, width=30).grid(row=1, column=1, pady=5, sticky=tk.W)
        
        # Price
        ttk.Label(main_frame, text="Price:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.price_var = tk.StringVar(value=str(product.price) if product else "")
        ttk.Entry(main_frame, textvariable=self.price_var, width=30).grid(row=2, column=1, pady=5, sticky=tk.W)
        
        # Stock
        ttk.Label(main_frame, text="Stock:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.stock_var = tk.StringVar(value=str(product.stock) if product else "")
        ttk.Entry(main_frame, textvariable=self.stock_var, width=30).grid(row=3, column=1, pady=5, sticky=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        # Focus on first entry
        if not product:
            barcode_entry.focus()
        else:
            main_frame.children['!entry2'].focus()  # Focus on name entry
    
    def save(self):
        try:
            barcode = self.barcode_var.get().strip()
            name = self.name_var.get().strip()
            price = float(self.price_var.get())
            stock = int(self.stock_var.get())
            
            if not barcode or not name:
                messagebox.showerror("Error", "Barcode and name are required!")
                return
            
            if price < 0 or stock < 0:
                messagebox.showerror("Error", "Price and stock must be non-negative!")
                return
            
            self.result = {
                'barcode': barcode,
                'name': name,
                'price': price,
                'stock': stock
            }
            
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for price and stock!")
    
    def cancel(self):
        self.dialog.destroy()

# Main application
if __name__ == "__main__":
    root = tk.Tk()
    app = SelfCheckoutSystem(root)
    root.mainloop()