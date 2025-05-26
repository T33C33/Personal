import re
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

class BillingManager:
    def __init__(self, db_manager, auth_manager):
        self.db_manager = db_manager
        self.auth_manager = auth_manager
    
    def get_all_invoices(self):
        return self.db_manager.execute_query('''
        SELECT i.id, i.invoice_number, c.name as customer_name, i.invoice_date, 
               i.due_date, i.total_amount, i.status
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        ORDER BY i.invoice_date DESC
        ''')
    
    def search_invoices(self, search_term="", status="All", from_date=None, to_date=None, customer_id=None):
        query = '''
        SELECT i.id, i.invoice_number, c.name as customer_name, i.invoice_date, 
               i.due_date, i.total_amount, i.status
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        '''
        
        params = []
        where_clauses = []
        
        if search_term:
            where_clauses.append("(LOWER(i.invoice_number) LIKE ? OR LOWER(c.name) LIKE ?)")
            params.extend([f'%{search_term.lower()}%', f'%{search_term.lower()}%'])
        
        if status != "All":
            where_clauses.append("i.status = ?")
            params.append(status)
        
        if from_date:
            where_clauses.append("i.invoice_date >= ?")
            params.append(from_date)
        
        if to_date:
            where_clauses.append("i.invoice_date <= ?")
            params.append(to_date)
        
        if customer_id:
            where_clauses.append("i.customer_id = ?")
            params.append(customer_id)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY i.invoice_date DESC"
        
        return self.db_manager.execute_query(query, tuple(params))
    
    def get_invoice_details(self, invoice_id):
        # Get invoice header
        invoice = self.db_manager.execute_query('''
        SELECT i.*, c.name as customer_name, c.email, c.phone, c.address, c.tax_id
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.id = ?
        ''', (invoice_id,), fetchone=True)
        
        # Get invoice items
        items = self.db_manager.execute_query('''
        SELECT ii.*, inv.item_name
        FROM invoice_items ii
        JOIN inventory inv ON ii.item_id = inv.id
        WHERE ii.invoice_id = ?
        ''', (invoice_id,))
        
        # Get payments
        payments = self.db_manager.execute_query('''
        SELECT p.*, u.username
        FROM payments p
        JOIN users u ON p.recorded_by = u.id
        WHERE p.invoice_id = ?
        ORDER BY p.payment_date
        ''', (invoice_id,))
        
        return invoice, items, payments
    
    def create_invoice(self, customer_id, items, invoice_date, due_date, tax_rate, discount_rate, notes=""):
        try:
            # Validate inputs
            if not customer_id:
                return False, "Customer is required", None
            
            if not items:
                return False, "No items added to invoice", None
            
            try:
                tax_rate = float(tax_rate)
                if tax_rate < 0:
                    raise ValueError()
            except ValueError:
                return False, "Tax rate must be a non-negative number", None
            
            try:
                discount_rate = float(discount_rate)
                if discount_rate < 0:
                    raise ValueError()
            except ValueError:
                return False, "Discount rate must be a non-negative number", None
            
            # Calculate totals
            subtotal = sum(item['quantity'] * item['unit_price'] for item in items)
            tax_amount = subtotal * (tax_rate / 100)
            discount_amount = subtotal * (discount_rate / 100)
            total_amount = subtotal + tax_amount - discount_amount
            
            # Generate invoice number
            prefix = self.db_manager.get_setting('invoice_prefix')
            next_num = int(self.db_manager.get_setting('invoice_starting_number'))
            
            # Check if we need to increment the next number
            last_invoice = self.db_manager.execute_query(
                "SELECT invoice_number FROM invoices ORDER BY id DESC LIMIT 1",
                fetchone=True
            )
            
            if last_invoice:
                # Extract number from last invoice
                last_num = int(re.search(r'\d+', last_invoice[0]).group())
                next_num = max(next_num, last_num + 1)
            
            invoice_number = f"{prefix}{next_num}"
            
            # Create invoice
            self.db_manager.execute_query('''
            INSERT INTO invoices (
                invoice_number, customer_id, invoice_date, due_date, subtotal, tax_rate, tax_amount,
                discount_rate, discount_amount, total_amount, notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                invoice_number, customer_id, invoice_date, due_date, subtotal, tax_rate, tax_amount,
                discount_rate, discount_amount, total_amount, notes, self.auth_manager.current_user["id"]
            ))
            
            # Get the ID of the new invoice
            invoice_id = self.db_manager.execute_query("SELECT last_insert_rowid()", fetchone=True)[0]
            
            # Add invoice items
            for item in items:
                self.db_manager.execute_query('''
                INSERT INTO invoice_items (
                    invoice_id, item_id, description, quantity, unit_price, total_price
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    invoice_id, item['id'], item.get('description', ''),
                    item['quantity'], item['unit_price'], item['quantity'] * item['unit_price']
                ))
                
                # Update inventory (reduce stock)
                self.db_manager.execute_query('''
                UPDATE inventory 
                SET quantity = quantity - ?, last_updated = CURRENT_TIMESTAMP, updated_by = ? 
                WHERE id = ?
                ''', (item['quantity'], self.auth_manager.current_user["id"], item['id']))
                
                # Add transaction record
                self.db_manager.execute_query('''
                INSERT INTO transactions (item_id, transaction_type, quantity, user_id, notes)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    item['id'], 'out', item['quantity'], 
                    self.auth_manager.current_user["id"], f"Invoice #{invoice_number}"
                ))
            
            return True, f"Invoice #{invoice_number} created successfully", invoice_id
        except Exception as e:
            return False, f"Failed to create invoice: {str(e)}", None
    
    def record_payment(self, invoice_id, amount, payment_method, reference_number, payment_date=None, notes=""):
        try:
            # Validate inputs
            try:
                amount = float(amount)
                if amount <= 0:
                    raise ValueError()
            except ValueError:
                return False, "Payment amount must be a positive number"
            
            # Get invoice details
            invoice = self.db_manager.execute_query(
                "SELECT total_amount, status FROM invoices WHERE id = ?", 
                (invoice_id,),
                fetchone=True
            )
            
            if not invoice:
                return False, "Invoice not found"
            
            total_amount = invoice[0]
            
            # Get total payments so far
            total_paid = self.db_manager.execute_query(
                "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE invoice_id = ?", 
                (invoice_id,),
                fetchone=True
            )[0]
            
            # Calculate new total paid
            new_total_paid = total_paid + amount
            
            # Determine new status
            if new_total_paid >= total_amount:
                new_status = "Paid"
            elif new_total_paid > 0:
                new_status = "Partial"
            else:
                new_status = "Unpaid"
            
            # Set payment date if not provided
            if not payment_date:
                payment_date = datetime.now().isoformat()
            
            # Record payment
            self.db_manager.execute_query('''
            INSERT INTO payments (invoice_id, payment_date, amount, payment_method, reference_number, notes, recorded_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                invoice_id, payment_date, amount, payment_method, reference_number, 
                notes, self.auth_manager.current_user["id"]
            ))
            
            # Update invoice status
            self.db_manager.execute_query(
                "UPDATE invoices SET status = ? WHERE id = ?",
                (new_status, invoice_id)
            )
            
            return True, "Payment recorded successfully"
        except Exception as e:
            return False, f"Failed to record payment: {str(e)}"
    
    def generate_invoice_pdf(self, invoice_id, output_path):
        try:
            # Get invoice details
            invoice, items, payments = self.get_invoice_details(invoice_id)
            
            if not invoice:
                return False, "Invoice not found"
            
            # Get company details
            company_name = self.db_manager.get_setting('company_name')
            company_address = self.db_manager.get_setting('company_address')
            company_phone = self.db_manager.get_setting('company_phone')
            company_email = self.db_manager.get_setting('company_email')
            company_website = self.db_manager.get_setting('company_website')
            company_tax_id = self.db_manager.get_setting('company_tax_id')
            currency_symbol = self.db_manager.get_setting('currency_symbol')
            
            # Create PDF
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            # Title
            elements.append(Paragraph(f"INVOICE #{invoice[1]}", styles['Title']))
            elements.append(Spacer(1, 0.25 * 72))  # 0.25 inch
            
            # Company and customer info
            data = [
                ["From:", "To:"],
                [company_name, invoice[12]],  # customer_name
                [company_address, invoice[13]],  # customer_address
                [f"Phone: {company_phone}", f"Phone: {invoice[14]}"],  # customer_phone
                [f"Email: {company_email}", f"Email: {invoice[13]}"],  # customer_email
                [f"Tax ID: {company_tax_id}", f"Tax ID: {invoice[15]}"]  # customer_tax_id
            ]
            
            t = Table(data, colWidths=[3 * 72, 3 * 72])  # 3 inches
            t.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 0.5 * 72))  # 0.5 inch
            
            # Invoice details
            invoice_date = datetime.fromisoformat(invoice[3]).strftime('%Y-%m-%d')
            due_date = datetime.fromisoformat(invoice[4]).strftime('%Y-%m-%d')
            
            data = [
                ["Invoice Number:", invoice[1]],
                ["Invoice Date:", invoice_date],
                ["Due Date:", due_date],
                ["Status:", invoice[11]]
            ]
            
            t = Table(data, colWidths=[2 * 72, 4 * 72])  # 2 and 4 inches
            t.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 0.5 * 72))  # 0.5 inch
            
            # Items table
            data = [["#", "Item", "Description", "Qty", "Unit Price", "Total"]]
            
            for i, item in enumerate(items, 1):
                data.append([
                    i,
                    item[7],  # item_name
                    item[2],  # description
                    item[3],  # quantity
                    f"{currency_symbol}{item[4]:.2f}",  # unit_price
                    f"{currency_symbol}{item[5]:.2f}"   # total_price
                ])
            
            # Add summary rows
            data.append(["", "", "", "", "Subtotal:", f"{currency_symbol}{invoice[5]:.2f}"])
            data.append(["", "", "", "", f"Tax ({invoice[6]}%):", f"{currency_symbol}{invoice[7]:.2f}"])
            data.append(["", "", "", "", f"Discount ({invoice[8]}%):", f"{currency_symbol}{invoice[9]:.2f}"])
            data.append(["", "", "", "", "Total:", f"{currency_symbol}{invoice[10]:.2f}"])
            
            # Calculate total paid
            total_paid = sum(payment[2] for payment in payments)
            data.append(["", "", "", "", "Paid:", f"{currency_symbol}{total_paid:.2f}"])
            data.append(["", "", "", "", "Balance:", f"{currency_symbol}{invoice[10] - total_paid:.2f}"])
            
            col_widths = [0.5 * 72, 2 * 72, 2 * 72, 0.5 * 72, 1 * 72, 1 * 72]  # in inches
            t = Table(data, colWidths=col_widths)
            
            # Style the table
            style = [
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, len(items)), 1, colors.black),
                ('LINEBELOW', (4, len(items) + 1), (-1, -2), 1, colors.black),
                ('LINEBELOW', (4, -1), (-1, -1), 2, colors.black),
                ('FONTNAME', (4, -1), (-1, -1), 'Helvetica-Bold'),
            ]
            t.setStyle(TableStyle(style))
            elements.append(t)
            
            # Payment information if any
            if payments:
                elements.append(Spacer(1, 0.5 * 72))  # 0.5 inch
                elements.append(Paragraph("Payment History", styles['Heading2']))
                
                data = [["Date", "Amount", "Method", "Reference", "Notes"]]
                
                for payment in payments:
                    payment_date = datetime.fromisoformat(payment[1]).strftime('%Y-%m-%d')
                    data.append([
                        payment_date,
                        f"{currency_symbol}{payment[2]:.2f}",
                        payment[3],
                        payment[4] or "",
                        payment[5] or ""
                    ])
                
                t = Table(data, colWidths=[1 * 72, 1 * 72, 1.5 * 72, 1.5 * 72, 2 * 72])  # in inches
                t.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(t)
            
            # Notes
            if invoice[12]:  # notes
                elements.append(Spacer(1, 0.5 * 72))  # 0.5 inch
                elements.append(Paragraph("Notes:", styles['Heading3']))
                elements.append(Paragraph(invoice[12], styles['Normal']))
            
            # Terms and conditions
            elements.append(Spacer(1, 0.5 * 72))  # 0.5 inch
            elements.append(Paragraph("Terms and Conditions:", styles['Heading3']))
            elements.append(Paragraph("1. Payment is due by the date specified above.", styles['Normal']))
            elements.append(Paragraph("2. Please include the invoice number with your payment.", styles['Normal']))
            elements.append(Paragraph("3. Thank you for your business!", styles['Normal']))
            
            # Build PDF
            doc.build(elements)
            
            return True, f"Invoice PDF generated successfully: {output_path}"
        except Exception as e:
            return False, f"Failed to generate PDF: {str(e)}"
    
    def send_invoice_email(self, invoice_id, recipient_email, subject, message, pdf_path, smtp_server, smtp_port, smtp_username, smtp_password):
        try:
            # Create email
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Add message body
            msg.attach(MIMEText(message, 'plain'))
            
            # Attach PDF
            with open(pdf_path, 'rb') as f:
                attachment = MIMEApplication(f.read(), _subtype='pdf')
                attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(pdf_path))
                msg.attach(attachment)
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True, "Invoice email sent successfully"
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"