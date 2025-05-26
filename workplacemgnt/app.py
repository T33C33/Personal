import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional
import uuid

class WorkplaceManagementSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Workplace Management System")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Data storage
        self.data_file = "workplace_data.json"
        self.workplaces = {}
        self.bookings = {}
        self.users = {}
        self.attendance = {}
        self.time_frames = ["09:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-13:00", 
                           "13:00-14:00", "14:00-15:00", "15:00-16:00", "16:00-17:00"]
        
        # Current user and selections
        self.current_user = None
        self.current_workplace = None
        self.current_hall = None
        self.selected_seat = None
        self.seat_buttons = {}
        
        # Create default admin if not exists
        self.create_default_admin()
        self.load_data()
        self.setup_ui()
        
    def create_default_admin(self):
        """Create default admin user"""
        if not os.path.exists(self.data_file):
            self.users = {
                'admin': {
                    'role': 'Admin',
                    'registered_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            self.save_data()
        
    def load_data(self):
        """Load data from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open (self.data_file, 'r') as f:
                    data = json.load(f)
                    self.workplaces = data.get('workplaces', {})
                    self.bookings = data.get('bookings', {})
                    self.users = data.get('users', {})
                    self.attendance = data.get('attendance', {})
                    self.time_frames = data.get('time_frames', self.time_frames)
        except Exception as e:
            print(f"Error loading data: {e}")
            
    def save_data(self):
        """Save data to JSON file"""
        try:
            data = {
                'workplaces': self.workplaces,
                'bookings': self.bookings,
                'users': self.users,
                'attendance': self.attendance,
                'time_frames': self.time_frames
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")
            
    def setup_ui(self):
        """Setup the main user interface"""
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_login_tab()
        self.create_admin_tab()
        self.create_booking_tab()
        self.create_attendance_tab()
        self.create_reports_tab()
        
       # Initially disable admin-only tabs
        self.notebook.tab(1, state="disabled")  # Admin tab
        self.notebook.tab(4, state="disabled")  # Reports tab
        
    def create_login_tab(self):
        """Create login/user management tab"""
        login_frame = ttk.Frame(self.notebook)
        self.notebook.add(login_frame, text="Login/Users")
        
        # Login section
        login_section = ttk.LabelFrame(login_frame, text="User Login", padding=20)
        login_section.pack(fill=tk.X, padx=10, pady=10)
        
        # Create a frame for login controls using grid
        login_controls = ttk.Frame(login_section)
        login_controls.pack(expand=True)
        
        ttk.Label(login_controls, text="Username:", font=('Arial', 12)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        self.username_entry = ttk.Entry(login_controls, width=25, font=('Arial', 12))
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Button(login_controls, text="Login as User", command=self.login_user, 
                  style='Accent.TButton').grid(row=0, column=2, padx=10, pady=10)
        ttk.Button(login_controls, text="Register New User", command=self.register_user).grid(row=0, column=3, padx=10, pady=10)
        
        # Admin login section
        admin_section = ttk.LabelFrame(login_frame, text="Admin Login", padding=20)
        admin_section.pack(fill=tk.X, padx=10, pady=10)
        
        admin_controls = ttk.Frame(admin_section)
        admin_controls.pack(expand=True)
        
        ttk.Label(admin_controls, text="Admin Password:", font=('Arial', 12)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        self.admin_password_entry = ttk.Entry(admin_controls, width=25, font=('Arial', 12), show="*")
        self.admin_password_entry.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Button(admin_controls, text="Login as Admin", command=self.login_admin, 
                  style='Accent.TButton').grid(row=0, column=2, padx=10, pady=10)
        
        # Current user display
        self.current_user_label = ttk.Label(login_frame, text="Not logged in", 
                                          foreground="red", font=('Arial', 14, 'bold'))
        self.current_user_label.pack(pady=20)
        
        # Users list
        users_section = ttk.LabelFrame(login_frame, text="Registered Users", padding=10)
        users_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.users_tree = ttk.Treeview(users_section, columns=("Role", "Registered"), show="tree headings", height=8)
        self.users_tree.heading("#0", text="Username")
        self.users_tree.heading("Role", text="Role")
        self.users_tree.heading("Registered", text="Registered Date")
        
        # Add scrollbar to users tree
        users_scrollbar = ttk.Scrollbar(users_section, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=users_scrollbar.set)
        
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        users_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_users_list()
        
    def create_admin_tab(self):
        """Create admin management tab"""
        admin_frame = ttk.Frame(self.notebook)
        self.notebook.add(admin_frame, text="Admin Panel")
        
        # Create paned window for better layout
        paned = ttk.PanedWindow(admin_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for controls
        left_panel = ttk.Frame(paned)
        paned.add(left_panel, weight=1)
        
        # Workplace management
        workplace_section = ttk.LabelFrame(left_panel, text="Workplace Management", padding=10)
        workplace_section.pack(fill=tk.X, pady=5)
        
        ttk.Button(workplace_section, text="Create New Workplace", 
                  command=self.create_workplace_dialog).pack(fill=tk.X, pady=2)
        ttk.Button(workplace_section, text="Edit Workplace", 
                  command=self.edit_workplace).pack(fill=tk.X, pady=2)
        ttk.Button(workplace_section, text="Delete Workplace", 
                  command=self.delete_workplace).pack(fill=tk.X, pady=2)
        
        # Hall management
        hall_section = ttk.LabelFrame(left_panel, text="Hall Management", padding=10)
        hall_section.pack(fill=tk.X, pady=5)
        
        ttk.Button(hall_section, text="Add Hall to Workplace", 
                  command=self.add_hall_dialog).pack(fill=tk.X, pady=2)
        ttk.Button(hall_section, text="Edit Hall", 
                  command=self.edit_hall).pack(fill=tk.X, pady=2)
        ttk.Button(hall_section, text="Delete Hall", 
                  command=self.delete_hall).pack(fill=tk.X, pady=2)
        
        # Seat management
        seat_section = ttk.LabelFrame(left_panel, text="Seat Management", padding=10)
        seat_section.pack(fill=tk.X, pady=5)
        
        ttk.Button(seat_section, text="Add Seats to Hall", 
                  command=self.add_seats_dialog).pack(fill=tk.X, pady=2)
        ttk.Button(seat_section, text="Remove Seats", 
                  command=self.remove_seats).pack(fill=tk.X, pady=2)
        ttk.Button(seat_section, text="Rearrange Seats", 
                  command=self.rearrange_seats).pack(fill=tk.X, pady=2)
        
        # Time frames management
        time_section = ttk.LabelFrame(left_panel, text="Time Management", padding=10)
        time_section.pack(fill=tk.X, pady=5)
        
        ttk.Button(time_section, text="Manage Time Frames", 
                  command=self.manage_time_frames).pack(fill=tk.X, pady=2)
        
        # Right panel for tree view
        right_panel = ttk.Frame(paned)
        paned.add(right_panel, weight=2)
        
        # Workplaces tree
        tree_section = ttk.LabelFrame(right_panel, text="Workplaces Structure", padding=10)
        tree_section.pack(fill=tk.BOTH, expand=True)
        
        self.workplace_tree = ttk.Treeview(tree_section, columns=("Type", "Capacity", "Details"), show="tree headings")
        self.workplace_tree.heading("#0", text="Name")
        self.workplace_tree.heading("Type", text="Type")
        self.workplace_tree.heading("Capacity", text="Capacity")
        self.workplace_tree.heading("Details", text="Details")
        
        # Add scrollbars to tree
        tree_v_scrollbar = ttk.Scrollbar(tree_section, orient=tk.VERTICAL, command=self.workplace_tree.yview)
        tree_h_scrollbar = ttk.Scrollbar(tree_section, orient=tk.HORIZONTAL, command=self.workplace_tree.xview)
        self.workplace_tree.configure(yscrollcommand=tree_v_scrollbar.set, xscrollcommand=tree_h_scrollbar.set)
        
        self.workplace_tree.grid(row=0, column=0, sticky="nsew")
        tree_v_scrollbar.grid(row=0, column=1, sticky="ns")
        tree_h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        tree_section.grid_rowconfigure(0, weight=1)
        tree_section.grid_columnconfigure(0, weight=1)
        
        self.refresh_workplace_tree()
        
    def create_booking_tab(self):
        """Create seat booking tab"""
        booking_frame = ttk.Frame(self.notebook)
        self.notebook.add(booking_frame, text="Seat Booking")
        
        # Selection section
        selection_section = ttk.LabelFrame(booking_frame, text="Select Location & Time", padding=15)
        selection_section.pack(fill=tk.X, padx=10, pady=10)
        
        # Create grid frame for selection controls
        selection_grid = ttk.Frame(selection_section)
        selection_grid.pack(expand=True)
        
        ttk.Label(selection_grid, text="Workplace:", font=('Arial', 11)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.workplace_combo = ttk.Combobox(selection_grid, state="readonly", width=20, font=('Arial', 11))
        self.workplace_combo.grid(row=0, column=1, padx=10, pady=5)
        self.workplace_combo.bind("<<ComboboxSelected>>", self.on_workplace_selected)
        
        ttk.Label(selection_grid, text="Hall:", font=('Arial', 11)).grid(row=0, column=2, sticky=tk.W, padx=10, pady=5)
        self.hall_combo = ttk.Combobox(selection_grid, state="readonly", width=20, font=('Arial', 11))
        self.hall_combo.grid(row=0, column=3, padx=10, pady=5)
        self.hall_combo.bind("<<ComboboxSelected>>", self.on_hall_selected)
        
        ttk.Label(selection_grid, text="Date:", font=('Arial', 11)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.date_entry = ttk.Entry(selection_grid, width=15, font=('Arial', 11))
        self.date_entry.grid(row=1, column=1, padx=10, pady=5)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        ttk.Label(selection_grid, text="Time Frame:", font=('Arial', 11)).grid(row=1, column=2, sticky=tk.W, padx=10, pady=5)
        self.timeframe_combo = ttk.Combobox(selection_grid, values=self.time_frames, state="readonly", width=15, font=('Arial', 11))
        self.timeframe_combo.grid(row=1, column=3, padx=10, pady=5)
        
        ttk.Button(selection_grid, text="Load Seats", command=self.refresh_seats, 
                  style='Accent.TButton').grid(row=1, column=4, padx=10, pady=5)
        
        # Seats display section
        seats_section = ttk.LabelFrame(booking_frame, text="Seat Layout", padding=10)
        seats_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create scrollable frame for seats
        canvas = tk.Canvas(seats_section, bg='white')
        v_scrollbar = ttk.Scrollbar(seats_section, orient="vertical", command=canvas.yview)
        h_scrollbar = ttk.Scrollbar(seats_section, orient="horizontal", command=canvas.xview)
        self.seats_frame = ttk.Frame(canvas)
        
        self.seats_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.seats_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        seats_section.grid_rowconfigure(0, weight=1)
        seats_section.grid_columnconfigure(0, weight=1)
        
        # Booking controls
        booking_controls = ttk.Frame(booking_frame)
        booking_controls.pack(fill=tk.X, padx=10, pady=10)
        
        self.selected_seat_label = ttk.Label(booking_controls, text="No seat selected", 
                                           font=('Arial', 12, 'bold'))
        self.selected_seat_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(booking_controls, text="Book Selected Seat", command=self.book_seat, 
                  style='Accent.TButton').pack(side=tk.RIGHT, padx=5)
        ttk.Button(booking_controls, text="My Bookings", command=self.show_my_bookings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(booking_controls, text="Cancel Booking", command=self.cancel_booking).pack(side=tk.RIGHT, padx=5)
        
        # Legend
        legend_frame = ttk.Frame(booking_controls)
        legend_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(legend_frame, text="Legend:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        available_btn = tk.Button(legend_frame, text="Available", bg="lightgreen", width=8, state="disabled")
        available_btn.pack(side=tk.LEFT, padx=2)
        
        booked_btn = tk.Button(legend_frame, text="Booked", bg="lightcoral", width=8, state="disabled")
        booked_btn.pack(side=tk.LEFT, padx=2)
        
        selected_btn = tk.Button(legend_frame, text="Selected", bg="lightblue", width=8, state="disabled")
        selected_btn.pack(side=tk.LEFT, padx=2)
        
        self.refresh_workplace_combo()
        
    def create_attendance_tab(self):
        """Create attendance tracking tab"""
        attendance_frame = ttk.Frame(self.notebook)
        self.notebook.add(attendance_frame, text="Attendance")
        
        # Check-in/out section
        checkin_section = ttk.LabelFrame(attendance_frame, text="Check In/Out", padding=20)
        checkin_section.pack(fill=tk.X, padx=10, pady=10)
        
        checkin_controls = ttk.Frame(checkin_section)
        checkin_controls.pack(expand=True)
        
        self.attendance_status_label = ttk.Label(checkin_controls, text="Status: Not checked in", 
                                               font=('Arial', 12))
        self.attendance_status_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        ttk.Button(checkin_controls, text="Check In", command=self.check_in, 
                  style='Accent.TButton').grid(row=1, column=0, padx=10, pady=5)
        ttk.Button(checkin_controls, text="Check Out", command=self.check_out, 
                  style='Accent.TButton').grid(row=1, column=1, padx=10, pady=5)
        ttk.Button(checkin_controls, text="View My Attendance", command=self.view_my_attendance).grid(row=1, column=2, padx=10, pady=5)
        
        # Attendance records
        records_section = ttk.LabelFrame(attendance_frame, text="Attendance Records", padding=10)
        records_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.attendance_tree = ttk.Treeview(records_section, columns=("Date", "Check In", "Check Out", "Duration"), show="tree headings")
        self.attendance_tree.heading("#0", text="User")
        self.attendance_tree.heading("Date", text="Date")
        self.attendance_tree.heading("Check In", text="Check In")
        self.attendance_tree.heading("Check Out", text="Check Out")
        self.attendance_tree.heading("Duration", text="Duration")
        
        # Add scrollbar to attendance tree
        attendance_scrollbar = ttk.Scrollbar(records_section, orient=tk.VERTICAL, command=self.attendance_tree.yview)
        self.attendance_tree.configure(yscrollcommand=attendance_scrollbar.set)
        
        self.attendance_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        attendance_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.update_attendance_status()
        
    def create_reports_tab(self):
        """Create reports tab"""
        reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(reports_frame, text="Reports")
        
        # Report controls
        controls_section = ttk.LabelFrame(reports_frame, text="Generate Reports", padding=15)
        controls_section.pack(fill=tk.X, padx=10, pady=10)
        
        report_controls = ttk.Frame(controls_section)
        report_controls.pack(expand=True)
        
        ttk.Button(report_controls, text="Booking Report", command=self.generate_booking_report).grid(row=0, column=0, padx=10, pady=5)
        ttk.Button(report_controls, text="Attendance Report", command=self.generate_attendance_report).grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(report_controls, text="Utilization Report", command=self.generate_utilization_report).grid(row=0, column=2, padx=10, pady=5)
        ttk.Button(report_controls, text="Daily Summary", command=self.generate_daily_summary).grid(row=0, column=3, padx=10, pady=5)
        
        # Report display
        report_display_frame = ttk.Frame(reports_frame)
        report_display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.report_text = tk.Text(report_display_frame, wrap=tk.WORD, font=('Courier', 10))
        scrollbar_report = ttk.Scrollbar(report_display_frame, orient=tk.VERTICAL, command=self.report_text.yview)
        
        self.report_text.grid(row=0, column=0, sticky="nsew")
        scrollbar_report.grid(row=0, column=1, sticky="ns")
        self.report_text.config(yscrollcommand=scrollbar_report.set)
        
        report_display_frame.grid_rowconfigure(0, weight=1)
        report_display_frame.grid_columnconfigure(0, weight=1)
        
    def login_user(self):
        """Login regular user"""
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Please enter a username")
            return
            
        if username not in self.users:
            messagebox.showerror("Error", "User not found. Please register first.")
            return
            
        if self.users[username]['role'] == 'Admin':
            messagebox.showerror("Error", "Admin users must use admin login")
            return
            
        self.current_user = username
        self.current_user_label.config(text=f"Logged in as: {username} (User)", foreground="green")
        self.update_attendance_status()
        messagebox.showinfo("Success", f"Logged in successfully as {username}")
        
    def login_admin(self):
        """Login admin user"""
        password = self.admin_password_entry.get().strip()
        if password != "admin123":  # Simple password for demo
            messagebox.showerror("Error", "Invalid admin password")
            return
            
        self.current_user = "admin"
        self.current_user_label.config(text="Logged in as: Admin", foreground="blue")
        
        # Enable admin tabs
        self.notebook.tab(1, state="normal")  # Admin tab
        self.notebook.tab(4, state="normal")  # Reports tab
        
        self.update_attendance_status()
        messagebox.showinfo("Success", "Logged in successfully as Admin")
        
    def register_user(self):
        """Register new user"""
        username = self.username_entry.get().strip()
        
        if not username:
            messagebox.showerror("Error", "Please enter a username")
            return
            
        if username in self.users:
            messagebox.showerror("Error", "Username already exists")
            return
            
        if username.lower() == 'admin':
            messagebox.showerror("Error", "Cannot register as admin")
            return
            
        self.users[username] = {
            'role': 'User',
            'registered_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.save_data()
        self.refresh_users_list()
        messagebox.showinfo("Success", f"User {username} registered successfully")
        
    def refresh_users_list(self):
        """Refresh the users list"""
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
            
        for username, data in self.users.items():
            self.users_tree.insert("", tk.END, text=username, values=(data['role'], data['registered_date']))
            
    def create_workplace_dialog(self):
        """Create new workplace with dialog"""
        if not self.is_admin():
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Workplace")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Workplace Name:", font=('Arial', 12)).pack(pady=10)
        name_entry = ttk.Entry(dialog, width=30, font=('Arial', 12))
        name_entry.pack(pady=5)
        name_entry.focus()
        
        ttk.Label(dialog, text="Description (optional):", font=('Arial', 12)).pack(pady=(20, 5))
        desc_entry = tk.Text(dialog, width=40, height=3, font=('Arial', 10))
        desc_entry.pack(pady=5)
        
        def create_wp():
            name = name_entry.get().strip()
            description = desc_entry.get(1.0, tk.END).strip()
            
            if not name:
                messagebox.showerror("Error", "Please enter a workplace name")
                return
                
            if name in self.workplaces:
                messagebox.showerror("Error", "Workplace already exists")
                return
                
            self.workplaces[name] = {
                'halls': {},
                'description': description,
                'created_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.save_data()
            self.refresh_workplace_tree()
            self.refresh_workplace_combo()
            dialog.destroy()
            messagebox.showinfo("Success", f"Workplace '{name}' created successfully")
            
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Create", command=create_wp, style='Accent.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        
    def add_hall_dialog(self):
        """Add hall to workplace with dialog"""
        if not self.is_admin():
            return
            
        if not self.workplaces:
            messagebox.showwarning("Warning", "No workplaces available. Create a workplace first.")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Hall to Workplace")
        dialog.geometry("450x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select Workplace:", font=('Arial', 12)).pack(pady=10)
        workplace_var = tk.StringVar()
        workplace_combo = ttk.Combobox(dialog, textvariable=workplace_var, values=list(self.workplaces.keys()), 
                                     state="readonly", width=30, font=('Arial', 11))
        workplace_combo.pack(pady=5)
        
        ttk.Label(dialog, text="Hall Name:", font=('Arial', 12)).pack(pady=(20, 5))
        hall_name_entry = ttk.Entry(dialog, width=30, font=('Arial', 12))
        hall_name_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Number of Seats:", font=('Arial', 12)).pack(pady=(20, 5))
        seats_var = tk.IntVar(value=20)
        seats_spinbox = ttk.Spinbox(dialog, from_=1, to=100, textvariable=seats_var, width=10, font=('Arial', 12))
        seats_spinbox.pack(pady=5)
        
        def add_hall():
            workplace = workplace_var.get()
            hall_name = hall_name_entry.get().strip()
            num_seats = seats_var.get()
            
            if not workplace:
                messagebox.showerror("Error", "Please select a workplace")
                return
                
            if not hall_name:
                messagebox.showerror("Error", "Please enter a hall name")
                return
                
            if hall_name in self.workplaces[workplace]['halls']:
                messagebox.showerror("Error", "Hall already exists in this workplace")
                return
                
            # Create hall with seats
            self.workplaces[workplace]['halls'][hall_name] = {
                'seats': {},
                'layout': {'rows': 0, 'cols': 0},
                'created_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Add seats
            for i in range(num_seats):
                seat_id = f"{hall_name}-{i + 1:03d}"
                self.workplaces[workplace]['halls'][hall_name]['seats'][seat_id] = {
                    'position': {'row': i // 10, 'col': i % 10},  # Default 10 seats per row
                    'created_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
            # Update layout
            rows = (num_seats - 1) // 10 + 1
            self.workplaces[workplace]['halls'][hall_name]['layout'] = {'rows': rows, 'cols': 10}
            
            self.save_data()
            self.refresh_workplace_tree()
            dialog.destroy()
            messagebox.showinfo("Success", f"Hall '{hall_name}' with {num_seats} seats added successfully")
            
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Add Hall", command=add_hall, style='Accent.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        
    def add_seats_dialog(self):
        """Add more seats to existing hall"""
        if not self.is_admin():
            return
            
        # Get all halls
        halls = []
        for wp_name, wp_data in self.workplaces.items():
            for hall_name in wp_data['halls']:
                halls.append(f"{wp_name} -> {hall_name}")
                
        if not halls:
            messagebox.showwarning("Warning", "No halls available. Create a hall first.")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Seats to Hall")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select Hall:", font=('Arial', 12)).pack(pady=10)
        hall_var = tk.StringVar()
        hall_combo = ttk.Combobox(dialog, textvariable=hall_var, values=halls, 
                                state="readonly", width=40, font=('Arial', 11))
        hall_combo.pack(pady=5)
        
        ttk.Label(dialog, text="Number of Additional Seats:", font=('Arial', 12)).pack(pady=(20, 5))
        seats_var = tk.IntVar(value=10)
        seats_spinbox = ttk.Spinbox(dialog, from_=1, to=50, textvariable=seats_var, width=10, font=('Arial', 12))
        seats_spinbox.pack(pady=5)
        
        def add_seats():
            hall_selection = hall_var.get()
            if not hall_selection:
                messagebox.showerror("Error", "Please select a hall")
                return
                
            workplace_name, hall_name = hall_selection.split(" -> ")
            num_seats = seats_var.get()
            
            current_seats = len(self.workplaces[workplace_name]['halls'][hall_name]['seats'])
            
            for i in range(num_seats):
                seat_id = f"{hall_name}-{current_seats + i + 1:03d}"
                row = (current_seats + i) // 10
                col = (current_seats + i) % 10
                
                self.workplaces[workplace_name]['halls'][hall_name]['seats'][seat_id] = {
                    'position': {'row': row, 'col': col},
                    'created_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
            # Update layout
            total_seats = current_seats + num_seats
            rows = (total_seats - 1) // 10 + 1
            self.workplaces[workplace_name]['halls'][hall_name]['layout'] = {'rows': rows, 'cols': 10}
            
            self.save_data()
            self.refresh_workplace_tree()
            dialog.destroy()
            messagebox.showinfo("Success", f"{num_seats} seats added to {hall_name}")
            
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Add Seats", command=add_seats, style='Accent.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        
    def edit_workplace(self):
        """Edit workplace"""
        if not self.is_admin():
            return
            
        if not self.workplaces:
            messagebox.showwarning("Warning", "No workplaces to edit")
            return
            
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Workplace")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select Workplace to Edit:", font=('Arial', 12)).pack(pady=10)
        workplace_var = tk.StringVar()
        workplace_combo = ttk.Combobox(dialog, textvariable=workplace_var, values=list(self.workplaces.keys()), 
                                     state="readonly", width=30, font=('Arial', 11))
        workplace_combo.pack(pady=5)
        
        def edit_selected():
            old_name = workplace_var.get()
            if not old_name:
                messagebox.showerror("Error", "Please select a workplace")
                return
                
            dialog.destroy()
            
            # Create edit dialog
            edit_dialog = tk.Toplevel(self.root)
            edit_dialog.title("Edit Workplace Details")
            edit_dialog.geometry("400x250")
            edit_dialog.transient(self.root)
            edit_dialog.grab_set()
            
            ttk.Label(edit_dialog, text="Workplace Name:", font=('Arial', 12)).pack(pady=10)
            name_entry = ttk.Entry(edit_dialog, width=30, font=('Arial', 12))
            name_entry.pack(pady=5)
            name_entry.insert(0, old_name)
            
            ttk.Label(edit_dialog, text="Description:", font=('Arial', 12)).pack(pady=(20, 5))
            desc_entry = tk.Text(edit_dialog, width=40, height=4, font=('Arial', 10))
            desc_entry.pack(pady=5)
            desc_entry.insert(1.0, self.workplaces[old_name].get('description', ''))
            
            def save_changes():
                new_name = name_entry.get().strip()
                description = desc_entry.get(1.0, tk.END).strip()
                
                if not new_name:
                    messagebox.showerror("Error", "Please enter a workplace name")
                    return
                    
                if new_name != old_name and new_name in self.workplaces:
                    messagebox.showerror("Error", "Workplace name already exists")
                    return
                    
                # Update workplace
                if new_name != old_name:
                    self.workplaces[new_name] = self.workplaces.pop(old_name)
                    
                self.workplaces[new_name]['description'] = description
                self.save_data()
                self.refresh_workplace_tree()
                self.refresh_workplace_combo()
                edit_dialog.destroy()
                messagebox.showinfo("Success", "Workplace updated successfully")
                
            button_frame = ttk.Frame(edit_dialog)
            button_frame.pack(pady=20)
            
            ttk.Button(button_frame, text="Save Changes", command=save_changes, style='Accent.TButton').pack(side=tk.LEFT, padx=10)
            ttk.Button(button_frame, text="Cancel", command=edit_dialog.destroy).pack(side=tk.LEFT, padx=10)
            
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Edit", command=edit_selected, style='Accent.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        
    def delete_workplace(self):
        """Delete workplace"""
        if not self.is_admin():
            return
            
        if not self.workplaces:
            messagebox.showwarning("Warning", "No workplaces to delete")
            return
            
        workplace_list = list(self.workplaces.keys())
        selected = simpledialog.askstring("Delete Workplace", 
                                        f"Enter workplace name to delete:\n\nAvailable workplaces:\n" + 
                                        "\n".join(workplace_list))
        
        if selected and selected in self.workplaces:
            if messagebox.askyesno("Confirm Deletion", 
                                 f"Are you sure you want to delete workplace '{selected}'?\n\n" +
                                 "This will also delete all halls and seats in this workplace."):
                del self.workplaces[selected]
                self.save_data()
                self.refresh_workplace_tree()
                self.refresh_workplace_combo()
                messagebox.showinfo("Success", f"Workplace '{selected}' deleted successfully")
                
    def edit_hall(self):
        """Edit hall details"""
        if not self.is_admin():
            return
            
        # Get all halls
        halls = []
        for wp_name, wp_data in self.workplaces.items():
            for hall_name in wp_data['halls']:
                halls.append(f"{wp_name} -> {hall_name}")
                
        if not halls:
            messagebox.showwarning("Warning", "No halls available")
            return
            
        selected = simpledialog.askstring("Edit Hall", 
                                        f"Enter hall to edit (format: Workplace -> Hall):\n\n" +
                                        "Available halls:\n" + "\n".join(halls))
        
        if selected and selected in halls:
            workplace_name, hall_name = selected.split(" -> ")
            new_name = simpledialog.askstring("Edit Hall", f"Enter new name for hall '{hall_name}':")
            
            if new_name and new_name != hall_name:
                if new_name not in self.workplaces[workplace_name]['halls']:
                    self.workplaces[workplace_name]['halls'][new_name] = self.workplaces[workplace_name]['halls'].pop(hall_name)
                    self.save_data()
                    self.refresh_workplace_tree()
                    messagebox.showinfo("Success", f"Hall renamed to '{new_name}'")
                else:
                    messagebox.showerror("Error", "Hall name already exists")
                    
    def delete_hall(self):
        """Delete hall"""
        if not self.is_admin():
            return
            
        # Get all halls
        halls = []
        for wp_name, wp_data in self.workplaces.items():
            for hall_name in wp_data['halls']:
                halls.append(f"{wp_name} -> {hall_name}")
                
        if not halls:
            messagebox.showwarning("Warning", "No halls available")
            return
            
        selected = simpledialog.askstring("Delete Hall", 
                                        f"Enter hall to delete (format: Workplace -> Hall):\n\n" +
                                        "Available halls:\n" + "\n".join(halls))
        
        if selected and selected in halls:
            workplace_name, hall_name = selected.split(" -> ")
            if messagebox.askyesno("Confirm Deletion", 
                                 f"Are you sure you want to delete hall '{hall_name}'?\n\n" +
                                 "This will also delete all seats in this hall."):
                del self.workplaces[workplace_name]['halls'][hall_name]
                self.save_data()
                self.refresh_workplace_tree()
                messagebox.showinfo("Success", f"Hall '{hall_name}' deleted successfully")
                
    def remove_seats(self):
        """Remove specific seats from hall"""
        if not self.is_admin():
            return
            
        # Get all halls with seats
        halls_with_seats = []
        for wp_name, wp_data in self.workplaces.items():
            for hall_name, hall_data in wp_data['halls'].items():
                if hall_data['seats']:
                    halls_with_seats.append(f"{wp_name} -> {hall_name}")
                    
        if not halls_with_seats:
            messagebox.showwarning("Warning", "No halls with seats available")
            return
            
        selected_hall = simpledialog.askstring("Remove Seats", 
                                             f"Select hall (format: Workplace -> Hall):\n\n" +
                                             "Available halls:\n" + "\n".join(halls_with_seats))
        
        if selected_hall and selected_hall in halls_with_seats:
            workplace_name, hall_name = selected_hall.split(" -> ")
            seats = list(self.workplaces[workplace_name]['halls'][hall_name]['seats'].keys())
            
            num_to_remove = simpledialog.askinteger("Remove Seats", 
                                                   f"How many seats to remove from '{hall_name}'?\n" +
                                                   f"Current seats: {len(seats)}", 
                                                   minvalue=1, maxvalue=len(seats))
            
            if num_to_remove:
                # Remove last N seats
                for i in range(num_to_remove):
                    if seats:
                        seat_to_remove = seats.pop()
                        del self.workplaces[workplace_name]['halls'][hall_name]['seats'][seat_to_remove]
                        
                # Update layout
                remaining_seats = len(self.workplaces[workplace_name]['halls'][hall_name]['seats'])
                if remaining_seats > 0:
                    rows = (remaining_seats - 1) // 10 + 1
                    self.workplaces[workplace_name]['halls'][hall_name]['layout'] = {'rows': rows, 'cols': 10}
                else:
                    self.workplaces[workplace_name]['halls'][hall_name]['layout'] = {'rows': 0, 'cols': 0}
                    
                self.save_data()
                self.refresh_workplace_tree()
                messagebox.showinfo("Success", f"{num_to_remove} seats removed from '{hall_name}'")
                
    def rearrange_seats(self):
        """Rearrange seats in a hall"""
        if not self.is_admin():
            return
            
        messagebox.showinfo("Feature", "Seat rearrangement feature will be available in the next version.\n" +
                          "Currently, seats are automatically arranged in a 10-column grid layout.")
        
    def manage_time_frames(self):
        """Manage time frames"""
        if not self.is_admin():
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Manage Time Frames")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Current time frames
        ttk.Label(dialog, text="Current Time Frames:", font=('Arial', 12, 'bold')).pack(pady=10)
        
        listbox_frame = ttk.Frame(dialog)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        listbox = tk.Listbox(listbox_frame, height=12, font=('Arial', 11))
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        for tf in self.time_frames:
            listbox.insert(tk.END, tf)
            
        # Controls
        controls = ttk.Frame(dialog)
        controls.pack(fill=tk.X, padx=20, pady=10)
        
        def add_timeframe():
            tf = simpledialog.askstring("Add Time Frame", 
                                       "Enter time frame (format: HH:MM-HH:MM):\n\nExample: 09:00-10:00")
            if tf and tf not in self.time_frames:
                # Validate format
                try:
                    start, end = tf.split('-')
                    datetime.strptime(start, '%H:%M')
                    datetime.strptime(end, '%H:%M')
                    self.time_frames.append(tf)
                    listbox.insert(tk.END, tf)
                except:
                    messagebox.showerror("Error", "Invalid time format. Use HH:MM-HH:MM")
            elif tf in self.time_frames:
                messagebox.showerror("Error", "Time frame already exists")
                
        def remove_timeframe():
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                removed_tf = self.time_frames.pop(index)
                listbox.delete(index)
                messagebox.showinfo("Removed", f"Time frame '{removed_tf}' removed")
            else:
                messagebox.showwarning("Warning", "Please select a time frame to remove")
                
        def save_timeframes():
            if len(self.time_frames) == 0:
                messagebox.showerror("Error", "At least one time frame is required")
                return
                
            self.save_data()
            # Update combo box in booking tab
            self.timeframe_combo['values'] = self.time_frames
            dialog.destroy()
            messagebox.showinfo("Success", "Time frames updated successfully")
            
        ttk.Button(controls, text="Add Time Frame", command=add_timeframe).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Remove Selected", command=remove_timeframe).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Save Changes", command=save_timeframes, style='Accent.TButton').pack(side=tk.RIGHT, padx=5)
        ttk.Button(controls, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
    def refresh_workplace_tree(self):
        """Refresh workplace tree view"""
        for item in self.workplace_tree.get_children():
            self.workplace_tree.delete(item)
            
        for wp_name, wp_data in self.workplaces.items():
            total_seats = sum(len(hall_data['seats']) for hall_data in wp_data['halls'].values())
            wp_item = self.workplace_tree.insert("", tk.END, text=wp_name, 
                                                values=("Workplace", len(wp_data['halls']), f"{total_seats} total seats"))
            
            for hall_name, hall_data in wp_data['halls'].items():
                hall_item = self.workplace_tree.insert(wp_item, tk.END, text=hall_name, 
                                                     values=("Hall", len(hall_data['seats']), f"Layout: {hall_data.get('layout', {}).get('rows', 0)}x{hall_data.get('layout', {}).get('cols', 0)}"))
                
                # Show first few seats as examples
                seat_list = list(hall_data['seats'].keys())
                for i, seat_id in enumerate(seat_list[:5]):  # Show first 5 seats
                    self.workplace_tree.insert(hall_item, tk.END, text=f"Seat {seat_id}", 
                                             values=("Seat", "-", f"Row {hall_data['seats'][seat_id].get('position', {}).get('row', 0)}, Col {hall_data['seats'][seat_id].get('position', {}).get('col', 0)}"))
                
                if len(seat_list) > 5:
                    self.workplace_tree.insert(hall_item, tk.END, text=f"... and {len(seat_list) - 5} more seats", 
                                             values=("Info", "-", ""))
                    
    def refresh_workplace_combo(self):
        """Refresh workplace combo box"""
        self.workplace_combo['values'] = list(self.workplaces.keys())
        
    def on_workplace_selected(self, event):
        """Handle workplace selection"""
        workplace = self.workplace_combo.get()
        if workplace in self.workplaces:
            self.current_workplace = workplace
            halls = list(self.workplaces[workplace]['halls'].keys())
            self.hall_combo['values'] = halls
            self.hall_combo.set("")
            self.current_hall = None
            
    def on_hall_selected(self, event):
        """Handle hall selection"""
        hall = self.hall_combo.get()
        if hall and self.current_workplace:
            self.current_hall = hall
            
    def refresh_seats(self):
        """Refresh seats display with improved layout"""
        # Clear existing seats
        for widget in self.seats_frame.winfo_children():
            widget.destroy()
            
        if not self.current_workplace or not self.current_hall:
            ttk.Label(self.seats_frame, text="Please select workplace and hall first", 
                     font=('Arial', 14)).pack(pady=50)
            return
            
        date = self.date_entry.get()
        timeframe = self.timeframe_combo.get()
        
        if not date or not timeframe:
            ttk.Label(self.seats_frame, text="Please select date and time frame", 
                     font=('Arial', 14)).pack(pady=50)
            return
            
        seats_data = self.workplaces[self.current_workplace]['halls'][self.current_hall]['seats']
        
        if not seats_data:
            ttk.Label(self.seats_frame, text="No seats available in this hall", 
                     font=('Arial', 14)).pack(pady=50)
            return
            
        # Create title
        title_label = ttk.Label(self.seats_frame, 
                               text=f"Seat Layout - {self.current_workplace} > {self.current_hall}", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=15, pady=20)
        
        # Create seat buttons with improved layout
        self.seat_buttons = {}
        layout = self.workplaces[self.current_workplace]['halls'][self.current_hall].get('layout', {'rows': 0, 'cols': 10})
        
        for seat_id, seat_info in seats_data.items():
            position = seat_info.get('position', {'row': 0, 'col': 0})
            row = position['row'] + 2  # +2 to account for title and spacing
            col = position['col']
            
            is_booked = self.is_seat_booked(self.current_workplace, self.current_hall, seat_id, date, timeframe)
            
            # Determine seat color and status
            if is_booked:
                color = "lightcoral"
                status = "BOOKED"
                state = "disabled"
            else:
                color = "lightgreen"
                status = "AVAILABLE"
                state = "normal"
                
            # Create seat button with seat number
            seat_number = seat_id.split('-')[-1]  # Get the number part
            btn = tk.Button(self.seats_frame, 
                           text=f"Seat\n{seat_number}\n{status}", 
                           bg=color, 
                           fg="black" if not is_booked else "white",
                           width=8, 
                           height=3,
                           font=('Arial', 9, 'bold'),
                           relief="raised",
                           borderwidth=2,
                           state=state,
                           command=lambda s=seat_id: self.select_seat(s))
            
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            self.seat_buttons[seat_id] = btn
            
        # Add row labels
        for row in range(layout.get('rows', 0)):
            row_label = ttk.Label(self.seats_frame, text=f"Row {row + 1}", font=('Arial', 10, 'bold'))
            row_label.grid(row=row + 2, column=12, padx=10, sticky="w")
            
        self.selected_seat = None
        self.selected_seat_label.config(text="No seat selected")
        
    def select_seat(self, seat_id):
        """Select a seat for booking"""
        date = self.date_entry.get()
        timeframe = self.timeframe_combo.get()
        
        if self.is_seat_booked(self.current_workplace, self.current_hall, seat_id, date, timeframe):
            messagebox.showwarning("Warning", "This seat is already booked for the selected time")
            return
            
        # Reset all available seat button colors
        for sid, btn in self.seat_buttons.items():
            if not self.is_seat_booked(self.current_workplace, self.current_hall, sid, date, timeframe):
                btn.config(bg="lightgreen")
                
        # Highlight selected seat
        self.seat_buttons[seat_id].config(bg="lightblue")
        self.selected_seat = seat_id
        
        # Update selected seat label
        seat_number = seat_id.split('-')[-1]
        self.selected_seat_label.config(text=f"Selected: Seat {seat_number}")
        
    def book_seat(self):
        """Book the selected seat"""
        if not self.current_user:
            messagebox.showerror("Error", "Please login first")
            return
            
        if self.current_user == "admin":
            messagebox.showerror("Error", "Admin cannot book seats. Please login as a regular user.")
            return
            
        if not self.selected_seat:
            messagebox.showerror("Error", "Please select a seat first")
            return
            
        date = self.date_entry.get()
        timeframe = self.timeframe_combo.get()
        
        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
            return
            
        booking_id = str(uuid.uuid4())
        booking_key = f"{self.current_workplace}_{self.current_hall}_{self.selected_seat}_{date}_{timeframe}"
        
        if booking_key in self.bookings:
            messagebox.showerror("Error", "Seat already booked for this time")
            return
            
        self.bookings[booking_key] = {
            'booking_id': booking_id,
            'user': self.current_user,
            'workplace': self.current_workplace,
            'hall': self.current_hall,
            'seat': self.selected_seat,
            'date': date,
            'timeframe': timeframe,
            'booking_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.save_data()
        self.refresh_seats()
        
        seat_number = self.selected_seat.split('-')[-1]
        messagebox.showinfo("Success", 
                          f"Seat {seat_number} booked successfully!\n\n" +
                          f"Details:\n" +
                          f"Workplace: {self.current_workplace}\n" +
                          f"Hall: {self.current_hall}\n" +
                          f"Date: {date}\n" +
                          f"Time: {timeframe}")
        
    def cancel_booking(self):
        """Cancel a booking"""
        if not self.current_user:
            messagebox.showerror("Error", "Please login first")
            return
            
        if self.current_user == "admin":
            messagebox.showerror("Error", "Admin cannot cancel bookings. Please login as a regular user.")
            return
            
        # Show user's bookings for cancellation
        user_bookings = [(key, booking) for key, booking in self.bookings.items() 
                        if booking['user'] == self.current_user]
        
        if not user_bookings:
            messagebox.showinfo("Info", "You have no bookings to cancel")
            return
            
        # Create cancellation dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Cancel Booking")
        dialog.geometry("800x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select booking to cancel:", font=('Arial', 12, 'bold')).pack(pady=10)
        
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tree = ttk.Treeview(tree_frame, columns=("Workplace", "Hall", "Seat", "Date", "Time", "Booked"), show="tree headings")
        tree.heading("#0", text="Booking ID")
        tree.heading("Workplace", text="Workplace")
        tree.heading("Hall", text="Hall")
        tree.heading("Seat", text="Seat")
        tree.heading("Date", text="Date")
        tree.heading("Time", text="Time Frame")
        tree.heading("Booked", text="Booking Time")
        
        # Add scrollbar
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=tree_scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        for key, booking in user_bookings:
            seat_number = booking['seat'].split('-')[-1]
            tree.insert("", tk.END, text=booking['booking_id'][:8], 
                       values=(booking['workplace'], booking['hall'], f"Seat {seat_number}", 
                              booking['date'], booking['timeframe'], booking['booking_time']))
        
        def cancel_selected():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a booking to cancel")
                return
                
            item = selection[0]
            booking_id = tree.item(item, "text")
            
            if messagebox.askyesno("Confirm Cancellation", "Are you sure you want to cancel this booking?"):
                # Find and delete booking
                for key, booking in list(self.bookings.items()):
                    if booking['booking_id'].startswith(booking_id):
                        del self.bookings[key]
                        break
                        
                self.save_data()
                dialog.destroy()
                self.refresh_seats()
                messagebox.showinfo("Success", "Booking cancelled successfully")
                
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Cancel Selected Booking", command=cancel_selected, 
                  style='Accent.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        
    def show_my_bookings(self):
        """Show current user's bookings"""
        if not self.current_user:
            messagebox.showerror("Error", "Please login first")
            return
        
        if self.current_user == "admin":
            messagebox.showerror("Error", "Admin cannot view bookings. Please login as a regular user.")
            return
            
        user_bookings = [booking for booking in self.bookings.values() 
                        if booking['user'] == self.current_user]
        
        if not user_bookings:
            messagebox.showinfo("Info", "You have no current bookings")
            return
            
        # Create bookings dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("My Bookings")
        dialog.geometry("900x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"Bookings for {self.current_user}", font=('Arial', 14, 'bold')).pack(pady=10)
        
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tree = ttk.Treeview(tree_frame, columns=("Workplace", "Hall", "Seat", "Date", "Time", "Booked"), show="tree headings")
        tree.heading("#0", text="Booking ID")
        tree.heading("Workplace", text="Workplace")
        tree.heading("Hall", text="Hall")
        tree.heading("Seat", text="Seat")
        tree.heading("Date", text="Date")
        tree.heading("Time", text="Time Frame")
        tree.heading("Booked", text="Booking Time")
        
        # Add scrollbar
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=tree_scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        for booking in user_bookings:
            seat_number = booking['seat'].split('-')[-1]
            tree.insert("", tk.END, text=booking['booking_id'][:8], 
                       values=(booking['workplace'], booking['hall'], f"Seat {seat_number}", 
                              booking['date'], booking['timeframe'], booking['booking_time']))
                              
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=20)
                              
    def is_seat_booked(self, workplace, hall, seat_id, date, timeframe):
        """Check if a seat is booked for given time"""
        booking_key = f"{workplace}_{hall}_{seat_id}_{date}_{timeframe}"
        return booking_key in self.bookings
        
    def check_in(self):
        """Check in user"""
        if not self.current_user:
            messagebox.showerror("Error", "Please login first")
            return
            
        if self.current_user == "admin":
            messagebox.showerror("Error", "Admin cannot check in. Please login as a regular user.")
            return
            
        today = datetime.now().strftime("%Y-%m-%d")
        time_now = datetime.now().strftime("%H:%M:%S")
        
        attendance_key = f"{self.current_user}_{today}"
        
        if attendance_key in self.attendance:
            if 'check_out' not in self.attendance[attendance_key]:
                messagebox.showwarning("Warning", "You are already checked in")
                return
            else:
                messagebox.showwarning("Warning", "You have already completed attendance for today")
                return
                
        self.attendance[attendance_key] = {
            'user': self.current_user,
            'date': today,
            'check_in': time_now
        }
        
        self.save_data()
        self.update_attendance_status()
        messagebox.showinfo("Success", f"Checked in at {time_now}")
        
    def check_out(self):
        """Check out user"""
        if not self.current_user:
            messagebox.showerror("Error", "Please login first")
            return
            
        if self.current_user == "admin":
            messagebox.showerror("Error", "Admin cannot check out. Please login as a regular user.")
            return
            
        today = datetime.now().strftime("%Y-%m-%d")
        time_now = datetime.now().strftime("%H:%M:%S")
        
        attendance_key = f"{self.current_user}_{today}"
        
        if attendance_key not in self.attendance:
            messagebox.showerror("Error", "You haven't checked in today")
            return
            
        if 'check_out' in self.attendance[attendance_key]:
            messagebox.showwarning("Warning", "You have already checked out today")
            return
            
        self.attendance[attendance_key]['check_out'] = time_now
        
        # Calculate duration
        check_in_time = datetime.strptime(self.attendance[attendance_key]['check_in'], "%H:%M:%S")
        check_out_time = datetime.strptime(time_now, "%H:%M:%S")
        duration = check_out_time - check_in_time
        self.attendance[attendance_key]['duration'] = str(duration)
        
        self.save_data()
        self.update_attendance_status()
        messagebox.showinfo("Success", f"Checked out at {time_now}. Duration: {duration}")
        
    def update_attendance_status(self):
        """Update attendance status display"""
        if not self.current_user or self.current_user == "admin":
            self.attendance_status_label.config(text="Status: Not applicable")
            return
            
        today = datetime.now().strftime("%Y-%m-%d")
        attendance_key = f"{self.current_user}_{today}"
        
        if attendance_key in self.attendance:
            att = self.attendance[attendance_key]
            if 'check_out' in att:
                self.attendance_status_label.config(
                    text=f"Status: Checked out at {att['check_out']} (Duration: {att.get('duration', 'N/A')})",
                    foreground="blue"
                )
            else:
                self.attendance_status_label.config(
                    text=f"Status: Checked in at {att['check_in']}",
                    foreground="green"
                )
        else:
            self.attendance_status_label.config(
                text="Status: Not checked in today",
                foreground="red"
            )
        
    def view_my_attendance(self):
        """View current user's attendance"""
        if not self.current_user:
            messagebox.showerror("Error", "Please login first")
            return
            
        if self.current_user == "admin":
            # Show all attendance for admin
            user_attendance = list(self.attendance.values())
            title = "All User Attendance Records"
        else:
            user_attendance = [att for att in self.attendance.values() 
                              if att['user'] == self.current_user]
            title = f"Attendance Records for {self.current_user}"
        
        if not user_attendance:
            messagebox.showinfo("Info", "No attendance records found")
            return
            
        # Clear and populate attendance tree
        for item in self.attendance_tree.get_children():
            self.attendance_tree.delete(item)
            
        for att in sorted(user_attendance, key=lambda x: x['date'], reverse=True):
            check_out = att.get('check_out', 'Not checked out')
            duration = att.get('duration', 'N/A')
            self.attendance_tree.insert("", tk.END, text=att['user'], 
                                      values=(att['date'], att['check_in'], check_out, duration))
                                      
        # Switch to attendance tab
        self.notebook.select(3)
        
    def generate_booking_report(self):
        """Generate booking report"""
        if not self.is_admin():
            return
            
        report = "BOOKING REPORT\n"
        report += "=" * 60 + "\n"
        report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        total_bookings = len(self.bookings)
        report += f"Total Bookings: {total_bookings}\n\n"
        
        if total_bookings == 0:
            report += "No bookings found.\n"
        else:
            # Bookings by user
            user_bookings = {}
            for booking in self.bookings.values():
                user = booking['user']
                user_bookings[user] = user_bookings.get(user, 0) + 1
                
            report += "BOOKINGS BY USER:\n"
            report += "-" * 30 + "\n"
            for user, count in sorted(user_bookings.items(), key=lambda x: x[1], reverse=True):
                report += f"  {user:<20}: {count:>3} bookings\n"
                
            report += "\n"
            
            # Bookings by workplace
            workplace_bookings = {}
            for booking in self.bookings.values():
                wp = booking['workplace']
                workplace_bookings[wp] = workplace_bookings.get(wp, 0) + 1
                
            report += "BOOKINGS BY WORKPLACE:\n"
            report += "-" * 30 + "\n"
            for wp, count in sorted(workplace_bookings.items(), key=lambda x: x[1], reverse=True):
                report += f"  {wp:<20}: {count:>3} bookings\n"
                
            report += "\n"
            
            # Bookings by time frame
            timeframe_bookings = {}
            for booking in self.bookings.values():
                tf = booking['timeframe']
                timeframe_bookings[tf] = timeframe_bookings.get(tf, 0) + 1
                
            report += "BOOKINGS BY TIME FRAME:\n"
            report += "-" * 30 + "\n"
            for tf, count in sorted(timeframe_bookings.items(), key=lambda x: x[1], reverse=True):
                report += f"  {tf:<15}: {count:>3} bookings\n"
                
            report += "\n"
            
            # Recent bookings
            report += "RECENT BOOKINGS (Last 10):\n"
            report += "-" * 50 + "\n"
            recent_bookings = sorted(self.bookings.values(), 
                                   key=lambda x: x['booking_time'], reverse=True)[:10]
            
            for booking in recent_bookings:
                seat_num = booking['seat'].split('-')[-1]
                report += f"  {booking['user']:<15} | Seat {seat_num:<8} | {booking['date']} {booking['timeframe']}\n"
            
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, report)
        self.notebook.select(4)  # Switch to reports tab
        
    def generate_attendance_report(self):
        """Generate attendance report"""
        if not self.is_admin():
            return
            
        report = "ATTENDANCE REPORT\n"
        report += "=" * 60 + "\n"
        report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        total_records = len(self.attendance)
        report += f"Total Attendance Records: {total_records}\n\n"
        
        if total_records == 0:
            report += "No attendance records found.\n"
        else:
            # Attendance by user
            user_attendance = {}
            total_hours = {}
            
            for att in self.attendance.values():
                user = att['user']
                user_attendance[user] = user_attendance.get(user, 0) + 1
                
                # Calculate hours if both check-in and check-out exist
                if 'check_out' in att and 'duration' in att:
                    try:
                        duration_str = att['duration']
                        hours, minutes, seconds = duration_str.split(':')
                        total_minutes = int(hours) * 60 + int(minutes)
                        total_hours[user] = total_hours.get(user, 0) + total_minutes
                    except:
                        pass
                        
            report += "ATTENDANCE BY USER:\n"
            report += "-" * 40 + "\n"
            for user in sorted(user_attendance.keys()):
                days = user_attendance[user]
                hours = total_hours.get(user, 0) / 60
                report += f"  {user:<15}: {days:>2} days, {hours:>6.1f} hours\n"
                
            report += "\n"
            
            # Recent attendance
            report += "RECENT ATTENDANCE (Last 15 records):\n"
            report += "-" * 70 + "\n"
            recent_attendance = sorted(self.attendance.values(), 
                                     key=lambda x: f"{x['date']} {x['check_in']}", reverse=True)[:15]
            
            report += f"{'User':<12} | {'Date':<12} | {'Check In':<10} | {'Check Out':<10} | {'Duration':<10}\n"
            report += "-" * 70 + "\n"
            
            for att in recent_attendance:
                check_out = att.get('check_out', 'N/A')
                duration = att.get('duration', 'N/A')
                report += f"{att['user']:<12} | {att['date']:<12} | {att['check_in']:<10} | {check_out:<10} | {duration:<10}\n"
            
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, report)
        self.notebook.select(4)  # Switch to reports tab
        
    def generate_utilization_report(self):
        """Generate utilization report"""
        if not self.is_admin():
            return
            
        report = "UTILIZATION REPORT\n"
        report += "=" * 60 + "\n"
        report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Calculate total seats
        total_seats = 0
        workplace_stats = {}
        
        for wp_name, wp_data in self.workplaces.items():
            wp_seats = 0
            for hall_data in wp_data['halls'].values():
                wp_seats += len(hall_data['seats'])
            total_seats += wp_seats
            workplace_stats[wp_name] = {
                'seats': wp_seats,
                'halls': len(wp_data['halls'])
            }
                
        report += f"SYSTEM OVERVIEW:\n"
        report += "-" * 30 + "\n"
        report += f"Total Workplaces: {len(self.workplaces)}\n"
        report += f"Total Halls: {sum(ws['halls'] for ws in workplace_stats.values())}\n"
        report += f"Total Seats: {total_seats}\n"
        report += f"Total Bookings: {len(self.bookings)}\n"
        report += f"Total Time Frames: {len(self.time_frames)}\n\n"
        
        if total_seats > 0:
            # Overall utilization
            max_possible_bookings = total_seats * len(self.time_frames)
            overall_utilization = (len(self.bookings) / max_possible_bookings) * 100 if max_possible_bookings > 0 else 0
            report += f"Overall Utilization: {overall_utilization:.2f}%\n\n"
            
            # Utilization by workplace
            report += "WORKPLACE UTILIZATION:\n"
            report += "-" * 50 + "\n"
            report += f"{'Workplace':<20} | {'Seats':<6} | {'Bookings':<9} | {'Utilization':<12}\n"
            report += "-" * 50 + "\n"
            
            for wp_name, stats in workplace_stats.items():
                wp_bookings = len([b for b in self.bookings.values() if b['workplace'] == wp_name])
                wp_max_bookings = stats['seats'] * len(self.time_frames)
                wp_utilization = (wp_bookings / wp_max_bookings) * 100 if wp_max_bookings > 0 else 0
                
                report += f"{wp_name:<20} | {stats['seats']:<6} | {wp_bookings:<9} | {wp_utilization:<11.2f}%\n"
                
            report += "\n"
            
            # Hall utilization
            report += "HALL UTILIZATION:\n"
            report += "-" * 60 + "\n"
            
            for wp_name, wp_data in self.workplaces.items():
                if wp_data['halls']:
                    report += f"\n{wp_name}:\n"
                    for hall_name, hall_data in wp_data['halls'].items():
                        hall_seats = len(hall_data['seats'])
                        hall_bookings = len([b for b in self.bookings.values() 
                                           if b['workplace'] == wp_name and b['hall'] == hall_name])
                        hall_max_bookings = hall_seats * len(self.time_frames)
                        hall_utilization = (hall_bookings / hall_max_bookings) * 100 if hall_max_bookings > 0 else 0
                        
                        report += f"  {hall_name:<15}: {hall_seats:>3} seats, {hall_bookings:>3} bookings, {hall_utilization:>6.2f}%\n"
                        
        # Most popular time frames
        timeframe_bookings = {}
        for booking in self.bookings.values():
            tf = booking['timeframe']
            timeframe_bookings[tf] = timeframe_bookings.get(tf, 0) + 1
            
        if timeframe_bookings:
            report += "\nPOPULAR TIME FRAMES:\n"
            report += "-" * 30 + "\n"
            for tf, count in sorted(timeframe_bookings.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(self.bookings)) * 100 if self.bookings else 0
                report += f"  {tf:<15}: {count:>3} bookings ({percentage:>5.1f}%)\n"
            
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, report)
        self.notebook.select(4)  # Switch to reports tab
        
    def generate_daily_summary(self):
        """Generate daily summary report"""
        if not self.is_admin():
            return
            
        today = datetime.now().strftime("%Y-%m-%d")
        
        report = "DAILY SUMMARY REPORT\n"
        report += "=" * 60 + "\n"
        report += f"Date: {today}\n"
        report += f"Generated at: {datetime.now().strftime('%H:%M:%S')}\n\n"
        
        # Today's bookings
        today_bookings = [b for b in self.bookings.values() if b['date'] == today]
        report += f"TODAY'S BOOKINGS: {len(today_bookings)}\n"
        report += "-" * 30 + "\n"
        
        if today_bookings:
            # Group by time frame
            timeframe_bookings = {}
            for booking in today_bookings:
                tf = booking['timeframe']
                if tf not in timeframe_bookings:
                    timeframe_bookings[tf] = []
                timeframe_bookings[tf].append(booking)
                
            for tf in sorted(timeframe_bookings.keys()):
                bookings = timeframe_bookings[tf]
                report += f"\n{tf}: {len(bookings)} bookings\n"
                for booking in bookings:
                    seat_num = booking['seat'].split('-')[-1]
                    report += f"  {booking['user']:<15} | {booking['workplace']:<15} | {booking['hall']:<10} | Seat {seat_num}\n"
        else:
            report += "No bookings for today.\n"
            
        # Today's attendance
        today_attendance = [a for a in self.attendance.values() if a['date'] == today]
        report += f"\nTODAY'S ATTENDANCE: {len(today_attendance)}\n"
        report += "-" * 30 + "\n"
        
        if today_attendance:
            checked_in = [a for a in today_attendance if 'check_out' not in a]
            checked_out = [a for a in today_attendance if 'check_out' in a]
            
            report += f"Currently checked in: {len(checked_in)}\n"
            report += f"Completed attendance: {len(checked_out)}\n\n"
            
            if checked_in:
                report += "Currently checked in:\n"
                for att in checked_in:
                    report += f"  {att['user']:<15} | Check-in: {att['check_in']}\n"
                    
            if checked_out:
                report += "\nCompleted attendance:\n"
                for att in checked_out:
                    report += f"  {att['user']:<15} | {att['check_in']} - {att['check_out']} | Duration: {att.get('duration', 'N/A')}\n"
        else:
            report += "No attendance records for today.\n"
            
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, report)
        self.notebook.select(4)  # Switch to reports tab
        
    def is_admin(self):
        """Check if current user is admin"""
        if not self.current_user:
            messagebox.showerror("Error", "Please login first")
            return False
            
        if self.current_user != "admin":
            messagebox.showerror("Error", "Admin access required")
            return False
            
        return True
        
    def run(self):
        """Run the application"""
        self.root.mainloop()

# Create and run the application
if __name__ == "__main__":
    app = WorkplaceManagementSystem()
    app.run()