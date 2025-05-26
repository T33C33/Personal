import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import math
import time
import datetime
import threading
import os
import platform

# Determine which sound module to use based on platform
SYSTEM = platform.system()
if SYSTEM == "Windows":
    import winsound
    def play_sound():
        winsound.Beep(1000, 1000)  # Frequency: 1000Hz, Duration: 1000ms
        
elif SYSTEM == "Darwin":  # macOS
    import os
    def play_sound():
        os.system("afplay /System/Library/Sounds/Ping.aiff")
        
else:  # Linux and other systems
    import os
    def play_sound():
        os.system("aplay /usr/share/sounds/sound-icons/glass.wav 2>/dev/null || echo '\a'")
        # Fallback to terminal bell if sound file not available

class AnalogClock:
    def __init__(self, root):
        self.root = root
        self.root.title("Analog Clock with Alarm")
        self.root.geometry("800x650")  # Wider window
        self.root.resizable(True, True)  # Allow resizing
        
        # Theme variables
        self.is_dark_mode = False
        self.light_theme = {
            "bg_color": "#f0f0f0",
            "clock_face_color": "white",
            "hour_hand_color": "black",
            "minute_hand_color": "black",
            "second_hand_color": "red",
            "marker_color": "black",
            "text_color": "black",
            "frame_bg": "#f0f0f0",
            "button_bg": "#e0e0e0",
            "button_fg": "black",
            "entry_bg": "white",
            "entry_fg": "black"
        }
        self.dark_theme = {
            "bg_color": "#2d2d2d",
            "clock_face_color": "#3d3d3d",
            "hour_hand_color": "white",
            "minute_hand_color": "white",
            "second_hand_color": "#ff6b6b",
            "marker_color": "white",
            "text_color": "white",
            "frame_bg": "#2d2d2d",
            "button_bg": "#444444",
            "button_fg": "white",
            "entry_bg": "#444444",
            "entry_fg": "white"
        }
        self.theme = self.light_theme  # Start with light theme
        
        # Clock size
        self.clock_size = 400
        self.center = self.clock_size // 2
        
        # Animation settings
        self.animation_enabled = True
        self.update_interval = 50  # milliseconds (for smooth animation)
        self.last_second = -1
        self.last_time = time.time()
        
        # Alarm variables
        self.alarms = []
        self.alarm_active = False
        self.alarm_thread = None
        
        # Create main container
        self.main_container = tk.Frame(root, bg=self.theme["bg_color"])
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create left and right frames for better layout
        self.left_frame = tk.Frame(self.main_container, bg=self.theme["bg_color"])
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=11)
        
        self.right_frame = tk.Frame(self.main_container, bg=self.theme["bg_color"])
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        # Create frames in left frame
        self.clock_frame = tk.Frame(self.left_frame, bg=self.theme["bg_color"])
        self.clock_frame.pack(pady=10)
        
        self.digital_frame = tk.Frame(self.left_frame, bg=self.theme["bg_color"])
        self.digital_frame.pack(pady=5)
        
        self.settings_frame = tk.Frame(self.left_frame, bg=self.theme["bg_color"])
        self.settings_frame.pack(pady=5)
        
        # Create canvas for analog clock
        self.canvas = tk.Canvas(
            self.clock_frame, 
            width=self.clock_size, 
            height=self.clock_size, 
            bg=self.theme["bg_color"], 
            highlightthickness=0
        )
        self.canvas.pack()
        
        # Create digital display
        self.digital_time = tk.Label(
            self.digital_frame, 
            font=("Arial", 24, "bold"), 
            bg=self.theme["bg_color"],
            fg=self.theme["text_color"]
        )
        self.digital_time.pack()
        
        self.digital_date = tk.Label(
            self.digital_frame, 
            font=("Arial", 16), 
            bg=self.theme["bg_color"],
            fg=self.theme["text_color"]
        )
        self.digital_date.pack()
        
        # Create settings in settings frame
        self.settings_label = tk.Label(
            self.settings_frame, 
            text="Settings", 
            font=("Arial", 14, "bold"),
            bg=self.theme["bg_color"],
            fg=self.theme["text_color"]
        )
        self.settings_label.pack(anchor="w", pady=(10, 5))
        
        # Create animation toggle
        self.animation_var = tk.BooleanVar(value=self.animation_enabled)
        self.animation_check = tk.Checkbutton(
            self.settings_frame, 
            text="Smooth Animation", 
            variable=self.animation_var,
            command=self.toggle_animation,
            bg=self.theme["bg_color"],
            fg=self.theme["text_color"],
            selectcolor=self.theme["button_bg"],
            activebackground=self.theme["bg_color"],
            activeforeground=self.theme["text_color"]
        )
        self.animation_check.pack(anchor="w")
        
        # Create theme toggle
        self.theme_button = tk.Button(
            self.settings_frame,
            text="Toggle Dark Mode",
            command=self.toggle_theme,
            bg=self.theme["button_bg"],
            fg=self.theme["button_fg"],
            activebackground=self.theme["button_bg"],
            activeforeground=self.theme["button_fg"]
        )
        self.theme_button.pack(anchor="w", pady=5)
        
        # Create alarm section in right frame
        self.alarm_frame = tk.Frame(self.right_frame, bg=self.theme["bg_color"])
        self.alarm_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.create_alarm_section()
        
        # Draw static clock face
        self.clock_face_image = self.draw_clock_face()
        
        # Start the clock
        self.update_clock()
    
    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.theme = self.dark_theme if self.is_dark_mode else self.light_theme
        
        # Update all UI elements with new theme
        self.update_ui_theme()
        
        # Redraw clock face with new theme
        self.clock_face_image = self.draw_clock_face()
    
    def update_ui_theme(self):
        # Update main container
        self.main_container.config(bg=self.theme["bg_color"])
        
        # Update frames
        for frame in [self.left_frame, self.right_frame, self.clock_frame, 
                      self.digital_frame, self.settings_frame, self.alarm_frame]:
            frame.config(bg=self.theme["bg_color"])
        
        # Update canvas
        self.canvas.config(bg=self.theme["bg_color"])
        
        # Update labels
        self.digital_time.config(bg=self.theme["bg_color"], fg=self.theme["text_color"])
        self.digital_date.config(bg=self.theme["bg_color"], fg=self.theme["text_color"])
        self.settings_label.config(bg=self.theme["bg_color"], fg=self.theme["text_color"])
        
        # Update checkbutton
        self.animation_check.config(
            bg=self.theme["bg_color"], 
            fg=self.theme["text_color"],
            selectcolor=self.theme["button_bg"],
            activebackground=self.theme["bg_color"],
            activeforeground=self.theme["text_color"]
        )
        
        # Update button
        self.theme_button.config(
            bg=self.theme["button_bg"],
            fg=self.theme["button_fg"],
            activebackground=self.theme["button_bg"],
            activeforeground=self.theme["button_fg"]
        )
        
        # Update alarm section
        self.alarm_title.config(bg=self.theme["bg_color"], fg=self.theme["text_color"])
        self.alarms_list_title.config(bg=self.theme["bg_color"], fg=self.theme["text_color"])
        
        # Update alarm input frame
        for widget in self.input_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(bg=self.theme["bg_color"], fg=self.theme["text_color"])
            elif isinstance(widget, tk.Button):
                widget.config(
                    bg=self.theme["button_bg"],
                    fg=self.theme["button_fg"],
                    activebackground=self.theme["button_bg"],
                    activeforeground=self.theme["button_fg"]
                )
            elif isinstance(widget, tk.Entry):
                widget.config(
                    bg=self.theme["entry_bg"],
                    fg=self.theme["entry_fg"],
                    insertbackground=self.theme["text_color"]
                )
        
        # Update alarms container
        self.alarms_container.config(bg=self.theme["bg_color"])
        
        # Update all alarm frames
        self.update_alarms_display()
    
    def toggle_animation(self):
        self.animation_enabled = self.animation_var.get()
        # Reset update interval based on animation setting
        self.update_interval = 50 if self.animation_enabled else 1000
    
    def create_alarm_section(self):
        # Alarm section title
        self.alarm_title = tk.Label(
            self.alarm_frame, 
            text="Alarm Settings", 
            font=("Arial", 14, "bold"), 
            bg=self.theme["bg_color"],
            fg=self.theme["text_color"]
        )
        self.alarm_title.pack(anchor="w", pady=(10, 5))
        
        # Alarm input frame
        self.input_frame = tk.Frame(self.alarm_frame, bg=self.theme["bg_color"])
        self.input_frame.pack(fill=tk.X, pady=5)
        
        # Hour input
        hour_label = tk.Label(
            self.input_frame, 
            text="Hour:", 
            bg=self.theme["bg_color"],
            fg=self.theme["text_color"]
        )
        hour_label.grid(row=0, column=0, padx=5)
        
        self.hour_var = tk.StringVar()
        self.hour_spinbox = ttk.Spinbox(self.input_frame, from_=0, to=23, width=5, textvariable=self.hour_var)
        self.hour_spinbox.grid(row=0, column=1, padx=5)
        
        # Minute input
        minute_label = tk.Label(
            self.input_frame, 
            text="Minute:", 
            bg=self.theme["bg_color"],
            fg=self.theme["text_color"]
        )
        minute_label.grid(row=0, column=2, padx=5)
        
        self.minute_var = tk.StringVar()
        self.minute_spinbox = ttk.Spinbox(self.input_frame, from_=0, to=59, width=5, textvariable=self.minute_var)
        self.minute_spinbox.grid(row=0, column=3, padx=5)
        
        # Label input
        label_text = tk.Label(
            self.input_frame, 
            text="Label:", 
            bg=self.theme["bg_color"],
            fg=self.theme["text_color"]
        )
        label_text.grid(row=0, column=4, padx=5)
        
        self.alarm_label_var = tk.StringVar()
        self.alarm_label_entry = tk.Entry(
            self.input_frame, 
            textvariable=self.alarm_label_var, 
            width=15,
            bg=self.theme["entry_bg"],
            fg=self.theme["entry_fg"],
            insertbackground=self.theme["text_color"]
        )
        self.alarm_label_entry.grid(row=0, column=5, padx=5)
        
        # Add alarm button
        add_button = tk.Button(
            self.input_frame, 
            text="Add Alarm", 
            command=self.add_alarm,
            bg=self.theme["button_bg"],
            fg=self.theme["button_fg"],
            activebackground=self.theme["button_bg"],
            activeforeground=self.theme["button_fg"]
        )
        add_button.grid(row=0, column=6, padx=10)
        
        # Alarms list frame
        self.alarms_list_frame = tk.Frame(self.alarm_frame, bg=self.theme["bg_color"])
        self.alarms_list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Alarms list title
        self.alarms_list_title = tk.Label(
            self.alarms_list_frame, 
            text="Active Alarms:", 
            font=("Arial", 12, "bold"), 
            bg=self.theme["bg_color"],
            fg=self.theme["text_color"]
        )
        self.alarms_list_title.pack(anchor="w")
        
        # Alarms container
        self.alarms_container = tk.Frame(self.alarms_list_frame, bg=self.theme["bg_color"])
        self.alarms_container.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def add_alarm(self):
        try:
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                messagebox.showerror("Invalid Input", "Please enter valid hour (0-23) and minute (0-59) values.")
                return
            
            label = self.alarm_label_var.get() or f"Alarm {len(self.alarms) + 1}"
            
            # Create alarm dict
            alarm = {
                "hour": hour,
                "minute": minute,
                "label": label,
                "active": True
            }
            
            self.alarms.append(alarm)
            self.update_alarms_display()
            
            # Clear inputs
            self.hour_var.set("")
            self.minute_var.set("")
            self.alarm_label_var.set("")
            
            messagebox.showinfo("Alarm Added", f"Alarm set for {hour:02d}:{minute:02d}")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values for hour and minute.")
    
    def update_alarms_display(self):
        # Clear existing alarms display
        for widget in self.alarms_container.winfo_children():
            widget.destroy()
        
        if not self.alarms:
            no_alarms_label = tk.Label(
                self.alarms_container, 
                text="No alarms set", 
                bg=self.theme["bg_color"], 
                fg=self.theme["text_color"]
            )
            no_alarms_label.pack(pady=5)
            return
        
        # Add each alarm to the display
        for i, alarm in enumerate(self.alarms):
            alarm_frame = tk.Frame(
                self.alarms_container, 
                bg=self.theme["bg_color"], 
                bd=1, 
                relief=tk.SOLID
            )
            alarm_frame.pack(fill=tk.X, pady=2)
            
            # Alarm time and label
            time_str = f"{alarm['hour']:02d}:{alarm['minute']:02d}"
            alarm_text = f"{time_str} - {alarm['label']}"
            
            alarm_label = tk.Label(
                alarm_frame, 
                text=alarm_text, 
                bg=self.theme["bg_color"], 
                fg=self.theme["text_color"],
                padx=5, 
                pady=5
            )
            alarm_label.pack(side=tk.LEFT)
            
            # Delete button
            delete_button = tk.Button(
                alarm_frame, 
                text="Delete", 
                command=lambda idx=i: self.delete_alarm(idx),
                bg=self.theme["button_bg"],
                fg=self.theme["button_fg"],
                activebackground=self.theme["button_bg"],
                activeforeground=self.theme["button_fg"]
            )
            delete_button.pack(side=tk.RIGHT, padx=5, pady=5)
            
            # Toggle button
            toggle_text = "Disable" if alarm["active"] else "Enable"
            toggle_button = tk.Button(
                alarm_frame, 
                text=toggle_text, 
                command=lambda idx=i: self.toggle_alarm(idx),
                bg=self.theme["button_bg"],
                fg=self.theme["button_fg"],
                activebackground=self.theme["button_bg"],
                activeforeground=self.theme["button_fg"]
            )
            toggle_button.pack(side=tk.RIGHT, padx=5, pady=5)
    
    def delete_alarm(self, index):
        if 0 <= index < len(self.alarms):
            del self.alarms[index]
            self.update_alarms_display()
    
    def toggle_alarm(self, index):
        if 0 <= index < len(self.alarms):
            self.alarms[index]["active"] = not self.alarms[index]["active"]
            self.update_alarms_display()
    
    def check_alarms(self, current_time):
        if self.alarm_active:
            return
        
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        for alarm in self.alarms:
            if (alarm["active"] and 
                alarm["hour"] == current_hour and 
                alarm["minute"] == current_minute and 
                current_time.second < 10):  # Only trigger in the first 10 seconds of a minute
                
                self.trigger_alarm(alarm)
                break
    
    def trigger_alarm(self, alarm):
        self.alarm_active = True
        
        # Create and start alarm thread
        self.alarm_thread = threading.Thread(target=self.play_alarm, args=(alarm,))
        self.alarm_thread.daemon = True
        self.alarm_thread.start()
    
    def play_alarm(self, alarm):
        try:
            # Play sound in a loop
            sound_thread = threading.Thread(target=self.sound_loop)
            sound_thread.daemon = True
            sound_thread.start()
            
            # Show alarm notification
            result = messagebox.showinfo(
                "Alarm!", 
                f"Time: {alarm['hour']:02d}:{alarm['minute']:02d}\n{alarm['label']}", 
                type=messagebox.OK
            )
            
            # Stop alarm
            self.alarm_active = False
            
        except Exception as e:
            print(f"Error playing alarm: {e}")
            self.alarm_active = False
    
    def sound_loop(self):
        # Play sound repeatedly until alarm is dismissed
        while self.alarm_active:
            play_sound()
            time.sleep(1)  # Wait a second between beeps
    
    def draw_clock_face(self):
        # Create a new image for the clock face
        image = Image.new("RGB", (self.clock_size, self.clock_size), self.theme["bg_color"])
        draw = ImageDraw.Draw(image)
        
        # Draw the outer circle
        draw.ellipse(
            [(5, 5), (self.clock_size - 5, self.clock_size - 5)],
            outline=self.theme["marker_color"],
            fill=self.theme["clock_face_color"],
            width=2
        )
        
        # Draw hour markers
        for i in range(12):
            angle = math.radians(i * 30)
            outer_x = self.center + 0.8 * self.center * math.sin(angle)
            outer_y = self.center - 0.8 * self.center * math.cos(angle)
            inner_x = self.center + 0.7 * self.center * math.sin(angle)
            inner_y = self.center - 0.7 * self.center * math.cos(angle)
            draw.line([(outer_x, outer_y), (inner_x, inner_y)], fill=self.theme["marker_color"], width=3)
            
            # Draw hour numbers
            text_x = self.center + 0.9 * self.center * math.sin(angle) - 10
            text_y = self.center - 0.9 * self.center * math.cos(angle) - 10
            hour_num = i if i != 0 else 12
            draw.text((text_x, text_y), str(hour_num), fill=self.theme["text_color"])
        
        # Draw minute markers
        for i in range(60):
            if i % 5 != 0:  # Skip hour markers
                angle = math.radians(i * 6)
                outer_x = self.center + 0.8 * self.center * math.sin(angle)
                outer_y = self.center - 0.8 * self.center * math.cos(angle)
                inner_x = self.center + 0.75 * self.center * math.sin(angle)
                inner_y = self.center - 0.75 * self.center * math.cos(angle)
                draw.line([(outer_x, outer_y), (inner_x, inner_y)], fill=self.theme["marker_color"], width=1)
        
        return image
    
    def draw_clock_hands(self, hour, minute, second, microsecond=0):
        # Create a copy of the clock face
        image = self.clock_face_image.copy()
        draw = ImageDraw.Draw(image)
        
        # Calculate precise time for smooth animation
        precise_second = second + (microsecond / 1000000)
        precise_minute = minute + (precise_second / 60)
        precise_hour = (hour % 12) + (precise_minute / 60)
        
        # Calculate angles
        hour_angle = math.radians(precise_hour * 30)
        minute_angle = math.radians(precise_minute * 6)
        second_angle = math.radians(precise_second * 6)
        
        # Draw hour hand
        hour_length = 0.5 * self.center
        hour_x = self.center + hour_length * math.sin(hour_angle)
        hour_y = self.center - hour_length * math.cos(hour_angle)
        draw.line([(self.center, self.center), (hour_x, hour_y)], fill=self.theme["hour_hand_color"], width=6)
        
        # Draw minute hand
        minute_length = 0.7 * self.center
        minute_x = self.center + minute_length * math.sin(minute_angle)
        minute_y = self.center - minute_length * math.cos(minute_angle)
        draw.line([(self.center, self.center), (minute_x, minute_y)], fill=self.theme["minute_hand_color"], width=4)
        
        # Draw second hand
        second_length = 0.8 * self.center
        second_x = self.center + second_length * math.sin(second_angle)
        second_y = self.center - second_length * math.cos(second_angle)
        draw.line([(self.center, self.center), (second_x, second_y)], fill=self.theme["second_hand_color"], width=2)
        
        # Draw center circle
        draw.ellipse(
            [(self.center - 8, self.center - 8), (self.center + 8, self.center + 8)],
            outline=self.theme["marker_color"],
            fill=self.theme["marker_color"]
        )
        
        return image
    
    def update_clock(self):
        # Get current time with microsecond precision
        current_time = datetime.datetime.now()
        hour, minute, second = current_time.hour, current_time.minute, current_time.second
        microsecond = current_time.microsecond
        
        # Check for alarms (only once per second)
        if second != self.last_second:
            self.check_alarms(current_time)
            self.last_second = second
        
        # Draw hands with smooth animation if enabled
        if self.animation_enabled:
            clock_image = self.draw_clock_hands(hour, minute, second, microsecond)
        else:
            clock_image = self.draw_clock_hands(hour, minute, second)
        
        # Convert to PhotoImage and display
        self.tk_image = ImageTk.PhotoImage(clock_image)
        self.canvas.delete("all")  # Clear previous image
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        
        # Update digital time display (only once per second to avoid flickering)
        if second != self.last_second or not self.animation_enabled:
            time_str = current_time.strftime("%H:%M:%S")
            self.digital_time.config(text=time_str)
            
            # Update digital date display
            date_str = current_time.strftime("%A, %B %d, %Y")
            self.digital_date.config(text=date_str)
        
        # Schedule the next update
        self.root.after(self.update_interval, self.update_clock)

if __name__ == "__main__":
    # Create the main window
    root = tk.Tk()
    app = AnalogClock(root)
    root.mainloop()