class CustomerManager:
    def __init__(self, db_manager, auth_manager):
        self.db_manager = db_manager
        self.auth_manager = auth_manager
    
    def get_all_customers(self):
        return self.db_manager.execute_query('''
        SELECT id, name, email, phone, address, tax_id, created_at
        FROM customers
        ORDER BY name
        ''')
    
    def search_customers(self, search_term=""):
        return self.db_manager.execute_query('''
        SELECT id, name, email, phone, address, tax_id, created_at
        FROM customers
        WHERE LOWER(name) LIKE ? OR LOWER(email) LIKE ? OR LOWER(phone) LIKE ?
        ORDER BY name
        ''', (f'%{search_term.lower()}%', f'%{search_term.lower()}%', f'%{search_term.lower()}%'))
    
    def get_customer(self, customer_id):
        return self.db_manager.execute_query('''
        SELECT id, name, email, phone, address, tax_id, created_at
        FROM customers
        WHERE id = ?
        ''', (customer_id,), fetchone=True)
    
    def add_customer(self, name, email, phone, address, tax_id):
        if not name:
            return False, "Customer name is required"
        
        try:
            self.db_manager.execute_query('''
            INSERT INTO customers (name, email, phone, address, tax_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, email, phone, address, tax_id, self.auth_manager.current_user["id"]))
            
            return True, "Customer added successfully"
        except Exception as e:
            return False, f"Failed to add customer: {str(e)}"
    
    def update_customer(self, customer_id, name, email, phone, address, tax_id):
        if not name:
            return False, "Customer name is required"
        
        try:
            self.db_manager.execute_query('''
            UPDATE customers
            SET name = ?, email = ?, phone = ?, address = ?, tax_id = ?
            WHERE id = ?
            ''', (name, email, phone, address, tax_id, customer_id))
            
            return True, "Customer updated successfully"
        except Exception as e:
            return False, f"Failed to update customer: {str(e)}"
    
    def delete_customer(self, customer_id):
        try:
            # Check if customer has invoices
            invoice_count = self.db_manager.execute_query(
                "SELECT COUNT(*) FROM invoices WHERE customer_id = ?", 
                (customer_id,),
                fetchone=True
            )[0]
            
            if invoice_count > 0:
                return False, f"Cannot delete customer because they have {invoice_count} invoice(s)."
            
            # Delete the customer
            self.db_manager.execute_query("DELETE FROM customers WHERE id = ?", (customer_id,))
            
            return True, "Customer deleted successfully"
        except Exception as e:
            return False, f"Failed to delete customer: {str(e)}"
    
    def get_customer_invoices(self, customer_id):
        """Get all invoices for a customer"""
        return self.db_manager.execute_query('''
        SELECT i.id, i.invoice_number, i.invoice_date, i.due_date, 
               i.total_amount, i.status
        FROM invoices i
        WHERE i.customer_id = ?
        ORDER BY i.invoice_date DESC
        ''', (customer_id,))