import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import random
import time

class RockPaperScissorsGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Rock Paper Scissors Deluxe")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#2c3e50")
        
        # Game variables
        self.player_score = 0
        self.computer_score = 0
        self.round_count = 0
        self.max_rounds = 5
        self.game_mode = "classic"  # classic, extended, timed
        self.player_streak = 0
        self.power_up_available = False
        self.game_active = True
        self.time_left = 30  # for timed mode
        self.timer_id = None
        
        # Classic moves
        self.classic_moves = ["rock", "paper", "scissors"]
        
        # Extended moves (including lizard and spock)
        self.extended_moves = ["rock", "paper", "scissors", "lizard", "spock"]
        
        # Current available moves based on game mode
        self.current_moves = self.classic_moves
        
        # Game rules
        self.rules = {
            "rock": {"scissors": "crushes", "lizard": "crushes"},
            "paper": {"rock": "covers", "spock": "disproves"},
            "scissors": {"paper": "cuts", "lizard": "decapitates"},
            "lizard": {"paper": "eats", "spock": "poisons"},
            "spock": {"rock": "vaporizes", "scissors": "smashes"}
        }
        
        self.create_widgets()
        
    def create_widgets(self):
        # Title frame
        title_frame = tk.Frame(self.root, bg="#2c3e50")
        title_frame.pack(pady=10)
        
        title_label = tk.Label(
            title_frame, 
            text="ROCK PAPER SCISSORS DELUXE", 
            font=("Helvetica", 24, "bold"),
            fg="#ecf0f1",
            bg="#2c3e50"
        )
        title_label.pack()
        
        # Mode selection frame
        mode_frame = tk.Frame(self.root, bg="#2c3e50")
        mode_frame.pack(pady=5)
        
        mode_label = tk.Label(
            mode_frame,
            text="Game Mode:",
            font=("Helvetica", 12),
            fg="#ecf0f1",
            bg="#2c3e50"
        )
        mode_label.pack(side=tk.LEFT, padx=5)
        
        self.mode_var = tk.StringVar(value="classic")
        
        classic_radio = ttk.Radiobutton(
            mode_frame,
            text="Classic",
            variable=self.mode_var,
            value="classic",
            command=self.change_game_mode
        )
        classic_radio.pack(side=tk.LEFT, padx=5)
        
        extended_radio = ttk.Radiobutton(
            mode_frame,
            text="Extended (Rock Paper Scissors Lizard Spock)",
            variable=self.mode_var,
            value="extended",
            command=self.change_game_mode
        )
        extended_radio.pack(side=tk.LEFT, padx=5)
        
        timed_radio = ttk.Radiobutton(
            mode_frame,
            text="Timed",
            variable=self.mode_var,
            value="timed",
            command=self.change_game_mode
        )
        timed_radio.pack(side=tk.LEFT, padx=5)
        
        # Score and round frame
        info_frame = tk.Frame(self.root, bg="#2c3e50")
        info_frame.pack(pady=10, fill=tk.X)
        
        # Player score
        player_score_frame = tk.Frame(info_frame, bg="#2c3e50")
        player_score_frame.pack(side=tk.LEFT, expand=True)
        
        player_label = tk.Label(
            player_score_frame,
            text="Player",
            font=("Helvetica", 14, "bold"),
            fg="#3498db",
            bg="#2c3e50"
        )
        player_label.pack()
        
        self.player_score_label = tk.Label(
            player_score_frame,
            text="0",
            font=("Helvetica", 24),
            fg="#ecf0f1",
            bg="#2c3e50"
        )
        self.player_score_label.pack()
        
        # Round info
        round_frame = tk.Frame(info_frame, bg="#2c3e50")
        round_frame.pack(side=tk.LEFT, expand=True)
        
        self.round_label = tk.Label(
            round_frame,
            text="Round: 0/5",
            font=("Helvetica", 14),
            fg="#ecf0f1",
            bg="#2c3e50"
        )
        self.round_label.pack()
        
        self.timer_label = tk.Label(
            round_frame,
            text="",
            font=("Helvetica", 14),
            fg="#e74c3c",
            bg="#2c3e50"
        )
        self.timer_label.pack()
        
        # Computer score
        computer_score_frame = tk.Frame(info_frame, bg="#2c3e50")
        computer_score_frame.pack(side=tk.LEFT, expand=True)
        
        computer_label = tk.Label(
            computer_score_frame,
            text="Computer",
            font=("Helvetica", 14, "bold"),
            fg="#e74c3c",
            bg="#2c3e50"
        )
        computer_label.pack()
        
        self.computer_score_label = tk.Label(
            computer_score_frame,
            text="0",
            font=("Helvetica", 24),
            fg="#ecf0f1",
            bg="#2c3e50"
        )
        self.computer_score_label.pack()
        
        # Game area frame
        game_frame = tk.Frame(self.root, bg="#34495e", padx=20, pady=20)
        game_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Result display
        self.result_label = tk.Label(
            game_frame,
            text="Choose your move!",
            font=("Helvetica", 16, "bold"),
            fg="#ecf0f1",
            bg="#34495e",
            wraplength=700
        )
        self.result_label.pack(pady=10)
        
        # Choices display frame
        choices_frame = tk.Frame(game_frame, bg="#34495e")
        choices_frame.pack(pady=10)
        
        # Player choice
        player_choice_frame = tk.Frame(choices_frame, bg="#34495e")
        player_choice_frame.pack(side=tk.LEFT, padx=20)
        
        player_choice_label = tk.Label(
            player_choice_frame,
            text="Your Choice",
            font=("Helvetica", 12),
            fg="#3498db",
            bg="#34495e"
        )
        player_choice_label.pack()
        
        self.player_choice_display = tk.Label(
            player_choice_frame,
            text="?",
            font=("Helvetica", 48, "bold"),
            width=3,
            height=1,
            fg="#ecf0f1",
            bg="#2c3e50"
        )
        self.player_choice_display.pack(pady=5)
        
        # VS label
        vs_label = tk.Label(
            choices_frame,
            text="VS",
            font=("Helvetica", 24, "bold"),
            fg="#f39c12",
            bg="#34495e"
        )
        vs_label.pack(side=tk.LEFT, padx=20)
        
        # Computer choice
        computer_choice_frame = tk.Frame(choices_frame, bg="#34495e")
        computer_choice_frame.pack(side=tk.LEFT, padx=20)
        
        computer_choice_label = tk.Label(
            computer_choice_frame,
            text="Computer's Choice",
            font=("Helvetica", 12),
            fg="#e74c3c",
            bg="#34495e"
        )
        computer_choice_label.pack()
        
        self.computer_choice_display = tk.Label(
            computer_choice_frame,
            text="?",
            font=("Helvetica", 48, "bold"),
            width=3,
            height=1,
            fg="#ecf0f1",
            bg="#2c3e50"
        )
        self.computer_choice_display.pack(pady=5)
        
        # Buttons frame
        buttons_frame = tk.Frame(game_frame, bg="#34495e")
        buttons_frame.pack(pady=20)
        
        # Create move buttons
        self.move_buttons = {}
        
        for move in self.extended_moves:
            btn = tk.Button(
                buttons_frame,
                text=move.capitalize(),
                font=("Helvetica", 12, "bold"),
                width=10,
                bg="#3498db",
                fg="#ffffff",
                activebackground="#2980b9",
                activeforeground="#ffffff",
                relief=tk.RAISED,
                bd=3,
                command=lambda m=move: self.play_move(m)
            )
            self.move_buttons[move] = btn
            if move in self.classic_moves:
                btn.pack(side=tk.LEFT, padx=5)
            else:
                btn.pack_forget()
        
        # Power-up button
        self.power_up_button = tk.Button(
            game_frame,
            text="Use Power-Up",
            font=("Helvetica", 12, "bold"),
            bg="#e74c3c",
            fg="#ffffff",
            activebackground="#c0392b",
            activeforeground="#ffffff",
            state=tk.DISABLED,
            command=self.use_power_up
        )
        self.power_up_button.pack(pady=10)
        
        # Control buttons frame
        control_frame = tk.Frame(self.root, bg="#2c3e50", pady=10)
        control_frame.pack(fill=tk.X)
        
        # Restart button
        restart_button = tk.Button(
            control_frame,
            text="Restart Game",
            font=("Helvetica", 12, "bold"),
            bg="#e67e22",
            fg="#ffffff",
            activebackground="#d35400",
            activeforeground="#ffffff",
            command=self.restart_game
        )
        restart_button.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Help button
        help_button = tk.Button(
            control_frame,
            text="Game Rules",
            font=("Helvetica", 12, "bold"),
            bg="#27ae60",
            fg="#ffffff",
            activebackground="#2ecc71",
            activeforeground="#ffffff",
            command=self.show_rules
        )
        help_button.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Set initial game state
        self.update_display()
    
    def change_game_mode(self):
        # Reset the game when changing modes
        self.restart_game()
        
        # Update game mode
        self.game_mode = self.mode_var.get()
        
        # Update available moves based on game mode
        if self.game_mode == "extended":
            self.current_moves = self.extended_moves
            for move in self.extended_moves:
                self.move_buttons[move].pack(side=tk.LEFT, padx=5)
        else:
            self.current_moves = self.classic_moves
            for move in self.extended_moves:
                if move in self.classic_moves:
                    self.move_buttons[move].pack(side=tk.LEFT, padx=5)
                else:
                    self.move_buttons[move].pack_forget()
        
        # Set up timer for timed mode
        if self.game_mode == "timed":
            self.time_left = 30
            self.timer_label.config(text=f"Time: {self.time_left}s")
            self.start_timer()
        else:
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
                self.timer_id = None
            self.timer_label.config(text="")
    
    def start_timer(self):
        if self.game_mode == "timed" and self.game_active:
            self.timer_label.config(text=f"Time: {self.time_left}s")
            if self.time_left > 0:
                self.time_left -= 1
                self.timer_id = self.root.after(1000, self.start_timer)
            else:
                self.end_game("Time's up! Game over.")
    
    def play_move(self, player_move):
        if not self.game_active:
            return
        
        # Increment round count
        self.round_count += 1
        
        # Get computer's move
        computer_move = random.choice(self.current_moves)
        
        # Display choices
        self.player_choice_display.config(text=player_move[0].upper())
        
        # Simulate computer "thinking"
        self.result_label.config(text="Computer is choosing...")
        self.root.update()
        time.sleep(0.5)
        
        self.computer_choice_display.config(text=computer_move[0].upper())
        
        # Determine winner
        result = self.determine_winner(player_move, computer_move)
        
        # Update scores and display
        if result == "win":
            self.player_score += 1
            self.player_streak += 1
            result_text = f"You win! {player_move.capitalize()} {self.rules[player_move][computer_move]} {computer_move}."
            
            # Check for power-up availability
            if self.player_streak >= 3 and not self.power_up_available:
                self.power_up_available = True
                self.power_up_button.config(state=tk.NORMAL)
                result_text += "\nPower-Up available! Use it to guarantee a win."
        
        elif result == "lose":
            self.computer_score += 1
            self.player_streak = 0
            result_text = f"You lose! {computer_move.capitalize()} {self.rules[computer_move][player_move]} {player_move}."
        
        else:  # Tie
            result_text = f"It's a tie! Both chose {player_move}."
        
        self.result_label.config(text=result_text)
        self.update_display()
        
        # Check if game should end
        if self.game_mode != "timed" and self.round_count >= self.max_rounds:
            self.end_game()
    
    def determine_winner(self, player_move, computer_move):
        if player_move == computer_move:
            return "tie"
        
        if computer_move in self.rules.get(player_move, {}):
            return "win"
        else:
            return "lose"
    
    def use_power_up(self):
        if not self.power_up_available or not self.game_active:
            return
        
        # Get computer's move first
        computer_move = random.choice(self.current_moves)
        
        # Find a move that beats the computer's move
        winning_move = None
        for move in self.current_moves:
            if computer_move in self.rules.get(move, {}):
                winning_move = move
                break
        
        if winning_move:
            # Automatically play the winning move
            self.power_up_available = False
            self.power_up_button.config(state=tk.DISABLED)
            self.player_streak = 0
            
            # Display special message
            self.result_label.config(text="Using Power-Up! Guaranteed win incoming...")
            self.root.update()
            time.sleep(1)
            
            # Play the winning move
            self.round_count += 1
            self.player_score += 1
            
            # Display choices
            self.player_choice_display.config(text=winning_move[0].upper())
            self.computer_choice_display.config(text=computer_move[0].upper())
            
            result_text = f"Power-Up Success! {winning_move.capitalize()} {self.rules[winning_move][computer_move]} {computer_move}."
            self.result_label.config(text=result_text)
            
            self.update_display()
            
            # Check if game should end
            if self.game_mode != "timed" and self.round_count >= self.max_rounds:
                self.end_game()
    
    def update_display(self):
        # Update score labels
        self.player_score_label.config(text=str(self.player_score))
        self.computer_score_label.config(text=str(self.computer_score))
        
        # Update round label
        if self.game_mode != "timed":
            self.round_label.config(text=f"Round: {self.round_count}/{self.max_rounds}")
        else:
            self.round_label.config(text=f"Round: {self.round_count}")
    
    def end_game(self, custom_message=None):
        self.game_active = False
        
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        
        # Determine winner
        if custom_message:
            result_message = custom_message
        elif self.player_score > self.computer_score:
            result_message = f"Game Over! You win with a score of {self.player_score}-{self.computer_score}!"
        elif self.player_score < self.computer_score:
            result_message = f"Game Over! Computer wins with a score of {self.computer_score}-{self.player_score}!"
        else:
            result_message = f"Game Over! It's a tie with a score of {self.player_score}-{self.computer_score}!"
        
        # Show game over message
        messagebox.showinfo("Game Over", result_message)
        
        # Ask if player wants to play again
        play_again = messagebox.askyesno("Play Again?", "Would you like to play again?")
        if play_again:
            self.restart_game()
    
    def restart_game(self):
        # Reset game variables
        self.player_score = 0
        self.computer_score = 0
        self.round_count = 0
        self.player_streak = 0
        self.power_up_available = False
        self.game_active = True
        
        # Reset display
        self.player_choice_display.config(text="?")
        self.computer_choice_display.config(text="?")
        self.result_label.config(text="Choose your move!")
        self.power_up_button.config(state=tk.DISABLED)
        
        # Reset timer for timed mode
        if self.game_mode == "timed":
            self.time_left = 30
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
            self.start_timer()
        
        self.update_display()
    
    def show_rules(self):
        # Create rules text based on game mode
        if self.game_mode == "extended":
            rules_text = """
Rock Paper Scissors Lizard Spock Rules:

- Rock crushes Scissors and Lizard
- Paper covers Rock and disproves Spock
- Scissors cuts Paper and decapitates Lizard
- Lizard eats Paper and poisons Spock
- Spock vaporizes Rock and smashes Scissors

Game Features:
- Win 3 times in a row to earn a Power-Up
- Power-Up guarantees a win on your next move
- First to win the most rounds out of 5 wins the game
            """
        else:
            rules_text = """
Rock Paper Scissors Rules:

- Rock crushes Scissors
- Paper covers Rock
- Scissors cuts Paper

Game Features:
- Win 3 times in a row to earn a Power-Up
- Power-Up guarantees a win on your next move
- First to win the most rounds out of 5 wins the game
            """
        
        if self.game_mode == "timed":
            rules_text += "\n- In Timed Mode, score as many points as possible in 30 seconds!"
        
        messagebox.showinfo("Game Rules", rules_text)

if __name__ == "__main__":
    root = tk.Tk()
    game = RockPaperScissorsGame(root)
    root.mainloop()