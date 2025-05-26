import tkinter as tk
from modules.database_manager import DatabaseManager
from modules.auth_manager import AuthManager
from modules.inventory_manager import InventoryManager
from modules.customer_manager import CustomerManager
from modules.billing_manager import BillingManager
from modules.report_manager import ReportManager
from modules.ui_manager import UIManager

class IntegratedSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Integrated Inventory & Billing System")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f5f5f5")
        
        # Initialize database and managers
        self.db_manager = DatabaseManager()
        self.auth_manager = AuthManager(self.db_manager)
        self.inventory_manager = InventoryManager(self.db_manager, self.auth_manager)
        self.customer_manager = CustomerManager(self.db_manager, self.auth_manager)
        self.billing_manager = BillingManager(self.db_manager, self.auth_manager)
        self.report_manager = ReportManager(self.db_manager)
        
        # Initialize UI manager
        self.ui_manager = UIManager(
            root=self.root,
            db_manager=self.db_manager,
            auth_manager=self.auth_manager,
            inventory_manager=self.inventory_manager,
            customer_manager=self.customer_manager,
            billing_manager=self.billing_manager,
            report_manager=self.report_manager
        )
        
        # Start with login screen
        self.ui_manager.show_login_screen()

if __name__ == "__main__":
    root = tk.Tk()
    app = IntegratedSystem(root)
    root.mainloop()