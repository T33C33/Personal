import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import hashlib
import datetime
import qrcode
import cv2
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import io

class AttendanceSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Attendance Management System")
        self.root.geometry("1000x600")
        self.root.configure(bg="#f0f0f0")
        
        # Initialize variables
        self.current_user = None
        self.is_admin = False
        
        # Create database
        self.create_database()
        
        # Create login frame
        self.show_login_frame()
    
    def create_database(self):
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT TEXT,
            department TEXT TEXT,
            is_admin INTEGER DEFAULT 0
        )
        ''')
        
        # Create attendance table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            time_in TEXT,
            time_out TEXT,
            status TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create leave table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            start_date TEXT,
            end_date TEXT,
            reason TEXT,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create notifications table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Insert admin user if not exists
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            hashed_password = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users (username, password, full_name, email, department, is_admin) VALUES (?, ?, ?, ?, ?, ?)",
                          ('admin', hashed_password, 'Administrator', 'admin@example.com', 'IT', 1))
        
        conn.commit()
        conn.close()
    
    def show_login_frame(self):
        # Clear current window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create login frame
        login_frame = tk.Frame(self.root, bg="#f0f0f0")
        login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title
        title_label = tk.Label(login_frame, text="Attendance Management System", font=("Arial", 20, "bold"), bg="#f0f0f0")
        title_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Username
        username_label = tk.Label(login_frame, text="Username:", font=("Arial", 12), bg="#f0f0f0")
        username_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.username_entry = tk.Entry(login_frame, font=("Arial", 12), width=20)
        self.username_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # Password
        password_label = tk.Label(login_frame, text="Password:", font=("Arial", 12), bg="#f0f0f0")
        password_label.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.password_entry = tk.Entry(login_frame, font=("Arial", 12), width=20, show="*")
        self.password_entry.grid(row=2, column=1, padx=10, pady=10)
        
        # Login button
        login_button = tk.Button(login_frame, text="Login", font=("Arial", 12), bg="#4CAF50", fg="white",
                                command=self.login, width=15)
        login_button.grid(row=3, column=0, padx=10, pady=20)
        
        # Register button
        register_button = tk.Button(login_frame, text="Register", font=("Arial", 12), bg="#2196F3", fg="white",
                                   command=self.show_register_frame, width=15)
        register_button.grid(row=3, column=1, padx=10, pady=20)
        
        # QR Code login
        qr_button = tk.Button(login_frame, text="Scan QR Code", font=("Arial", 12), bg="#FF9800", fg="white",
                             command=self.scan_qr_login, width=15)
        qr_button.grid(row=4, column=0, columnspan=2, pady=10)
    
    def show_register_frame(self):
        # Clear current window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create register frame
        register_frame = tk.Frame(self.root, bg="#f0f0f0")
        register_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title
        title_label = tk.Label(register_frame, text="User Registration", font=("Arial", 20, "bold"), bg="#f0f0f0")
        title_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Username
        username_label = tk.Label(register_frame, text="Username:", font=("Arial", 12), bg="#f0f0f0")
        username_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.reg_username_entry = tk.Entry(register_frame, font=("Arial", 12), width=20)
        self.reg_username_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # Password
        password_label = tk.Label(register_frame, text="Password:", font=("Arial", 12), bg="#f0f0f0")
        password_label.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.reg_password_entry = tk.Entry(register_frame, font=("Arial", 12), width=20, show="*")
        self.reg_password_entry.grid(row=2, column=1, padx=10, pady=10)
        
        # Full Name
        fullname_label = tk.Label(register_frame, text="Full Name:", font=("Arial", 12), bg="#f0f0f0")
        fullname_label.grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        self.reg_fullname_entry = tk.Entry(register_frame, font=("Arial", 12), width=20)
        self.reg_fullname_entry.grid(row=3, column=1, padx=10, pady=10)
        
        # Email
        email_label = tk.Label(register_frame, text="Email:", font=("Arial", 12), bg="#f0f0f0")
        email_label.grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
        self.reg_email_entry = tk.Entry(register_frame, font=("Arial", 12), width=20)
        self.reg_email_entry.grid(row=4, column=1, padx=10, pady=10)
        
        # Department
        dept_label = tk.Label(register_frame, text="Department:", font=("Arial", 12), bg="#f0f0f0")
        dept_label.grid(row=5, column=0, padx=10, pady=10, sticky=tk.W)
        self.reg_dept_entry = tk.Entry(register_frame, font=("Arial", 12), width=20)
        self.reg_dept_entry.grid(row=5, column=1, padx=10, pady=10)
        
        # Register button
        register_button = tk.Button(register_frame, text="Register", font=("Arial", 12), bg="#4CAF50", fg="white",
                                   command=self.register_user, width=15)
        register_button.grid(row=6, column=0, padx=10, pady=20)
        
        # Back button
        back_button = tk.Button(register_frame, text="Back to Login", font=("Arial", 12), bg="#f44336", fg="white",
                               command=self.show_login_frame, width=15)
        back_button.grid(row=6, column=1, padx=10, pady=20)
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Check credentials
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, full_name, is_admin FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            self.current_user = {"id": user[0], "username": username, "full_name": user[1]}
            self.is_admin = bool(user[2])
            self.show_main_dashboard()
        else:
            messagebox.showerror("Error", "Invalid username or password")
    
    def register_user(self):
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()
        full_name = self.reg_fullname_entry.get()
        email = self.reg_email_entry.get()
        department = self.reg_dept_entry.get()
        
        if not username or not password or not full_name:
            messagebox.showerror("Error", "Please fill in all required fields")
            return
        
        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Insert new user
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, full_name, email, department) VALUES (?, ?, ?, ?, ?)",
                          (username, hashed_password, full_name, email, department))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "User registered successfully")
            self.show_login_frame()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def scan_qr_login(self):
        try:
            # Open camera
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                messagebox.showerror("Error", "Could not open camera")
                return
            
            messagebox.showinfo("QR Scan", "Point camera at QR code. Press 'q' to quit.")
            
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Detect QR code
                detector = cv2.QRCodeDetector()
                data, bbox, _ = detector.detectAndDecode(frame)
                
                if data:
                    cap.release()
                    cv2.destroyAllWindows()
                    
                    # Use the QR data (username) to login
                    conn = sqlite3.connect('attendance.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, full_name, is_admin FROM users WHERE username = ?", (data,))
                    user = cursor.fetchone()
                    conn.close()
                    
                    if user:
                        self.current_user = {"id": user[0], "username": data, "full_name": user[1]}
                        self.is_admin = bool(user[2])
                        self.show_main_dashboard()
                    else:
                        messagebox.showerror("Error", "Invalid QR code")
                    return
                
                cv2.imshow('QR Scanner', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            
        except Exception as e:
            messagebox.showerror("Error", f"QR scan failed: {str(e)}")
    
    def show_main_dashboard(self):
        # Clear current window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create main frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create sidebar
        sidebar = tk.Frame(main_frame, width=200, bg="#333333")
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        # User info
        user_frame = tk.Frame(sidebar, bg="#333333")
        user_frame.pack(pady=20)
        
        user_label = tk.Label(user_frame, text=f"Welcome,\n{self.current_user['full_name']}", 
                             font=("Arial", 12, "bold"), bg="#333333", fg="white", wraplength=180)
        user_label.pack()
        
        # Menu buttons
        menu_buttons = [
            ("Dashboard", self.show_dashboard),
            ("Mark Attendance", self.show_mark_attendance),
            ("Attendance Reports", self.show_attendance_reports),
            ("Leave Management", self.show_leave_management),
            ("My Profile", self.show_profile),
            ("Notifications", self.show_notifications)
        ]
        
        if self.is_admin:
            menu_buttons.extend([
                ("User Management", self.show_user_management),
                ("Analytics", self.show_analytics)
            ])
        
        for text, command in menu_buttons:
            btn = tk.Button(sidebar, text=text, font=("Arial", 12), bg="#333333", fg="white",
                           activebackground="#555555", activeforeground="white", bd=0,
                           command=command, width=20, anchor="w", padx=10)
            btn.pack(fill=tk.X, pady=5)
        
        # Logout button
        logout_btn = tk.Button(sidebar, text="Logout", font=("Arial", 12), bg="#f44336", fg="white",
                              command=self.logout, width=20)
        logout_btn.pack(side=tk.BOTTOM, pady=20)
        
        # Content frame
        self.content_frame = tk.Frame(main_frame, bg="#f0f0f0")
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Show dashboard by default
        self.show_dashboard()
    
    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_dashboard(self):
        self.clear_content_frame()
        
        # Dashboard title
        title_label = tk.Label(self.content_frame, text="Dashboard", font=("Arial", 18, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # Create dashboard widgets
        dashboard_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Stats cards
        stats_frame = tk.Frame(dashboard_frame, bg="#f0f0f0")
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Get attendance stats
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # Today's attendance
        today = datetime.date.today().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE user_id = ? AND date = ?", 
                      (self.current_user["id"], today))
        today_attendance = cursor.fetchone()[0] > 0
        
        # Total attendance
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE user_id = ?", (self.current_user["id"],))
        total_attendance = cursor.fetchone()[0]
        
        # Pending leaves
        cursor.execute("SELECT COUNT(*) FROM leaves WHERE user_id = ? AND status = 'Pending'", 
                      (self.current_user["id"],))
        pending_leaves = cursor.fetchone()[0]
        
        # Unread notifications
        cursor.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0", 
                      (self.current_user["id"],))
        unread_notifications = cursor.fetchone()[0]
        
        conn.close()
        
        # Create stat cards
        stat_cards = [
            {"title": "Today's Status", "value": "Present" if today_attendance else "Absent", 
             "color": "#4CAF50" if today_attendance else "#f44336"},
            {"title": "Total Attendance", "value": str(total_attendance), "color": "#2196F3"},
            {"title": "Pending Leaves", "value": str(pending_leaves), "color": "#FF9800"},
            {"title": "Notifications", "value": str(unread_notifications), "color": "#9C27B0"}
        ]
        
        for i, card in enumerate(stat_cards):
            card_frame = tk.Frame(stats_frame, bg=card["color"], padx=20, pady=15, bd=0)
            card_frame.grid(row=0, column=i, padx=10)
            
            title_label = tk.Label(card_frame, text=card["title"], font=("Arial", 12), bg=card["color"], fg="white")
            title_label.pack()
            
            value_label = tk.Label(card_frame, text=card["value"], font=("Arial", 24, "bold"), 
                                  bg=card["color"], fg="white")
            value_label.pack(pady=10)
        
        # Recent attendance
        recent_frame = tk.Frame(dashboard_frame, bg="white", padx=20, pady=15, bd=0)
        recent_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        recent_label = tk.Label(recent_frame, text="Recent Attendance", font=("Arial", 14, "bold"), bg="white")
        recent_label.pack(anchor=tk.W, pady=10)
        
        # Create treeview for recent attendance
        columns = ("Date", "Time In", "Time Out", "Status")
        tree = ttk.Treeview(recent_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor=tk.CENTER)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Get recent attendance records
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, time_in, time_out, status FROM attendance 
            WHERE user_id = ? ORDER BY date DESC, time_in DESC LIMIT 10
        """, (self.current_user["id"],))
        
        records = cursor.fetchall()
        conn.close()
        
        for record in records:
            tree.insert("", tk.END, values=record)
        
        # Quick actions
        actions_frame = tk.Frame(dashboard_frame, bg="#f0f0f0", pady=15)
        actions_frame.pack(fill=tk.X)
        
        actions_label = tk.Label(actions_frame, text="Quick Actions", font=("Arial", 14, "bold"), bg="#f0f0f0")
        actions_label.pack(anchor=tk.W, pady=10)
        
        buttons_frame = tk.Frame(actions_frame, bg="#f0f0f0")
        buttons_frame.pack(fill=tk.X)
        
        quick_buttons = [
            {"text": "Mark Attendance", "command": self.show_mark_attendance, "color": "#4CAF50"},
            {"text": "Apply Leave", "command": self.show_leave_management, "color": "#FF9800"},
            {"text": "View Reports", "command": self.show_attendance_reports, "color": "#2196F3"}
        ]
        
        for i, btn in enumerate(quick_buttons):
            action_btn = tk.Button(buttons_frame, text=btn["text"], font=("Arial", 12), bg=btn["color"], fg="white",
                                  command=btn["command"], padx=15, pady=8)
            action_btn.grid(row=0, column=i, padx=10)
    
    def show_mark_attendance(self):
        self.clear_content_frame()
        
        # Title
        title_label = tk.Label(self.content_frame, text="Mark Attendance", font=("Arial", 18, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # Create attendance frame
        attendance_frame = tk.Frame(self.content_frame, bg="white", padx=30, pady=30)
        attendance_frame.pack(padx=50, pady=20)
        
        # Current date and time
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        date_label = tk.Label(attendance_frame, text=f"Date: {date_str}", font=("Arial", 14), bg="white")
        date_label.pack(anchor=tk.W, pady=10)
        
        time_label = tk.Label(attendance_frame, text=f"Time: {time_str}", font=("Arial", 14), bg="white")
        time_label.pack(anchor=tk.W, pady=10)
        
        # Check if already marked attendance today
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT time_in, time_out FROM attendance 
            WHERE user_id = ? AND date = ?
        """, (self.current_user["id"], date_str))
        
        attendance_record = cursor.fetchone()
        conn.close()
        
        if attendance_record:
            time_in = attendance_record[0]
            time_out = attendance_record[1]
            
            status_label = tk.Label(attendance_frame, text="You have already marked attendance today", 
                                   font=("Arial", 14, "bold"), bg="white", fg="#4CAF50")
            status_label.pack(pady=20)
            
            details_frame = tk.Frame(attendance_frame, bg="white")
            details_frame.pack(pady=10)
            
            tk.Label(details_frame, text=f"Time In: {time_in}", font=("Arial", 12), bg="white").pack(anchor=tk.W)
            
            if time_out:
                tk.Label(details_frame, text=f"Time Out: {time_out}", font=("Arial", 12), bg="white").pack(anchor=tk.W)
                
                # Show complete message
                complete_label = tk.Label(attendance_frame, text="Attendance complete for today", 
                                         font=("Arial", 14), bg="white", fg="#4CAF50")
                complete_label.pack(pady=20)
            else:
                # Show time out button
                timeout_btn = tk.Button(attendance_frame, text="Mark Time Out", font=("Arial", 14), 
                                       bg="#f44336", fg="white", padx=20, pady=10,
                                       command=self.mark_timeout)
                timeout_btn.pack(pady=30)
        else:
            # Show mark attendance button
            mark_btn = tk.Button(attendance_frame, text="Mark Attendance", font=("Arial", 14), 
                               bg="#4CAF50", fg="white", padx=20, pady=10,
                               command=self.mark_attendance)
            mark_btn.pack(pady=30)
            
            # QR code option
            separator = ttk.Separator(attendance_frame, orient='horizontal')
            separator.pack(fill='x', pady=20)
            
            qr_label = tk.Label(attendance_frame, text="Or scan QR code", font=("Arial", 14), bg="white")
            qr_label.pack(pady=10)
            
            qr_btn = tk.Button(attendance_frame, text="Scan QR Code", font=("Arial", 14), 
                              bg="#2196F3", fg="white", padx=20, pady=10,
                              command=self.scan_qr_code)
            qr_btn.pack(pady=10)
    
    def mark_attendance(self):
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO attendance (user_id, date, time_in, status)
            VALUES (?, ?, ?, ?)
        """, (self.current_user["id"], date_str, time_str, "Present"))
        
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Success", "Attendance marked successfully")
        self.show_mark_attendance()  # Refresh the page
    
    def mark_timeout(self):
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE attendance SET time_out = ?
            WHERE user_id = ? AND date = ?
        """, (time_str, self.current_user["id"], date_str))
        
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Success", "Time out marked successfully")
        self.show_mark_attendance()  # Refresh the page
    
    def scan_qr_code(self):
        # This would typically use a camera to scan QR codes
        # For this demo, we'll simulate it with a file dialog
        messagebox.showinfo("QR Code Scanner", "In a real implementation, this would open your camera to scan a QR code. For this demo, please select a QR code image file.")
        
        file_path = filedialog.askopenfilename(title="Select QR Code Image", 
                                              filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        
        if file_path:
            try:
                # In a real implementation, this would use OpenCV to decode the QR code
                # For this demo, we'll just mark attendance
                self.mark_attendance()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to scan QR code: {str(e)}")
    
    def show_attendance_reports(self):
        self.clear_content_frame()
        
        # Title
        title_label = tk.Label(self.content_frame, text="Attendance Reports", font=("Arial", 18, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # Create reports frame
        reports_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        reports_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Filter options
        filter_frame = tk.Frame(reports_frame, bg="white", padx=20, pady=15)
        filter_frame.pack(fill=tk.X, pady=10)
        
        filter_label = tk.Label(filter_frame, text="Filter Reports", font=("Arial", 14, "bold"), bg="white")
        filter_label.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=10)
        
        # Date range
        from_label = tk.Label(filter_frame, text="From Date:", font=("Arial", 12), bg="white")
        from_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        
        self.from_date = tk.StringVar(value=datetime.date.today().replace(day=1).strftime("%Y-%m-%d"))
        from_entry = tk.Entry(filter_frame, textvariable=self.from_date, font=("Arial", 12), width=12)
        from_entry.grid(row=1, column=1, padx=10, pady=10)
        
        to_label = tk.Label(filter_frame, text="To Date:", font=("Arial", 12), bg="white")
        to_label.grid(row=1, column=2, padx=10, pady=10, sticky=tk.W)
        
        self.to_date = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        to_entry = tk.Entry(filter_frame, textvariable=self.to_date, font=("Arial", 12), width=12)
        to_entry.grid(row=1, column=3, padx=10, pady=10)
        
        # Generate report button
        generate_btn = tk.Button(filter_frame, text="Generate Report", font=("Arial", 12), 
                                bg="#4CAF50", fg="white", padx=15, pady=5,
                                command=self.generate_attendance_report)
        generate_btn.grid(row=1, column=4, padx=20, pady=10)
        
        # Export button
        export_btn = tk.Button(filter_frame, text="Export to Excel", font=("Arial", 12), 
                              bg="#2196F3", fg="white", padx=15, pady=5,
                              command=self.export_attendance_report)
        export_btn.grid(row=1, column=5, padx=20, pady=10)
        
        # Report data
        report_frame = tk.Frame(reports_frame, bg="white")
        report_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create treeview for attendance report
        columns = ("Date", "Day", "Time In", "Time Out", "Duration", "Status")
        self.report_tree = ttk.Treeview(report_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=100, anchor=tk.CENTER)
        
        self.report_tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Generate report by default
        self.generate_attendance_report()
        
        # Summary frame
        summary_frame = tk.Frame(reports_frame, bg="white", padx=20, pady=15)
        summary_frame.pack(fill=tk.X, pady=10)
        
        summary_label = tk.Label(summary_frame, text="Summary", font=("Arial", 14, "bold"), bg="white")
        summary_label.pack(anchor=tk.W, pady=10)
        
        self.summary_text = tk.Text(summary_frame, height=5, width=80, font=("Arial", 12), bg="#f9f9f9")
        self.summary_text.pack(fill=tk.X, pady=10)
        self.summary_text.config(state=tk.DISABLED)
    
    def generate_attendance_report(self):
        from_date = self.from_date.get()
        to_date = self.to_date.get()
        
        # Clear existing data
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        
        # Get attendance data
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, time_in, time_out, status FROM attendance 
            WHERE user_id = ? AND date BETWEEN ? AND ?
            ORDER BY date DESC
        """, (self.current_user["id"], from_date, to_date))
        
        records = cursor.fetchall()
        conn.close()
        
        total_days = 0
        present_days = 0
        total_hours = 0
        
        for record in records:
            date_str, time_in, time_out, status = record
            
            # Calculate day of week
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            day_of_week = date_obj.strftime("%A")
            
            # Calculate duration
            duration = "N/A"
            if time_in and time_out:
                time_in_obj = datetime.datetime.strptime(time_in, "%H:%M:%S")
                time_out_obj = datetime.datetime.strptime(time_out, "%H:%M:%S")
                
                duration_seconds = (time_out_obj - time_in_obj).total_seconds()
                hours = int(duration_seconds // 3600)
                minutes = int((duration_seconds % 3600) // 60)
                
                duration = f"{hours}h {minutes}m"
                total_hours += duration_seconds / 3600
            
            self.report_tree.insert("", tk.END, values=(date_str, day_of_week, time_in, time_out, duration, status))
            
            total_days += 1
            if status == "Present":
                present_days += 1
        
        # Update summary
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        
        summary = f"Total Working Days: {total_days}\n"
        summary += f"Present Days: {present_days}\n"
        summary += f"Absent Days: {total_days - present_days}\n"
        summary += f"Attendance Percentage: {(present_days / max(total_days, 1)) * 100:.2f}%\n"
        summary += f"Total Working Hours: {total_hours:.2f} hours"
        
        self.summary_text.insert(tk.END, summary)
        self.summary_text.config(state=tk.DISABLED)
    
    def export_attendance_report(self):
        from_date = self.from_date.get()
        to_date = self.to_date.get()
        
        # Get attendance data
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, time_in, time_out, status FROM attendance 
            WHERE user_id = ? AND date BETWEEN ? AND ?
            ORDER BY date DESC
        """, (self.current_user["id"], from_date, to_date))
        
        records = cursor.fetchall()
        conn.close()
        
        # Create DataFrame
        data = []
        for record in records:
            date_str, time_in, time_out, status = record
            
            # Calculate day of week
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            day_of_week = date_obj.strftime("%A")
            
            # Calculate duration
            duration = "N/A"
            if time_in and time_out:
                time_in_obj = datetime.datetime.strptime(time_in, "%H:%M:%S")
                time_out_obj = datetime.datetime.strptime(time_out, "%H:%M:%S")
                
                duration_seconds = (time_out_obj - time_in_obj).total_seconds()
                hours = int(duration_seconds // 3600)
                minutes = int((duration_seconds % 3600) // 60)
                
                duration = f"{hours}h {minutes}m"
            
            data.append({
                "Date": date_str,
                "Day": day_of_week,
                "Time In": time_in,
                "Time Out": time_out,
                "Duration": duration,
                "Status": status
            })
        
        df = pd.DataFrame(data)
        
        # Ask for save location
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", 
                                                filetypes=[("Excel files", "*.xlsx")],
                                                title="Save Attendance Report")
        
        if file_path:
            try:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Success", f"Report exported successfully to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export report: {str(e)}")
    
    def show_leave_management(self):
        self.clear_content_frame()
        
        # Title
        title_label = tk.Label(self.content_frame, text="Leave Management", font=("Arial", 18, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # Create leave management frame
        leave_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        leave_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Apply for leave section
        apply_frame = tk.Frame(leave_frame, bg="white", padx=20, pady=15)
        apply_frame.pack(fill=tk.X, pady=10)
        
        apply_label = tk.Label(apply_frame, text="Apply for Leave", font=("Arial", 14, "bold"), bg="white")
        apply_label.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=10)
        
        # Start date
        start_label = tk.Label(apply_frame, text="Start Date:", font=("Arial", 12), bg="white")
        start_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        
        self.start_date = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        start_entry = tk.Entry(apply_frame, textvariable=self.start_date, font=("Arial", 12), width=12)
        start_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # End date
        end_label = tk.Label(apply_frame, text="End Date:", font=("Arial", 12), bg="white")
        end_label.grid(row=1, column=2, padx=10, pady=10, sticky=tk.W)
        
        self.end_date = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        end_entry = tk.Entry(apply_frame, textvariable=self.end_date, font=("Arial", 12), width=12)
        end_entry.grid(row=1, column=3, padx=10, pady=10)
        
        # Reason
        reason_label = tk.Label(apply_frame, text="Reason:", font=("Arial", 12), bg="white")
        reason_label.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        
        self.reason_text = tk.Text(apply_frame, height=3, width=40, font=("Arial", 12))
        self.reason_text.grid(row=2, column=1, columnspan=3, padx=10, pady=10, sticky=tk.W)
        
        # Apply button
        apply_btn = tk.Button(apply_frame, text="Apply for Leave", font=("Arial", 12), 
                             bg="#4CAF50", fg="white", padx=15, pady=5,
                             command=self.apply_for_leave)
        apply_btn.grid(row=3, column=1, columnspan=2, pady=20)
        
        # Leave history section
        history_frame = tk.Frame(leave_frame, bg="white")
        history_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        history_label = tk.Label(history_frame, text="Leave History", font=("Arial", 14, "bold"), bg="white")
        history_label.pack(anchor=tk.W, padx=20, pady=10)
        
        # Create treeview for leave history
        columns = ("Start Date", "End Date", "Reason", "Status")
        self.leave_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.leave_tree.heading(col, text=col)
            self.leave_tree.column(col, width=150, anchor=tk.CENTER)
        
        self.leave_tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Get leave history
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT start_date, end_date, reason, status FROM leaves 
            WHERE user_id = ? ORDER BY start_date DESC
        """, (self.current_user["id"],))
        
        records = cursor.fetchall()
        conn.close()
        
        for record in records:
            self.leave_tree.insert("", tk.END, values=record)
    
    def apply_for_leave(self):
        start_date = self.start_date.get()
        end_date = self.end_date.get()
        reason = self.reason_text.get(1.0, tk.END).strip()
        
        if not start_date or not end_date or not reason:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        try:
            # Validate dates
            start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            
            if end_date_obj < start_date_obj:
                messagebox.showerror("Error", "End date cannot be before start date")
                return
            
            # Insert leave request
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO leaves (user_id, start_date, end_date, reason, status)
                VALUES (?, ?, ?, ?, ?)
            """, (self.current_user["id"], start_date, end_date, reason, "Pending"))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "Leave application submitted successfully")
            
            # Refresh the page
            self.show_leave_management()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def show_profile(self):
        self.clear_content_frame()
        
        # Title
        title_label = tk.Label(self.content_frame, text="My Profile", font=("Arial", 18, "bold"), bg="#f0f0f0")
        title_label.pack(pady=5)
        
        # Get user details
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, full_name, email, department FROM users 
            WHERE id = ?
        """, (self.current_user["id"],))
        
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data:
            messagebox.showerror("Error", "User data not found")
            return
        
        username, full_name, email, department = user_data
        
        # Create profile frame
        profile_frame = tk.Frame(self.content_frame, bg="white", padx=30, pady=30)
        profile_frame.pack(padx=50, pady=20)
        
        # Profile picture (placeholder)
        profile_pic_frame = tk.Frame(profile_frame, bg="white")
        profile_pic_frame.pack(pady=20)
        
        profile_pic = tk.Label(profile_pic_frame, text="👤", font=("Arial", 60), bg="white")
        profile_pic.pack()
        
        # User details
        details_frame = tk.Frame(profile_frame, bg="white")
        details_frame.pack(pady=20)
        
        # Full name
        name_label = tk.Label(details_frame, text="Full Name:", font=("Arial", 12, "bold"), bg="white")
        name_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        
        self.name_var = tk.StringVar(value=full_name)
        name_entry = tk.Entry(details_frame, textvariable=self.name_var, font=("Arial", 12), width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        
        # Username
        username_label = tk.Label(details_frame, text="Username:", font=("Arial", 12, "bold"), bg="white")
        username_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        
        username_value = tk.Label(details_frame, text=username, font=("Arial", 12), bg="white")
        username_value.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
        
        # Email
        email_label = tk.Label(details_frame, text="Email:", font=("Arial", 12, "bold"), bg="white")
        email_label.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        
        self.email_var = tk.StringVar(value=email)
        email_entry = tk.Entry(details_frame, textvariable=self.email_var, font=("Arial", 12), width=30)
        email_entry.grid(row=2, column=1, padx=10, pady=10)
        
        # Department
        dept_label = tk.Label(details_frame, text="Department:", font=("Arial", 12, "bold"), bg="white")
        dept_label.grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        
        self.dept_var = tk.StringVar(value=department)
        dept_entry = tk.Entry(details_frame, textvariable=self.dept_var, font=("Arial", 12), width=30)
        dept_entry.grid(row=3, column=1, padx=10, pady=10)
        
        # Change password section
        password_frame = tk.Frame(profile_frame, bg="white")
        password_frame.pack(pady=20)
        
        password_label = tk.Label(password_frame, text="Change Password", font=("Arial", 14, "bold"), bg="white")
        password_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # Current password
        current_label = tk.Label(password_frame, text="Current Password:", font=("Arial", 12), bg="white")
        current_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        
        self.current_password = tk.Entry(password_frame, font=("Arial", 12), width=20, show="*")
        self.current_password.grid(row=1, column=1, padx=10, pady=10)
        
        # New password
        new_label = tk.Label(password_frame, text="New Password:", font=("Arial", 12), bg="white")
        new_label.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        
        self.new_password = tk.Entry(password_frame, font=("Arial", 12), width=20, show="*")
        self.new_password.grid(row=2, column=1, padx=10, pady=10)
        
        # Confirm password
        confirm_label = tk.Label(password_frame, text="Confirm Password:", font=("Arial", 12), bg="white")
        confirm_label.grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        
        self.confirm_password = tk.Entry(password_frame, font=("Arial", 12), width=20, show="*")
        self.confirm_password.grid(row=3, column=1, padx=10, pady=10)
        
        # Buttons
        buttons_frame = tk.Frame(profile_frame, bg="white")
        buttons_frame.pack(pady=20)
        
        update_profile_btn = tk.Button(buttons_frame, text="Update Profile", font=("Arial", 12), 
                                      bg="#4CAF50", fg="white", padx=15, pady=8,
                                      command=self.update_profile)
        update_profile_btn.grid(row=0, column=0, padx=10)
        
        change_password_btn = tk.Button(buttons_frame, text="Change Password", font=("Arial", 12), 
                                       bg="#2196F3", fg="white", padx=15, pady=8,
                                       command=self.change_password)
        change_password_btn.grid(row=0, column=1, padx=10)
        
        # Generate QR Code
        qr_frame = tk.Frame(profile_frame, bg="white")
        qr_frame.pack(pady=20)
        
        qr_label = tk.Label(qr_frame, text="Your QR Code", font=("Arial", 14, "bold"), bg="white")
        qr_label.pack(pady=10)
        
        generate_qr_btn = tk.Button(qr_frame, text="Generate QR Code", font=("Arial", 12), 
                                   bg="#FF9800", fg="white", padx=15, pady=8,
                                   command=self.generate_user_qr)
        generate_qr_btn.pack(pady=10)
        
        self.qr_image_label = tk.Label(qr_frame, bg="white")
        self.qr_image_label.pack(pady=10)
    
    def update_profile(self):
        full_name = self.name_var.get()
        email = self.email_var.get()
        department = self.dept_var.get()
        
        if not full_name:
            messagebox.showerror("Error", "Full name cannot be empty")
            return
        
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET full_name = ?, email = ?, department = ?
                WHERE id = ?
            """, (full_name, email, department, self.current_user["id"]))
            
            conn.commit()
            conn.close()
            
            # Update current user info
            self.current_user["full_name"] = full_name
            
            messagebox.showinfo("Success", "Profile updated successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def change_password(self):
        current_password = self.current_password.get()
        new_password = self.new_password.get()
        confirm_password = self.confirm_password.get()
        
        if not current_password or not new_password or not confirm_password:
            messagebox.showerror("Error", "Please fill in all password fields")
            return
        
        if new_password != confirm_password:
            messagebox.showerror("Error", "New password and confirm password do not match")
            return
        
        # Hash the passwords
        hashed_current = hashlib.sha256(current_password.encode()).hexdigest()
        hashed_new = hashlib.sha256(new_password.encode()).hexdigest()
        
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            # Verify current password
            cursor.execute("SELECT id FROM users WHERE id = ? AND password = ?", 
                          (self.current_user["id"], hashed_current))
            
            if not cursor.fetchone():
                messagebox.showerror("Error", "Current password is incorrect")
                conn.close()
                return
            
            # Update password
            cursor.execute("UPDATE users SET password = ? WHERE id = ?", 
                          (hashed_new, self.current_user["id"]))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "Password changed successfully")
            
            # Clear password fields
            self.current_password.delete(0, tk.END)
            self.new_password.delete(0, tk.END)
            self.confirm_password.delete(0, tk.END)
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def generate_user_qr(self):
        # Generate QR code for the user
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.current_user["username"])
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to PhotoImage
        img = img.resize((200, 200))
        photo = ImageTk.PhotoImage(img)
        
        # Display QR code
        self.qr_image_label.config(image=photo)
        self.qr_image_label.image = photo  # Keep a reference
        
        # Option to save
        save_btn = tk.Button(self.qr_image_label.master, text="Save QR Code", font=("Arial", 12), 
                            bg="#2196F3", fg="white", padx=15, pady=5,
                            command=lambda: self.save_qr_code(img))
        save_btn.pack(pady=10)
    
    def save_qr_code(self, img):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", 
                                                filetypes=[("PNG files", "*.png")],
                                                title="Save QR Code")
        
        if file_path:
            img.save(file_path)
            messagebox.showinfo("Success", f"QR code saved to {file_path}")
    
    def show_notifications(self):
        self.clear_content_frame()
        
        # Title
        title_label = tk.Label(self.content_frame, text="Notifications", font=("Arial", 18, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # Create notifications frame
        notifications_frame = tk.Frame(self.content_frame, bg="white")
        notifications_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)
        
        # Get notifications
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, message, created_at, is_read FROM notifications 
            WHERE user_id = ? ORDER BY created_at DESC
        """, (self.current_user["id"],))
        
        notifications = cursor.fetchall()
        
        # Mark all as read
        cursor.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", 
                      (self.current_user["id"],))
        
        conn.commit()
        conn.close()
        
        if not notifications:
            no_notif_label = tk.Label(notifications_frame, text="No notifications", 
                                     font=("Arial", 14), bg="white")
            no_notif_label.pack(pady=50)
        else:
            # Create scrollable frame
            canvas = tk.Canvas(notifications_frame, bg="white")
            scrollbar = ttk.Scrollbar(notifications_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="white")
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Display notifications
            for i, (notif_id, message, date, is_read) in enumerate(notifications):
                notif_frame = tk.Frame(scrollable_frame, bg="#f9f9f9" if is_read else "#e3f2fd", 
                                      padx=20, pady=15, bd=1, relief=tk.SOLID)
                notif_frame.pack(fill=tk.X, pady=5)
                
                date_label = tk.Label(notif_frame, text=date, font=("Arial", 10), 
                                     bg="#f9f9f9" if is_read else "#e3f2fd", fg="#666666")
                date_label.pack(anchor=tk.W)
                
                message_label = tk.Label(notif_frame, text=message, font=("Arial", 12), 
                                        bg="#f9f9f9" if is_read else "#e3f2fd", wraplength=600, 
                                        justify=tk.LEFT)
                message_label.pack(anchor=tk.W, pady=5)
    
    def show_user_management(self):
        if not self.is_admin:
            messagebox.showerror("Access Denied", "You do not have permission to access this feature")
            return
        
        self.clear_content_frame()
        
        # Title
        title_label = tk.Label(self.content_frame, text="User Management", font=("Arial", 18, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # Create user management frame
        user_mgmt_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        user_mgmt_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Search and filter
        filter_frame = tk.Frame(user_mgmt_frame, bg="white", padx=20, pady=15)
        filter_frame.pack(fill=tk.X, pady=10)
        
        search_label = tk.Label(filter_frame, text="Search Users:", font=("Arial", 12), bg="white")
        search_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(filter_frame, textvariable=self.search_var, font=("Arial", 12), width=30)
        search_entry.grid(row=0, column=1, padx=10, pady=10)
        
        search_btn = tk.Button(filter_frame, text="Search", font=("Arial", 12), 
                              bg="#2196F3", fg="white", padx=15, pady=5,
                              command=self.search_users)
        search_btn.grid(row=0, column=2, padx=20, pady=10)
        
        # Add user button
        add_user_btn = tk.Button(filter_frame, text="Add New User", font=("Arial", 12), 
                                bg="#4CAF50", fg="white", padx=15, pady=5,
                                command=self.show_add_user)
        add_user_btn.grid(row=0, column=3, padx=20, pady=10)
        
        # User list
        users_frame = tk.Frame(user_mgmt_frame, bg="white")
        users_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create treeview for users
        columns = ("ID", "Username", "Full Name", "Email", "Department", "Admin")
        self.users_tree = ttk.Treeview(users_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=100, anchor=tk.CENTER)
        
        self.users_tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Add right-click menu
        self.user_menu = tk.Menu(self.users_tree, tearoff=0)
        self.user_menu.add_command(label="Edit User", command=self.edit_selected_user)
        self.user_menu.add_command(label="Delete User", command=self.delete_selected_user)
        self.user_menu.add_separator()
        self.user_menu.add_command(label="Reset Password", command=self.reset_user_password)
        
        self.users_tree.bind("<Button-3>", self.show_user_menu)
        
        # Load users
        self.load_users()
    
    def load_users(self):
        # Clear existing data
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        # Get users
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, full_name, email, department, is_admin FROM users
            ORDER BY id
        """)
        
        users = cursor.fetchall()
        conn.close()
        
        for user in users:
            user_id, username, full_name, email, department, is_admin = user
            admin_status = "Yes" if is_admin else "No"
            
            self.users_tree.insert("", tk.END, values=(user_id, username, full_name, email, department, admin_status))
    
    def search_users(self):
        search_term = self.search_var.get().strip().lower()
        
        if not search_term:
            self.load_users()
            return
        
        # Clear existing data
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        # Search users
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, full_name, email, department, is_admin FROM users
            WHERE lower(username) LIKE ? OR lower(full_name) LIKE ? OR lower(email) LIKE ? 
            OR lower(department) LIKE ?
            ORDER BY id
        """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        
        users = cursor.fetchall()
        conn.close()
        
        for user in users:
            user_id, username, full_name, email, department, is_admin = user
            admin_status = "Yes" if is_admin else "No"
            
            self.users_tree.insert("", tk.END, values=(user_id, username, full_name, email, department, admin_status))
    
    def show_user_menu(self, event):
        # Select row under mouse
        iid = self.users_tree.identify_row(event.y)
        if iid:
            self.users_tree.selection_set(iid)
            self.user_menu.post(event.x_root, event.y_root)
    
    def edit_selected_user(self):
        selected_item = self.users_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a user to edit")
            return
        
        user_id = self.users_tree.item(selected_item[0], "values")[0]
        
        # Get user details
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, full_name, email, department, is_admin FROM users 
            WHERE id = ?
        """, (user_id,))
        
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data:
            messagebox.showerror("Error", "User data not found")
            return
        
        username, full_name, email, department, is_admin = user_data
        
        # Create edit user dialog
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit User")
        edit_window.geometry("400x400")
        edit_window.resizable(False, False)
        
        # User details form
        form_frame = tk.Frame(edit_window, padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Username (readonly)
        username_label = tk.Label(form_frame, text="Username:", font=("Arial", 12))
        username_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        
        username_value = tk.Label(form_frame, text=username, font=("Arial", 12))
        username_value.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
        
        # Full Name
        name_label = tk.Label(form_frame, text="Full Name:", font=("Arial", 12))
        name_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        
        name_var = tk.StringVar(value=full_name)
        name_entry = tk.Entry(form_frame, textvariable=name_var, font=("Arial", 12), width=20)
        name_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # Email
        email_label = tk.Label(form_frame, text="Email:", font=("Arial", 12))
        email_label.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        
        email_var = tk.StringVar(value=email)
        email_entry = tk.Entry(form_frame, textvariable=email_var, font=("Arial", 12), width=20)
        email_entry.grid(row=2, column=1, padx=10, pady=10)
        
        # Department
        dept_label = tk.Label(form_frame, text="Department:", font=("Arial", 12))
        dept_label.grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        
        dept_var = tk.StringVar(value=department)
        dept_entry = tk.Entry(form_frame, textvariable=dept_var, font=("Arial", 12), width=20)
        dept_entry.grid(row=3, column=1, padx=10, pady=10)
        
        # Admin status
        admin_label = tk.Label(form_frame, text="Admin Status:", font=("Arial", 12))
        admin_label.grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
        
        admin_var = tk.BooleanVar(value=bool(is_admin))
        admin_check = tk.Checkbutton(form_frame, variable=admin_var, font=("Arial", 12))
        admin_check.grid(row=4, column=1, padx=10, pady=10, sticky=tk.W)
        
        # Save button
        def save_user():
            try:
                conn = sqlite3.connect('attendance.db')
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET full_name = ?, email = ?, department = ?, is_admin = ?
                    WHERE id = ?
                """, (name_var.get(), email_var.get(), dept_var.get(), 
                      1 if admin_var.get() else 0, user_id))
                
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Success", "User updated successfully")
                edit_window.destroy()
                self.load_users()
                
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
        save_btn = tk.Button(form_frame, text="Save Changes", font=("Arial", 12), 
                            bg="#4CAF50", fg="white", padx=15, pady=5,
                            command=save_user)
        save_btn.grid(row=5, column=0, columnspan=2, pady=20)
    
    def delete_selected_user(self):
        selected_item = self.users_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a user to delete")
            return
        
        user_id = self.users_tree.item(selected_item[0], "values")[0]
        username = self.users_tree.item(selected_item[0], "values")[1]
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete user '{username}'?")
        if not confirm:
            return
        
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            # Delete user's attendance records
            cursor.execute("DELETE FROM attendance WHERE user_id = ?", (user_id,))
            
            # Delete user's leave records
            cursor.execute("DELETE FROM leaves WHERE user_id = ?", (user_id,))
            
            # Delete user's notifications
            cursor.execute("DELETE FROM notifications WHERE user_id = ?", (user_id,))
            
            # Delete user
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"User '{username}' deleted successfully")
            self.load_users()
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def reset_user_password(self):
        selected_item = self.users_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a user to reset password")
            return
        
        user_id = self.users_tree.item(selected_item[0], "values")[0]
        username = self.users_tree.item(selected_item[0], "values")[1]
        
        # Confirm reset
        confirm = messagebox.askyesno("Confirm Reset", f"Are you sure you want to reset password for user '{username}'?")
        if not confirm:
            return
        
        # Default password
        default_password = "password123"
        hashed_password = hashlib.sha256(default_password.encode()).hexdigest()
        
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Password for user '{username}' has been reset to '{default_password}'")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def show_add_user(self):
        # Create add user dialog
        add_window = tk.Toplevel(self.root)
        add_window.title("Add New User")
        add_window.geometry("400x450")
        add_window.resizable(False, False)
        
        # User details form
        form_frame = tk.Frame(add_window, padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Username
        username_label = tk.Label(form_frame, text="Username:", font=("Arial", 12))
        username_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        
        username_var = tk.StringVar()
        username_entry = tk.Entry(form_frame, textvariable=username_var, font=("Arial", 12), width=20)
        username_entry.grid(row=0, column=1, padx=10, pady=10)
        
        # Password
        password_label = tk.Label(form_frame, text="Password:", font=("Arial", 12))
        password_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        
        password_var = tk.StringVar()
        password_entry = tk.Entry(form_frame, textvariable=password_var, font=("Arial", 12), width=20, show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # Full Name
        name_label = tk.Label(form_frame, text="Full Name:", font=("Arial", 12))
        name_label.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        
        name_var = tk.StringVar()
        name_entry = tk.Entry(form_frame, textvariable=name_var, font=("Arial", 12), width=20)
        name_entry.grid(row=2, column=1, padx=10, pady=10)
        
        # Email
        email_label = tk.Label(form_frame, text="Email:", font=("Arial", 12))
        email_label.grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        
        email_var = tk.StringVar()
        email_entry = tk.Entry(form_frame, textvariable=email_var, font=("Arial", 12), width=20)
        email_entry.grid(row=3, column=1, padx=10, pady=10)
        
        # Department
        dept_label = tk.Label(form_frame, text="Department:", font=("Arial", 12))
        dept_label.grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
        
        dept_var = tk.StringVar()
        dept_entry = tk.Entry(form_frame, textvariable=dept_var, font=("Arial", 12), width=20)
        dept_entry.grid(row=4, column=1, padx=10, pady=10)
        
        # Admin status
        admin_label = tk.Label(form_frame, text="Admin Status:", font=("Arial", 12))
        admin_label.grid(row=5, column=0, padx=10, pady=10, sticky=tk.W)
        
        admin_var = tk.BooleanVar(value=False)
        admin_check = tk.Checkbutton(form_frame, variable=admin_var, font=("Arial", 12))
        admin_check.grid(row=5, column=1, padx=10, pady=10, sticky=tk.W)
        
        # Add button
        def add_user():
            username = username_var.get()
            password = password_var.get()
            full_name = name_var.get()
            email = email_var.get()
            department = dept_var.get()
            is_admin = admin_var.get()
            
            if not username or not password or not full_name:
                messagebox.showerror("Error", "Please fill in all required fields", parent=add_window)
                return
            
            # Hash the password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            try:
                conn = sqlite3.connect('attendance.db')
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, password, full_name, email, department, is_admin)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, hashed_password, full_name, email, department, 1 if is_admin else 0))
                
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Success", "User added successfully", parent=add_window)
                add_window.destroy()
                self.load_users()
                
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists", parent=add_window)
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}", parent=add_window)
        
        add_btn = tk.Button(form_frame, text="Add User", font=("Arial", 12), 
                           bg="#4CAF50", fg="white", padx=15, pady=5,
                           command=add_user)
        add_btn.grid(row=6, column=0, columnspan=2, pady=20)
    
    def show_analytics(self):
        if not self.is_admin:
            messagebox.showerror("Access Denied", "You do not have permission to access this feature")
            return
        
        self.clear_content_frame()
        
        # Title
        title_label = tk.Label(self.content_frame, text="Attendance Analytics", font=("Arial", 18, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # Create analytics frame
        analytics_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        analytics_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Filter options
        filter_frame = tk.Frame(analytics_frame, bg="white", padx=20, pady=15)
        filter_frame.pack(fill=tk.X, pady=10)
        
        # Department filter
        dept_label = tk.Label(filter_frame, text="Department:", font=("Arial", 12), bg="white")
        dept_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        
        # Get departments
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT department FROM users WHERE department IS NOT NULL")
        departments = [dept[0] for dept in cursor.fetchall()]
        conn.close()
        
        self.dept_var = tk.StringVar(value="All Departments")
        dept_options = ["All Departments"] + departments
        dept_dropdown = ttk.Combobox(filter_frame, textvariable=self.dept_var, values=dept_options, 
                                    font=("Arial", 12), width=20)
        dept_dropdown.grid(row=0, column=1, padx=10, pady=10)
        
        # Date range
        from_label = tk.Label(filter_frame, text="From Date:", font=("Arial", 12), bg="white")
        from_label.grid(row=0, column=2, padx=10, pady=10, sticky=tk.W)
        
        self.analytics_from_date = tk.StringVar(value=(datetime.date.today() - datetime.timedelta(days=30)).strftime("%Y-%m-%d"))
        from_entry = tk.Entry(filter_frame, textvariable=self.analytics_from_date, font=("Arial", 12), width=12)
        from_entry.grid(row=0, column=3, padx=10, pady=10)
        
        to_label = tk.Label(filter_frame, text="To Date:", font=("Arial", 12), bg="white")
        to_label.grid(row=0, column=4, padx=10, pady=10, sticky=tk.W)
        
        self.analytics_to_date = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        to_entry = tk.Entry(filter_frame, textvariable=self.analytics_to_date, font=("Arial", 12), width=12)
        to_entry.grid(row=0, column=5, padx=10, pady=10)
        
        # Generate button
        generate_btn = tk.Button(filter_frame, text="Generate Analytics", font=("Arial", 12), 
                                bg="#4CAF50", fg="white", padx=15, pady=5,
                                command=self.generate_analytics)
        generate_btn.grid(row=0, column=6, padx=20, pady=10)
        
        # Charts frame
        self.charts_frame = tk.Frame(analytics_frame, bg="white")
        self.charts_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Generate analytics by default
        self.generate_analytics()
    
    def generate_analytics(self):
        department = self.dept_var.get()
        from_date = self.analytics_from_date.get()
        to_date = self.analytics_to_date.get()
        
        # Clear charts frame
        for widget in self.charts_frame.winfo_children():
            widget.destroy()
        
        # Get attendance data
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        if department == "All Departments":
            cursor.execute("""
                SELECT u.department, a.date, COUNT(a.id) 
                FROM attendance a
                JOIN users u ON a.user_id = u.id
                WHERE a.date BETWEEN ? AND ?
                GROUP BY u.department, a.date
            """, (from_date, to_date))
        else:
            cursor.execute("""
                SELECT u.department, a.date, COUNT(a.id) 
                FROM attendance a
                JOIN users u ON a.user_id = u.id
                WHERE u.department = ? AND a.date BETWEEN ? AND ?
                GROUP BY u.department, a.date
            """, (department, from_date, to_date))
        
        attendance_data = cursor.fetchall()
        
        # Get user count by department
        if department == "All Departments":
            cursor.execute("""
                SELECT department, COUNT(id) FROM users
                WHERE department IS NOT NULL
                GROUP BY department
            """)
        else:
            cursor.execute("""
                SELECT department, COUNT(id) FROM users
                WHERE department = ?
                GROUP BY department
            """, (department,))
        
        user_counts = dict(cursor.fetchall())
        
        conn.close()
        
        # Process data for charts
        attendance_by_dept = {}
        attendance_by_date = {}
        
        for dept, date, count in attendance_data:
            if dept is None:
                continue
                
            # By department
            if dept not in attendance_by_dept:
                attendance_by_dept[dept] = 0
            attendance_by_dept[dept] += count
            
            # By date
            if date not in attendance_by_date:
                attendance_by_date[date] = {}
            if dept not in attendance_by_date[date]:
                attendance_by_date[date][dept] = 0
            attendance_by_date[date][dept] = count
        
        # Create charts
        if not attendance_by_dept:
            no_data_label = tk.Label(self.charts_frame, text="No attendance data found for the selected criteria", 
                                    font=("Arial", 14), bg="white")
            no_data_label.pack(pady=50)
            return
        
        # Create pie chart for department distribution
        fig1 = plt.Figure(figsize=(6, 4), dpi=100)
        ax1 = fig1.add_subplot(111)
        
        labels = list(attendance_by_dept.keys())
        sizes = list(attendance_by_dept.values())
        
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        ax1.set_title('Attendance Distribution by Department')
        
        chart_frame1 = tk.Frame(self.charts_frame, bg="white")
        chart_frame1.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        chart1 = FigureCanvasTkAgg(fig1, chart_frame1)
        chart1.draw()
        chart1.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create bar chart for attendance trend
        if attendance_by_date:
            fig2 = plt.Figure(figsize=(8, 4), dpi=100)
            ax2 = fig2.add_subplot(111)
            
            # Sort dates
            sorted_dates = sorted(attendance_by_date.keys())
            
            # Get all departments
            all_depts = set()
            for date_data in attendance_by_date.values():
                all_depts.update(date_data.keys())
            
            # Create data for stacked bar chart
            data = {}
            for dept in all_depts:
                data[dept] = []
                for date in sorted_dates:
                    data[dept].append(attendance_by_date[date].get(dept, 0))
            
            bottom = [0] * len(sorted_dates)
            for dept, values in data.items():
                ax2.bar(sorted_dates, values, label=dept, bottom=bottom)
                bottom = [b + v for b, v in zip(bottom, values)]
            
            ax2.set_xlabel('Date')
            ax2.set_ylabel('Attendance Count')
            ax2.set_title('Attendance Trend by Date')
            ax2.legend()
            
            # Rotate x-axis labels for better readability
            plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
            fig2.tight_layout()
            
            chart_frame2 = tk.Frame(self.charts_frame, bg="white")
            chart_frame2.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            chart2 = FigureCanvasTkAgg(fig2, chart_frame2)
            chart2.draw()
            chart2.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def logout(self):
        self.current_user = None
        self.is_admin = False
        self.show_login_frame()

def main():
    root = tk.Tk()
    app = AttendanceSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main()
