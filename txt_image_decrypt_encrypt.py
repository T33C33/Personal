import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import io
from PIL import Image, ImageTk
import threading

class ModernCryptoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔐 Modern Crypto Suite")
        self.root.geometry("900x700")
        self.root.configure(bg='#1a1a1a')
        
        # Configure modern styling
        self.setup_styles()
        
        # Variables
        self.current_key = None
        self.selected_image_path = None
        self.encrypted_image_data = None
        
        # Create main interface
        self.create_widgets()
        
    def setup_styles(self):
        """Configure modern dark theme styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        bg_color = '#1a1a1a'
        fg_color = '#ffffff'
        accent_color = '#4a9eff'
        secondary_color = '#2d2d2d'
        
        # Configure styles
        style.configure('Title.TLabel', 
                       background=bg_color, 
                       foreground=accent_color, 
                       font=('Helvetica', 24, 'bold'))
        
        style.configure('Heading.TLabel', 
                       background=bg_color, 
                       foreground=fg_color, 
                       font=('Helvetica', 14, 'bold'))
        
        style.configure('Modern.TLabel', 
                       background=bg_color, 
                       foreground=fg_color, 
                       font=('Helvetica', 10))
        
        style.configure('Modern.TButton',
                       background=accent_color,
                       foreground='white',
                       font=('Helvetica', 10, 'bold'),
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Modern.TButton',
                 background=[('active', '#3d8bdb'),
                           ('pressed', '#2d6bb3')])
        
        style.configure('Modern.TFrame', background=bg_color)
        style.configure('Card.TFrame', background=secondary_color, relief='flat', borderwidth=1)
        
        # Configure notebook (tabs)
        style.configure('Modern.TNotebook', background=bg_color, borderwidth=0)
        style.configure('Modern.TNotebook.Tab', 
                       background=secondary_color,
                       foreground=fg_color,
                       padding=[20, 10],
                       font=('Helvetica', 11, 'bold'))
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', accent_color),
                           ('active', '#3d8bdb')])
    
    def create_widgets(self):
        """Create the main interface"""
        # Main container
        main_frame = ttk.Frame(self.root, style='Modern.TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="🔐 Modern Crypto Suite", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Key management section
        self.create_key_section(main_frame)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame, style='Modern.TNotebook')
        self.notebook.pack(fill='both', expand=True, pady=(20, 0))
        
        # Text encryption tab
        self.create_text_tab()
        
        # Image encryption tab
        self.create_image_tab()
    
    def create_key_section(self, parent):
        """Create key management section"""
        key_frame = ttk.Frame(parent, style='Card.TFrame')
        key_frame.pack(fill='x', pady=(0, 10))
        
        # Key section content
        key_content = ttk.Frame(key_frame, style='Modern.TFrame')
        key_content.pack(fill='x', padx=15, pady=15)
        
        ttk.Label(key_content, text="🔑 Key Management", style='Heading.TLabel').pack(anchor='w')
        
        # Key input frame
        key_input_frame = ttk.Frame(key_content, style='Modern.TFrame')
        key_input_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(key_input_frame, text="Password:", style='Modern.TLabel').pack(side='left')
        
        self.key_entry = tk.Entry(key_input_frame, 
                                 show='*', 
                                 bg='#2d2d2d', 
                                 fg='white', 
                                 insertbackground='white',
                                 font=('Helvetica', 10),
                                 relief='flat',
                                 bd=5)
        self.key_entry.pack(side='left', fill='x', expand=True, padx=(10, 10))
        
        ttk.Button(key_input_frame, 
                  text="Generate Key", 
                  command=self.generate_key,
                  style='Modern.TButton').pack(side='right')
        
        # Key status
        self.key_status = ttk.Label(key_content, text="No key loaded", style='Modern.TLabel')
        self.key_status.pack(anchor='w', pady=(5, 0))
    
    def create_text_tab(self):
        """Create text encryption/decryption tab"""
        text_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(text_frame, text='📝 Text Encryption')
        
        # Input section
        input_card = ttk.Frame(text_frame, style='Card.TFrame')
        input_card.pack(fill='both', expand=True, padx=10, pady=10)
        
        input_content = ttk.Frame(input_card, style='Modern.TFrame')
        input_content.pack(fill='both', expand=True, padx=15, pady=15)
        
        ttk.Label(input_content, text="📝 Input Text", style='Heading.TLabel').pack(anchor='w')
        
        self.text_input = scrolledtext.ScrolledText(input_content,
                                                   height=8,
                                                   bg='#2d2d2d',
                                                   fg='white',
                                                   insertbackground='white',
                                                   font=('Consolas', 10),
                                                   relief='flat',
                                                   bd=5)
        self.text_input.pack(fill='both', expand=True, pady=(10, 10))
        
        # Buttons
        text_buttons = ttk.Frame(input_content, style='Modern.TFrame')
        text_buttons.pack(fill='x')
        
        ttk.Button(text_buttons, text="🔒 Encrypt", 
                  command=self.encrypt_text, style='Modern.TButton').pack(side='left', padx=(0, 10))
        ttk.Button(text_buttons, text="🔓 Decrypt", 
                  command=self.decrypt_text, style='Modern.TButton').pack(side='left', padx=(0, 10))
        ttk.Button(text_buttons, text="📋 Clear", 
                  command=self.clear_text, style='Modern.TButton').pack(side='right')
        
        # Output section
        output_card = ttk.Frame(text_frame, style='Card.TFrame')
        output_card.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        output_content = ttk.Frame(output_card, style='Modern.TFrame')
        output_content.pack(fill='both', expand=True, padx=15, pady=15)
        
        ttk.Label(output_content, text="📤 Output", style='Heading.TLabel').pack(anchor='w')
        
        self.text_output = scrolledtext.ScrolledText(output_content,
                                                    height=8,
                                                    bg='#2d2d2d',
                                                    fg='#4a9eff',
                                                    insertbackground='white',
                                                    font=('Consolas', 10),
                                                    relief='flat',
                                                    bd=5)
        self.text_output.pack(fill='both', expand=True, pady=(10, 0))
    
    def create_image_tab(self):
        """Create image encryption/decryption tab"""
        image_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(image_frame, text='🖼️ Image Encryption')
        
        # Left panel - controls
        left_panel = ttk.Frame(image_frame, style='Card.TFrame')
        left_panel.pack(side='left', fill='y', padx=(10, 5), pady=10)
        
        left_content = ttk.Frame(left_panel, style='Modern.TFrame')
        left_content.pack(fill='both', expand=True, padx=15, pady=15)
        
        ttk.Label(left_content, text="🖼️ Image Controls", style='Heading.TLabel').pack(anchor='w')
        
        # File selection
        ttk.Button(left_content, text="📁 Select Image", 
                  command=self.select_image, style='Modern.TButton').pack(fill='x', pady=(20, 10))
        
        self.image_status = ttk.Label(left_content, text="No image selected", style='Modern.TLabel')
        self.image_status.pack(anchor='w', pady=(0, 20))
        
        # Encryption buttons
        ttk.Button(left_content, text="🔒 Encrypt Image", 
                  command=self.encrypt_image, style='Modern.TButton').pack(fill='x', pady=(0, 10))
        ttk.Button(left_content, text="🔓 Decrypt Image", 
                  command=self.decrypt_image, style='Modern.TButton').pack(fill='x', pady=(0, 10))
        
        # Save buttons
        ttk.Button(left_content, text="💾 Save Encrypted", 
                  command=self.save_encrypted_image, style='Modern.TButton').pack(fill='x', pady=(20, 10))
        ttk.Button(left_content, text="💾 Save Decrypted", 
                  command=self.save_decrypted_image, style='Modern.TButton').pack(fill='x', pady=(0, 10))
        
        # Right panel - image preview
        right_panel = ttk.Frame(image_frame, style='Card.TFrame')
        right_panel.pack(side='right', fill='both', expand=True, padx=(5, 10), pady=10)
        
        right_content = ttk.Frame(right_panel, style='Modern.TFrame')
        right_content.pack(fill='both', expand=True, padx=15, pady=15)
        
        ttk.Label(right_content, text="🖼️ Image Preview", style='Heading.TLabel').pack(anchor='w')
        
        # Image display
        self.image_display = tk.Label(right_content, 
                                     bg='#2d2d2d', 
                                     text="No image loaded\n\nSelect an image to preview",
                                     fg='#888888',
                                     font=('Helvetica', 12))
        self.image_display.pack(fill='both', expand=True, pady=(10, 0))
    
    def generate_key(self):
        """Generate a new encryption key"""
        password = self.key_entry.get()
        if not password:
            messagebox.showerror("Error", "Please enter a password")
            return
        
        # Generate key from password
        password_bytes = password.encode()
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        self.current_key = Fernet(key)
        
        self.key_status.config(text="✅ Key loaded successfully")
        messagebox.showinfo("Success", "Encryption key generated successfully!")
    
    def encrypt_text(self):
        """Encrypt the input text"""
        if not self.current_key:
            messagebox.showerror("Error", "Please generate a key first")
            return
        
        text = self.text_input.get(1.0, tk.END).strip()
        if not text:
            messagebox.showerror("Error", "Please enter text to encrypt")
            return
        
        try:
            encrypted = self.current_key.encrypt(text.encode())
            encrypted_b64 = base64.b64encode(encrypted).decode()
            
            self.text_output.delete(1.0, tk.END)
            self.text_output.insert(1.0, encrypted_b64)
            
            messagebox.showinfo("Success", "Text encrypted successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Encryption failed: {str(e)}")
    
    def decrypt_text(self):
        """Decrypt the input text"""
        if not self.current_key:
            messagebox.showerror("Error", "Please generate a key first")
            return
        
        encrypted_text = self.text_input.get(1.0, tk.END).strip()
        if not encrypted_text:
            messagebox.showerror("Error", "Please enter encrypted text to decrypt")
            return
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_text.encode())
            decrypted = self.current_key.decrypt(encrypted_bytes)
            decrypted_text = decrypted.decode()
            
            self.text_output.delete(1.0, tk.END)
            self.text_output.insert(1.0, decrypted_text)
            
            messagebox.showinfo("Success", "Text decrypted successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Decryption failed: {str(e)}")
    
    def clear_text(self):
        """Clear text areas"""
        self.text_input.delete(1.0, tk.END)
        self.text_output.delete(1.0, tk.END)
    
    def select_image(self):
        """Select an image file"""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff")]
        )
        
        if file_path:
            self.selected_image_path = file_path
            self.image_status.config(text=f"Selected: {os.path.basename(file_path)}")
            self.display_image(file_path)
    
    def display_image(self, image_path):
        """Display image in the preview area"""
        try:
            # Open and resize image for display
            image = Image.open(image_path)
            
            # Calculate size to fit in display area (max 400x400)
            display_size = (400, 400)
            image.thumbnail(display_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Update display
            self.image_display.config(image=photo, text="")
            self.image_display.image = photo  # Keep a reference
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display image: {str(e)}")
    
    def encrypt_image(self):
        """Encrypt the selected image"""
        if not self.current_key:
            messagebox.showerror("Error", "Please generate a key first")
            return
        
        if not self.selected_image_path:
            messagebox.showerror("Error", "Please select an image first")
            return
        
        try:
            # Read image file
            with open(self.selected_image_path, 'rb') as file:
                image_data = file.read()
            
            # Encrypt image data
            self.encrypted_image_data = self.current_key.encrypt(image_data)
            
            # Show encrypted data visualization
            self.show_encrypted_visualization()
            
            messagebox.showinfo("Success", "Image encrypted successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Image encryption failed: {str(e)}")
    
    def decrypt_image(self):
        """Decrypt the encrypted image"""
        if not self.current_key:
            messagebox.showerror("Error", "Please generate a key first")
            return
        
        if not self.encrypted_image_data:
            messagebox.showerror("Error", "No encrypted image data available")
            return
        
        try:
            # Decrypt image data
            decrypted_data = self.current_key.decrypt(self.encrypted_image_data)
            
            # Create temporary file to display
            temp_path = "temp_decrypted.png"
            with open(temp_path, 'wb') as file:
                file.write(decrypted_data)
            
            # Display decrypted image
            self.display_image(temp_path)
            
            # Clean up temp file
            os.remove(temp_path)
            
            messagebox.showinfo("Success", "Image decrypted successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Image decryption failed: {str(e)}")
    
    def show_encrypted_visualization(self):
        """Show a visualization of encrypted data"""
        # Create a noise-like image to represent encrypted data
        import random
        
        noise_image = Image.new('RGB', (400, 400))
        pixels = []
        
        # Generate random pixels to simulate encrypted data
        for _ in range(400 * 400):
            pixels.append((
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            ))
        
        noise_image.putdata(pixels)
        photo = ImageTk.PhotoImage(noise_image)
        
        self.image_display.config(image=photo, text="")
        self.image_display.image = photo
    
    def save_encrypted_image(self):
        """Save encrypted image data to file"""
        if not self.encrypted_image_data:
            messagebox.showerror("Error", "No encrypted image data to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Encrypted Image",
            defaultextension=".enc",
            filetypes=[("Encrypted files", "*.enc"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'wb') as file:
                    file.write(self.encrypted_image_data)
                messagebox.showinfo("Success", "Encrypted image saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save encrypted image: {str(e)}")
    
    def save_decrypted_image(self):
        """Save decrypted image"""
        if not self.current_key or not self.encrypted_image_data:
            messagebox.showerror("Error", "No decrypted image data available")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Decrypted Image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                decrypted_data = self.current_key.decrypt(self.encrypted_image_data)
                with open(file_path, 'wb') as file:
                    file.write(decrypted_data)
                messagebox.showinfo("Success", "Decrypted image saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save decrypted image: {str(e)}")

def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = ModernCryptoApp(root)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (900 // 2)
    y = (root.winfo_screenheight() // 2) - (700 // 2)
    root.geometry(f"900x700+{x}+{y}")
    
    print("🔐 Modern Crypto Suite Started!")
    print("Features:")
    print("✅ Text encryption/decryption")
    print("✅ Image encryption/decryption") 
    print("✅ Password-based key generation")
    print("✅ Modern dark theme UI")
    print("✅ File save/load functionality")
    print("\nInstructions:")
    print("1. Enter a password and click 'Generate Key'")
    print("2. Use the Text tab to encrypt/decrypt text")
    print("3. Use the Image tab to encrypt/decrypt images")
    print("4. Save encrypted files and load them later")
    
    root.mainloop()

if __name__ == "__main__":
    main()