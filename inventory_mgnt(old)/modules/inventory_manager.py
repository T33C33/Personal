class InventoryManager:
    def __init__(self, db_manager, auth_manager):
        self.db_manager = db_manager
        self.auth_manager = auth_manager
    
    def get_all_items(self):
        return self.db_manager.execute_query('''
        SELECT id, item_name, description, category, quantity, unit_price, supplier, last_updated
        FROM inventory
        ORDER BY item_name
        ''')
    
    def search_items(self, search_term="", category="All"):
        if category == "All":
            return self.db_manager.execute_query('''
            SELECT id, item_name, description, category, quantity, unit_price, supplier, last_updated
            FROM inventory
            WHERE LOWER(item_name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(supplier) LIKE ?
            ORDER BY item_name
            ''', (f'%{search_term.lower()}%', f'%{search_term.lower()}%', f'%{search_term.lower()}%'))
        else:
            return self.db_manager.execute_query('''
            SELECT id, item_name, description, category, quantity, unit_price, supplier, last_updated
            FROM inventory
            WHERE (LOWER(item_name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(supplier) LIKE ?)
            AND category = ?
            ORDER BY item_name
            ''', (f'%{search_term.lower()}%', f'%{search_term.lower()}%', f'%{search_term.lower()}%', category))
    
    def get_categories(self):
        categories = self.db_manager.execute_query("SELECT DISTINCT category FROM inventory ORDER BY category")
        return [row[0] for row in categories]
    
    def add_item(self, name, description, category, quantity, price, supplier):
        if not name or not category:
            return False, "Item name and category are required"
        
        try:
            quantity = int(quantity)
            if quantity < 0:
                raise ValueError()
        except ValueError:
            return False, "Quantity must be a positive number"
        
        try:
            price = float(price)
            if price < 0:
                raise ValueError()
        except ValueError:
            return False, "Price must be a positive number"
        
        try:
            # Insert new item
            self.db_manager.execute_query('''
            INSERT INTO inventory (item_name, description, category, quantity, unit_price, supplier, updated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, description, category, quantity, price, supplier, self.auth_manager.current_user["id"]))
            
            # Get the ID of the new item
            item_id = self.db_manager.execute_query("SELECT last_insert_rowid()", fetchone=True)[0]
            
            # Add transaction record
            self.db_manager.execute_query('''
            INSERT INTO transactions (item_id, transaction_type, quantity, user_id, notes)
            VALUES (?, ?, ?, ?, ?)
            ''', (item_id, 'in', quantity, self.auth_manager.current_user["id"], "Initial stock"))
            
            return True, "Item added successfully"
        except Exception as e:
            return False, f"Failed to add item: {str(e)}"
    
    def update_item(self, item_id, name, description, category, quantity, price, supplier):
        if not name or not category:
            return False, "Item name and category are required"
        
        try:
            quantity = int(quantity)
            if quantity < 0:
                raise ValueError()
        except ValueError:
            return False, "Quantity must be a positive number"
        
        try:
            price = float(price)
            if price < 0:
                raise ValueError()
        except ValueError:
            return False, "Price must be a positive number"
        
        try:
            # Get current quantity
            current_qty = self.db_manager.execute_query(
                "SELECT quantity FROM inventory WHERE id = ?", 
                (item_id,),
                fetchone=True
            )[0]
            
            # Update inventory item
            self.db_manager.execute_query('''
            UPDATE inventory
            SET item_name = ?, description = ?, category = ?, quantity = ?, 
                unit_price = ?, supplier = ?, last_updated = CURRENT_TIMESTAMP,
                updated_by = ?
            WHERE id = ?
            ''', (name, description, category, quantity, price, supplier, 
                 self.auth_manager.current_user["id"], item_id))
            
            # If quantity changed, add a transaction record
            if quantity != current_qty:
                qty_diff = quantity - current_qty
                tx_type = 'in' if qty_diff > 0 else 'out'
                
                self.db_manager.execute_query('''
                INSERT INTO transactions (item_id, transaction_type, quantity, user_id, notes)
                VALUES (?, ?, ?, ?, ?)
                ''', (item_id, tx_type, abs(qty_diff), self.auth_manager.current_user["id"], "Manual adjustment"))
            
            return True, "Item updated successfully"
        except Exception as e:
            return False, f"Failed to update item: {str(e)}"
    
    def delete_item(self, item_id):
        try:
            # Check if item is used in any invoices
            invoice_count = self.db_manager.execute_query(
                "SELECT COUNT(*) FROM invoice_items WHERE item_id = ?", 
                (item_id,),
                fetchone=True
            )[0]
            
            if invoice_count > 0:
                return False, f"Cannot delete item because it is used in {invoice_count} invoice(s)."
            
            # First delete related transactions
            self.db_manager.execute_query("DELETE FROM transactions WHERE item_id = ?", (item_id,))
            
            # Then delete the item
            self.db_manager.execute_query("DELETE FROM inventory WHERE id = ?", (item_id,))
            
            return True, "Item deleted successfully"
        except Exception as e:
            return False, f"Failed to delete item: {str(e)}"
    
    def add_transaction(self, item_id, transaction_type, quantity, notes=""):
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return False, "Quantity must be a positive number"
            
            # Get current quantity
            current_qty = self.db_manager.execute_query(
                "SELECT quantity FROM inventory WHERE id = ?", 
                (item_id,),
                fetchone=True
            )[0]
            
            # Calculate new quantity
            new_qty = current_qty + quantity if transaction_type == 'in' else current_qty - quantity
            
            # Check if enough stock for out transaction
            if transaction_type == 'out' and new_qty < 0:
                return False, "Not enough stock available"
            
            # Update inventory quantity
            self.db_manager.execute_query(
                "UPDATE inventory SET quantity = ?, last_updated = CURRENT_TIMESTAMP, updated_by = ? WHERE id = ?",
                (new_qty, self.auth_manager.current_user["id"], item_id)
            )
            
            # Add transaction record
            self.db_manager.execute_query('''
            INSERT INTO transactions (item_id, transaction_type, quantity, user_id, notes)
            VALUES (?, ?, ?, ?, ?)
            ''', (item_id, transaction_type, quantity, self.auth_manager.current_user["id"], notes))
            
            return True, "Transaction recorded successfully"
        except Exception as e:
            return False, f"Failed to record transaction: {str(e)}"
    
    def get_transactions(self, from_date=None, to_date=None, transaction_type=None, item_id=None):
        """Get transactions with optional filters"""
        query = '''
        SELECT t.id, t.transaction_date, i.item_name, t.transaction_type, 
               t.quantity, u.username, t.notes
        FROM transactions t
        JOIN inventory i ON t.item_id = i.id
        JOIN users u ON t.user_id = u.id
        '''
        
        params = []
        where_clauses = []
        
        if from_date:
            where_clauses.append("t.transaction_date >= ?")
            params.append(from_date)
        
        if to_date:
            where_clauses.append("t.transaction_date <= ?")
            params.append(to_date)
        
        if transaction_type and transaction_type != "All":
            where_clauses.append("t.transaction_type = ?")
            params.append(transaction_type.lower())
        
        if item_id:
            where_clauses.append("t.item_id = ?")
            params.append(item_id)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY t.transaction_date DESC"
        
        return self.db_manager.execute_query(query, tuple(params))