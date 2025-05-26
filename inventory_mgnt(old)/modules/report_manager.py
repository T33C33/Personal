import csv
from datetime import datetime

class ReportManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_inventory_report(self, category=None, low_stock=False):
        query = '''
        SELECT i.id, i.item_name, i.description, i.category, i.quantity, 
               i.unit_price, i.quantity * i.unit_price as total_value, i.supplier
        FROM inventory i
        '''
        
        params = []
        where_clauses = []
        
        if category and category != "All":
            where_clauses.append("i.category = ?")
            params.append(category)
        
        if low_stock:
            where_clauses.append("i.quantity < 10")
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY i.category, i.item_name"
        
        return self.db_manager.execute_query(query, tuple(params))
    
    def get_sales_report(self, start_date, end_date, customer_id=None):
        query = '''
        SELECT i.id, i.invoice_number, i.invoice_date, c.name as customer_name,
               i.subtotal, i.tax_amount, i.discount_amount, i.total_amount, i.status
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.invoice_date BETWEEN ? AND ?
        '''
        
        params = [start_date, end_date]
        
        if customer_id:
            query += " AND i.customer_id = ?"
            params.append(customer_id)
        
        query += " ORDER BY i.invoice_date"
        
        return self.db_manager.execute_query(query, tuple(params))
    
    def get_payment_report(self, start_date, end_date, payment_method=None):
        query = '''
        SELECT p.id, i.invoice_number, p.payment_date, c.name as customer_name,
               p.amount, p.payment_method, p.reference_number
        FROM payments p
        JOIN invoices i ON p.invoice_id = i.id
        JOIN customers c ON i.customer_id = c.id
        WHERE p.payment_date BETWEEN ? AND ?
        '''
        
        params = [start_date, end_date]
        
        if payment_method and payment_method != "All":
            query += " AND p.payment_method = ?"
            params.append(payment_method)
        
        query += " ORDER BY p.payment_date"
        
        return self.db_manager.execute_query(query, tuple(params))
    
    def get_transaction_report(self, start_date, end_date, transaction_type=None):
        query = '''
        SELECT t.id, t.transaction_date, i.item_name, t.transaction_type,
               t.quantity, u.username, t.notes
        FROM transactions t
        JOIN inventory i ON t.item_id = i.id
        JOIN users u ON t.user_id = u.id
        WHERE t.transaction_date BETWEEN ? AND ?
        '''
        
        params = [start_date, end_date]
        
        if transaction_type and transaction_type != "All":
            query += " AND t.transaction_type = ?"
            params.append(transaction_type)
        
        query += " ORDER BY t.transaction_date"
        
        return self.db_manager.execute_query(query, tuple(params))
    
    def get_profit_report(self, start_date, end_date):
        """Calculate profit for a given period"""
        # Get total sales
        sales_query = '''
        SELECT SUM(total_amount) as total_sales
        FROM invoices
        WHERE invoice_date BETWEEN ? AND ?
        AND status != 'Void'
        '''
        
        total_sales = self.db_manager.execute_query(sales_query, (start_date, end_date), fetchone=True)[0] or 0
        
        # Get cost of goods sold
        cogs_query = '''
        SELECT SUM(ii.quantity * inv.unit_price) as total_cost
        FROM invoice_items ii
        JOIN invoices i ON ii.invoice_id = i.id
        JOIN inventory inv ON ii.item_id = inv.id
        WHERE i.invoice_date BETWEEN ? AND ?
        AND i.status != 'Void'
        '''
        
        total_cost = self.db_manager.execute_query(cogs_query, (start_date, end_date), fetchone=True)[0] or 0
        
        # Calculate profit
        gross_profit = total_sales - total_cost
        
        return {
            'total_sales': total_sales,
            'total_cost': total_cost,
            'gross_profit': gross_profit,
            'profit_margin': (gross_profit / total_sales * 100) if total_sales > 0 else 0
        }
    
    def export_report_to_csv(self, data, headers, filename):
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                for row in data:
                    writer.writerow(row)
            return True, f"Report exported successfully to {filename}"
        except Exception as e:
            return False, f"Failed to export report: {str(e)}"