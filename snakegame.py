import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import random
import time

class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Snake Game")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        self.root.config(bg="#1E1E1E")
        
        # Game variables
        self.width = 500
        self.height = 500
        self.grid_size = 20
        self.speed = 150  # milliseconds between moves (lower = faster)
        self.direction = "Right"
        self.next_direction = "Right"
        self.score = 0
        self.high_score = 0
        self.game_running = False
        self.paused = False
        
        # Snake and food
        self.snake = [(100, 100), (80, 100), (60, 100)]
        self.food_position = self.create_food()
        self.special_food_position = None
        self.special_food_timer = 0
        self.special_food_active = False
        
        # Colors
        self.snake_color = "#4CAF50"  # Green
        self.snake_head_color = "#388E3C"  # Darker green
        self.food_color = "#F44336"  # Red
        self.special_food_color = "#FFC107"  # Yellow/Gold
        self.bg_color = "#212121"  # Dark gray
        self.grid_color = "#2C2C2C"  # Slightly lighter gray
        
        # Create UI elements
        self.create_widgets()
        
        # Bind keys
        self.root.bind("<KeyPress>", self.on_key_press)

        # Bind window resize event
        self.root.bind("<Configure>", self.on_window_resize)
        
        # Start with welcome screen
        self.show_welcome_screen()
    
    def create_widgets(self):
        # Main frame
        self.main_frame = tk.Frame(self.root, bg="#1E1E1E")
        self.main_frame.pack(pady=10)

        # Configure style for combobox
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TCombobox', 
                        fieldbackground='#333333',
                        background='#4CAF50',
                        foreground='#FFFFFF',
                        arrowcolor='#FFFFFF')
        style.map('TCombobox', 
                  fieldbackground=[('readonly', '#333333')],
                  selectbackground=[('readonly', '#4CAF50')],
                  selectforeground=[('readonly', '#FFFFFF')])
        
        # Game canvas
        self.canvas = tk.Canvas(
            self.main_frame, 
            width=self.width, 
            height=self.height, 
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Draw grid lines
        self.draw_grid()
        
        # Control frame
        self.control_frame = tk.Frame(self.root, bg="#1E1E1E")
        self.control_frame.pack(fill="x", padx=20, pady=5)
        
        # Score display
        self.score_frame = tk.Frame(self.control_frame, bg="#1E1E1E")
        self.score_frame.pack(side="left", padx=10)
        
        self.score_label = tk.Label(
            self.score_frame, 
            text="Score: 0", 
            font=("Arial", 14, "bold"),
            fg="#FFFFFF",
            bg="#1E1E1E"
        )
        self.score_label.pack(side="left", padx=5)
        
        self.high_score_label = tk.Label(
            self.score_frame, 
            text="High Score: 0", 
            font=("Arial", 14),
            fg="#AAAAAA",
            bg="#1E1E1E"
        )
        self.high_score_label.pack(side="left", padx=5)
        
        # Speed selection
        self.speed_frame = tk.Frame(self.control_frame, bg="#1E1E1E")
        self.speed_frame.pack(side="right", padx=10)
        
        tk.Label(
            self.speed_frame, 
            text="Speed:", 
            font=("Arial", 12),
            fg="#FFFFFF",
            bg="#1E1E1E"
        ).pack(side="left", padx=5)
        
        self.speed_var = tk.StringVar(value="Medium")
        speed_options = ["Slow", "Medium", "Fast", "Insane"]
        
        self.speed_menu = ttk.Combobox(
            self.speed_frame, 
            textvariable=self.speed_var,
            values=speed_options,
            width=8,
            state="readonly"
        )
        self.speed_menu.pack(side="left", padx=5)
        self.speed_menu.bind("<<ComboboxSelected>>", self.change_speed)
        
        # Button frame
        self.button_frame = tk.Frame(self.root, bg="#1E1E1E")
        self.button_frame.pack(pady=5)
        
        # Start button
        self.start_button = tk.Button(
            self.button_frame,
            text="Start Game",
            command=self.start_game,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            width=12,
            relief="raised",
            borderwidth=3,
            padx=10,
            cursor="hand2"
        )
        self.start_button.pack(side="left", padx=5)
        
        # Pause button
        self.pause_button = tk.Button(
            self.button_frame,
            text="Pause",
            command=self.toggle_pause,
            bg="#2196F3",
            fg="white",
            font=("Arial", 12),
            width=10,
            relief="raised",
            borderwidth=3,
            cursor="hand2",
            state="disabled"
        )
        self.pause_button.pack(side="left", padx=5)
        
        # Reset button
        self.reset_button = tk.Button(
            self.button_frame,
            text="Reset",
            command=self.reset_game,
            bg="#F44336",
            fg="white",
            font=("Arial", 12),
            width=10,
            relief="raised",
            borderwidth=3,
            cursor="hand2"
        )
        self.reset_button.pack(side="left", padx=5)
    
    def draw_grid(self):
        # Draw vertical lines
        for i in range(0, self.width, self.grid_size):
            self.canvas.create_line(i, 0, i, self.height, fill=self.grid_color)
        
        # Draw horizontal lines
        for i in range(0, self.height, self.grid_size):
            self.canvas.create_line(0, i, self.width, i, fill=self.grid_color)
    
    def on_window_resize(self, event):
        # Only respond to root window resize events
        if event.widget == self.root:
            # Get new window dimensions
            window_width = event.width
            window_height = event.height
            
            # Calculate new canvas size (with some margin)
            new_width = max(500, window_width - 100)
            new_height = max(500, window_height - 200)
            
            # Update canvas size
            self.width = new_width
            self.height = new_height
            self.canvas.config(width=new_width, height=new_height)
            
            # Redraw the game
            if self.game_running and not self.paused:
                self.canvas.delete("all")
                self.draw_grid()
                self.draw_snake()
                self.draw_food()
            else:
                self.show_welcome_screen()
    
    def show_welcome_screen(self):
        self.canvas.delete("all")
        self.draw_grid()
        
        # Welcome text
        self.canvas.create_text(
            self.width // 2,
            self.height // 2 - 50,
            text="Welcome to Snake Game!",
            fill="#FFFFFF",
            font=("Arial", 24, "bold")
        )
        
        # Instructions
        instructions = [
            "Use arrow keys to control the snake",
            "Eat food to grow and earn points",
            "Don't hit the walls or yourself!",
            "Yellow food gives bonus points but disappears quickly",
            "Press 'Start Game' to begin"
        ]
        
        y_pos = self.height // 2
        for instruction in instructions:
            self.canvas.create_text(
                self.width // 2,
                y_pos,
                text=instruction,
                fill="#CCCCCC",
                font=("Arial", 14)
            )
            y_pos += 30
    
    def start_game(self):
        if not self.game_running:
            self.game_running = True
            self.paused = False
            self.snake = [(100, 100), (80, 100), (60, 100)]
            self.direction = "Right"
            self.next_direction = "Right"
            self.score = 0
            self.update_score_display()
            self.food_position = self.create_food()
            self.special_food_position = None
            self.special_food_active = False
            self.special_food_timer = 0
            
            self.start_button.config(state="disabled")
            self.pause_button.config(state="normal")
            
            self.update()
    
    def reset_game(self):
        self.game_running = False
        self.paused = False
        self.score = 0
        self.update_score_display()
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="Pause")
        self.show_welcome_screen()
    
    def toggle_pause(self):
        if self.game_running:
            self.paused = not self.paused
            if self.paused:
                self.pause_button.config(text="Resume")
                self.canvas.create_text(
                    self.width // 2,
                    self.height // 2,
                    text="PAUSED",
                    fill="#FFFFFF",
                    font=("Arial", 36, "bold"),
                    tags="pause"
                )
            else:
                self.pause_button.config(text="Pause")
                self.canvas.delete("pause")
                self.update()
    
    def change_speed(self, event=None):
        speed_setting = self.speed_var.get()
        if speed_setting == "Slow":
            self.speed = 200
        elif speed_setting == "Medium":
            self.speed = 150
        elif speed_setting == "Fast":
            self.speed = 100
        elif speed_setting == "Insane":
            self.speed = 50
    
    def create_food(self):
        while True:
            x = random.randint(1, (self.width - self.grid_size) // self.grid_size) * self.grid_size
            y = random.randint(1, (self.height - self.grid_size) // self.grid_size) * self.grid_size
            food_pos = (x, y)
            
            # Make sure food doesn't appear on the snake
            if food_pos not in self.snake:
                return food_pos
    
    def create_special_food(self):
        # 20% chance to create special food when regular food is eaten
        if random.random() < 0.2:
            while True:
                x = random.randint(1, (self.width - self.grid_size) // self.grid_size) * self.grid_size
                y = random.randint(1, (self.height - self.grid_size) // self.grid_size) * self.grid_size
                food_pos = (x, y)
                
                # Make sure special food doesn't appear on the snake or regular food
                if food_pos not in self.snake and food_pos != self.food_position:
                    self.special_food_position = food_pos
                    self.special_food_active = True
                    self.special_food_timer = time.time()
                    break
    
    def on_key_press(self, event):
        key = event.keysym
        
        # Prevent 180-degree turns
        if key == "Up" and self.direction != "Down":
            self.next_direction = "Up"
        elif key == "Down" and self.direction != "Up":
            self.next_direction = "Down"
        elif key == "Left" and self.direction != "Right":
            self.next_direction = "Left"
        elif key == "Right" and self.direction != "Left":
            self.next_direction = "Right"
        elif key == "space":
            self.toggle_pause()
    
    def move_snake(self):
        head_x, head_y = self.snake[0]
        
        # Update direction
        self.direction = self.next_direction
        
        # Calculate new head position
        if self.direction == "Up":
            head_y -= self.grid_size
        elif self.direction == "Down":
            head_y += self.grid_size
        elif self.direction == "Left":
            head_x -= self.grid_size
        elif self.direction == "Right":
            head_x += self.grid_size
        
        new_head = (head_x, head_y)
        
        # Check for collisions
        if (
            head_x < 0 or head_x >= self.width or
            head_y < 0 or head_y >= self.height or
            new_head in self.snake
        ):
            self.game_over()
            return
        
        # Add new head
        self.snake.insert(0, new_head)
        
        # Check if food is eaten
        if new_head == self.food_position:
            self.score += 10
            self.update_score_display()
            self.food_position = self.create_food()
            self.create_special_food()
        elif new_head == self.special_food_position and self.special_food_active:
            self.score += 30
            self.update_score_display()
            self.special_food_position = None
            self.special_food_active = False
        else:
            # Remove tail if no food eaten
            self.snake.pop()
    
    def update_score_display(self):
        self.score_label.config(text=f"Score: {self.score}")
        if self.score > self.high_score:
            self.high_score = self.score
            self.high_score_label.config(text=f"High Score: {self.high_score}")
    
    def game_over(self):
        self.game_running = False
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="Pause")
        
        messagebox.showinfo("Game Over", f"Your score: {self.score}")
        
        if self.score > self.high_score:
            self.high_score = self.score
            self.high_score_label.config(text=f"High Score: {self.high_score}")
    
    def draw_snake(self):
        for i, (x, y) in enumerate(self.snake):
            if i == 0:  # Head
                self.canvas.create_rectangle(
                    x, y, x + self.grid_size, y + self.grid_size,
                    fill=self.snake_head_color, outline=""
                )
            else:  # Body
                self.canvas.create_rectangle(
                    x, y, x + self.grid_size, y + self.grid_size,
                    fill=self.snake_color, outline=""
                )
    
    def draw_food(self):
        x, y = self.food_position
        self.canvas.create_oval(
            x, y, x + self.grid_size, y + self.grid_size,
            fill=self.food_color, outline=""
        )
        
        # Draw special food if active
        if self.special_food_active and self.special_food_position:
            x, y = self.special_food_position
            self.canvas.create_oval(
                x, y, x + self.grid_size, y + self.grid_size,
                fill=self.special_food_color, outline=""
            )
            
            # Check if special food should disappear (after 5 seconds)
            if time.time() - self.special_food_timer > 5:
                self.special_food_active = False
                self.special_food_position = None
    
    def update(self):
        if self.game_running and not self.paused:
            self.canvas.delete("all")
            self.draw_grid()
            self.move_snake()
            self.draw_snake()
            self.draw_food()
            
            # Schedule next update
            self.root.after(self.speed, self.update)

# Create the main window and start the game
if __name__ == "__main__":
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()

# For demonstration purposes, let's print some instructions
print("Snake Game Instructions:")
print("1. Use arrow keys to control the snake")
print("2. Eat red food to grow and earn 10 points")
print("3. Yellow special food appears occasionally and gives 30 points")
print("4. Choose speed level from the dropdown menu")
print("5. Press spacebar to pause/resume the game")
print("\nNote: This game requires a GUI to run properly.")
