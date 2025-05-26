import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import subprocess
import json
import sys
from urllib.request import urlopen, Request
from io import BytesIO
from PIL import Image, ImageTk
import re
import time

def install_requirements():
    """Install required packages if not available"""
    packages = ['yt-dlp', 'pillow']
    for package in packages:
        try:
            if package == 'yt-dlp':
                import yt_dlp
            elif package == 'pillow':
                import PIL
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install requirements on startup
install_requirements()

import yt_dlp

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Downloader (yt-dlp)")
        self.root.geometry("900x650")
        
        # Theme variables
        self.is_dark_mode = tk.BooleanVar(value=False)
        
        # Define color schemes
        self.colors = {
            "light": {
                "bg": "#f5f5f5",
                "fg": "#333333",
                "accent": "#ff0000",  # YouTube red
                "button": "#ff0000",
                "button_fg": "white",
                "entry_bg": "white",
                "hover": "#cc0000",
                "progress": "#ff0000",
                "card_bg": "white",
                "border": "#dddddd"
            },
            "dark": {
                "bg": "#121212",
                "fg": "#f5f5f5",
                "accent": "#ff0000",  # YouTube red
                "button": "#ff0000",
                "button_fg": "white",
                "entry_bg": "#2a2a2a",
                "hover": "#cc0000",
                "progress": "#ff0000",
                "card_bg": "#1e1e1e",
                "border": "#333333"
            }
        }
        
        # Configure ttk styles
        self.style = ttk.Style()
        self.create_styles()
        
        # Create main container
        self.main_container = tk.Frame(root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create widgets
        self.create_widgets()
        
        # Apply initial theme
        self.apply_theme()
        
        # Store video information
        self.video_info = None
        self.formats = []
        self.fetching = False
        
        # Store all widgets for theme updates
        self.all_widgets = []
        self.collect_widgets(self.root, self.all_widgets)
        
    def collect_widgets(self, parent, widget_list):
        """Recursively collect all widgets from a parent widget"""
        for widget in parent.winfo_children():
            widget_list.append(widget)
            self.collect_widgets(widget, widget_list)
        
    def create_styles(self):
        # Create custom styles for ttk widgets
        self.style.configure("TFrame", background=self.colors["light"]["bg"])
        self.style.configure("TLabel", background=self.colors["light"]["bg"], foreground=self.colors["light"]["fg"])
        self.style.configure("TButton", background=self.colors["light"]["button"], foreground=self.colors["light"]["button_fg"])
        self.style.configure("Accent.TButton", background=self.colors["light"]["accent"], foreground="white")
        self.style.configure("TEntry", fieldbackground=self.colors["light"]["entry_bg"])
        self.style.configure("TCombobox", fieldbackground=self.colors["light"]["entry_bg"])
        self.style.configure("Horizontal.TProgressbar", background=self.colors["light"]["progress"])
        
        # Configure the combobox dropdown style
        self.style.map('TCombobox', fieldbackground=[('readonly', self.colors["light"]["entry_bg"])])
        self.style.map('TCombobox', selectbackground=[('readonly', self.colors["light"]["accent"])])
        self.style.map('TCombobox', selectforeground=[('readonly', 'white')])
        
    def create_widgets(self):
        # Header frame with title and theme toggle
        header_frame = tk.Frame(self.main_container)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # App title
        title_label = tk.Label(
            header_frame, 
            text="YouTube Video Downloader (yt-dlp)", 
            font=("Arial", 22, "bold"),
        )
        title_label.pack(side=tk.LEFT, pady=10)
        
        # Dark mode toggle
        theme_frame = tk.Frame(header_frame)
        theme_frame.pack(side=tk.RIGHT, pady=10)
        
        theme_label = tk.Label(theme_frame, text="Dark Mode:")
        theme_label.pack(side=tk.LEFT, padx=(0, 5))
        
        theme_switch = tk.Checkbutton(
            theme_frame, 
            variable=self.is_dark_mode,
            command=self.toggle_theme,
            width=2, height=1
        )
        theme_switch.pack(side=tk.LEFT)
        
        # Main content frame
        content_frame = tk.Frame(self.main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # URL input card
        url_card = tk.Frame(content_frame)
        url_card.pack(fill=tk.X, pady=10)
        
        url_label = tk.Label(url_card, text="Enter YouTube URL:", font=("Arial", 12))
        url_label.pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        url_input_frame = tk.Frame(url_card)
        url_input_frame.pack(fill=tk.X, padx=15, pady=(0, 5))
        
        self.url_entry = tk.Entry(url_input_frame, font=("Arial", 12))
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.fetch_button = tk.Button(
            url_input_frame, 
            text="Fetch Video", 
            font=("Arial", 11, "bold"),
            command=self.fetch_video,
            cursor="hand2"
        )
        self.fetch_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Debug button
        self.debug_button = tk.Button(
            url_input_frame,
            text="Debug Info",
            font=("Arial", 11),
            command=self.show_debug_info,
            cursor="hand2"
        )
        self.debug_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Video info frame
        self.info_frame = tk.Frame(content_frame)
        self.info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Left side - Thumbnail
        self.thumbnail_frame = tk.Frame(self.info_frame, width=320, height=180)
        self.thumbnail_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Placeholder for thumbnail
        self.thumbnail_placeholder = tk.Label(
            self.thumbnail_frame, 
            text="Thumbnail will appear here",
            width=40, height=10
        )
        self.thumbnail_placeholder.pack(fill=tk.BOTH, expand=True)
        
        # Right side - Video details
        details_frame = tk.Frame(self.info_frame)
        details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Video title
        self.title_var = tk.StringVar()
        self.title_label = tk.Label(
            details_frame, 
            textvariable=self.title_var,
            wraplength=400,
            font=("Arial", 14, "bold"),
            anchor=tk.W,
            justify=tk.LEFT
        )
        self.title_label.pack(anchor=tk.W, pady=5, fill=tk.X)
        
        # Video details frame
        video_details_frame = tk.Frame(details_frame)
        video_details_frame.pack(fill=tk.X, pady=5, anchor=tk.W)
        
        # Video duration
        self.duration_var = tk.StringVar()
        duration_label = tk.Label(
            video_details_frame, 
            textvariable=self.duration_var,
            font=("Arial", 11)
        )
        duration_label.pack(anchor=tk.W, pady=2)
        
        # Video author
        self.author_var = tk.StringVar()
        author_label = tk.Label(
            video_details_frame, 
            textvariable=self.author_var,
            font=("Arial", 11)
        )
        author_label.pack(anchor=tk.W, pady=2)
        
        # Video views
        self.views_var = tk.StringVar()
        views_label = tk.Label(
            video_details_frame, 
            textvariable=self.views_var,
            font=("Arial", 11)
        )
        views_label.pack(anchor=tk.W, pady=2)
        
        # Quality selection
        quality_frame = tk.Frame(details_frame)
        quality_frame.pack(fill=tk.X, pady=10)
        
        quality_label = tk.Label(quality_frame, text="Select Quality:", font=("Arial", 12))
        quality_label.pack(anchor=tk.W)
        
        self.quality_combobox = ttk.Combobox(
            quality_frame, 
            state="readonly", 
            font=("Arial", 11),
            width=50
        )
        self.quality_combobox.pack(fill=tk.X, pady=5)
        
        # Download options frame
        options_frame = tk.Frame(details_frame)
        options_frame.pack(fill=tk.X, pady=10)
        
        # Audio only option
        self.audio_only_var = tk.BooleanVar(value=False)
        audio_only_check = tk.Checkbutton(
            options_frame,
            text="Audio Only (MP3)",
            variable=self.audio_only_var,
            font=("Arial", 11),
            command=self.toggle_audio_only
        )
        audio_only_check.pack(anchor=tk.W)
        
        # Download location
        location_frame = tk.Frame(details_frame)
        location_frame.pack(fill=tk.X, pady=10)
        
        location_label = tk.Label(location_frame, text="Download Location:", font=("Arial", 12))
        location_label.pack(anchor=tk.W)
        
        location_select_frame = tk.Frame(location_frame)
        location_select_frame.pack(fill=tk.X, pady=5)
        
        self.location_var = tk.StringVar()
        self.location_var.set(os.path.expanduser("~/Downloads"))
        
        location_entry = tk.Entry(
            location_select_frame, 
            textvariable=self.location_var, 
            font=("Arial", 11),
            width=50
        )
        location_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_button = tk.Button(
            location_select_frame, 
            text="Browse", 
            font=("Arial", 11),
            command=self.browse_location,
            cursor="hand2"
        )
        browse_button.pack(side=tk.RIGHT, padx=5)
        
        # Download button
        self.download_button = tk.Button(
            details_frame, 
            text="Download Video", 
            font=("Arial", 12, "bold"),
            command=self.download_video,
            state=tk.DISABLED,
            cursor="hand2"
        )
        self.download_button.pack(pady=10)
        
        # Progress frame
        progress_frame = tk.Frame(content_frame)
        progress_frame.pack(fill=tk.X, pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            orient=tk.HORIZONTAL, 
            length=100, 
            mode='determinate', 
            variable=self.progress_var
        )
        self.progress_bar.pack(fill=tk.X, padx=15, pady=(5, 0))
        
        # Status frame
        status_frame = tk.Frame(progress_frame)
        status_frame.pack(fill=tk.X, padx=15, pady=(5, 15))
        
        # Status label
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to download videos")
        self.status_label = tk.Label(
            status_frame, 
            textvariable=self.status_var,
            font=("Arial", 11),
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X)
        
        # Loading indicator (spinner)
        self.loading_var = tk.StringVar()
        self.loading_label = tk.Label(
            status_frame,
            textvariable=self.loading_var,
            font=("Arial", 11, "bold")
        )
        self.loading_label.pack(side=tk.RIGHT)
        
    def show_debug_info(self):
        """Show debug information to help diagnose issues"""
        try:
            # Get yt-dlp version
            result = subprocess.run([sys.executable, "-m", "yt_dlp", "--version"], 
                                  capture_output=True, text=True)
            ytdlp_version = result.stdout.strip() if result.returncode == 0 else "Not installed"
            
            debug_info = f"""
yt-dlp Version: {ytdlp_version}
Python Version: {sys.version}

Current Working Directory: {os.getcwd()}

yt-dlp Module Path: {yt_dlp.__file__ if 'yt_dlp' in globals() else 'Not found'}

To fix common issues:
1. Try updating yt-dlp: pip install --upgrade yt-dlp
2. Check your internet connection
3. Try a different YouTube URL
4. Make sure the video is not region-restricted

yt-dlp is much more reliable than pytube and actively maintained.
            """
            
            messagebox.showinfo("Debug Information", debug_info)
        except Exception as e:
            messagebox.showerror("Error", f"Could not get debug information: {str(e)}")
        
    def toggle_audio_only(self):
        """Handle toggling between audio-only and video modes"""
        if self.audio_only_var.get():
            # Update UI for audio-only mode
            self.download_button.config(text="Download Audio")
            self.update_format_options()
        else:
            # Update UI for video mode
            self.download_button.config(text="Download Video")
            self.update_format_options()
            
    def update_format_options(self):
        """Update the quality options based on audio/video selection"""
        if not self.video_info:
            return
            
        try:
            # Clear current options
            self.quality_combobox['values'] = []
            
            if self.audio_only_var.get():
                # Filter for audio formats
                audio_formats = [f for f in self.formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
                audio_formats.sort(key=lambda x: float(x.get('abr', 0)), reverse=True)
                
                # Create quality options for audio
                quality_options = []
                self.current_formats = []
                
                for fmt in audio_formats:
                    abr = fmt.get('abr', 'Unknown')
                    ext = fmt.get('ext', 'unknown')
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                    
                    quality_text = f"Audio: {abr}kbps - {ext.upper()} - {self._format_size(filesize)}"
                    quality_options.append(quality_text)
                    self.current_formats.append(fmt)
            else:
                # Filter for video formats with both video and audio
                video_formats = [f for f in self.formats if f.get('vcodec') != 'none' and f.get('height')]
                video_formats.sort(key=lambda x: int(x.get('height', 0)), reverse=True)
                
                # Create quality options for video
                quality_options = []
                self.current_formats = []
                
                for fmt in video_formats:
                    height = fmt.get('height', 'Unknown')
                    fps = fmt.get('fps', 'Unknown')
                    ext = fmt.get('ext', 'unknown')
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                    vcodec = fmt.get('vcodec', 'unknown')
                    
                    quality_text = f"{height}p - {fps}fps - {ext.upper()} ({vcodec}) - {self._format_size(filesize)}"
                    quality_options.append(quality_text)
                    self.current_formats.append(fmt)
            
            self.quality_combobox['values'] = quality_options
            if quality_options:
                self.quality_combobox.current(0)
                
        except Exception as e:
            print(f"Error updating format options: {e}")
            
    def toggle_theme(self):
        self.apply_theme()
        
    def apply_theme(self):
        # Update the widget list to ensure we have all widgets
        self.all_widgets = []
        self.collect_widgets(self.root, self.all_widgets)
        
        theme = "dark" if self.is_dark_mode.get() else "light"
        colors = self.colors[theme]
        
        # Update ttk styles
        self.style.configure("TFrame", background=colors["bg"])
        self.style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
        self.style.configure("TButton", background=colors["button"], foreground=colors["button_fg"])
        self.style.configure("Accent.TButton", background=colors["accent"], foreground="white")
        self.style.configure("TEntry", fieldbackground=colors["entry_bg"])
        self.style.configure("TCombobox", fieldbackground=colors["entry_bg"])
        self.style.configure("Horizontal.TProgressbar", background=colors["progress"])
        
        # Update tk widgets
        self.root.configure(bg=colors["bg"])
        self.main_container.configure(bg=colors["bg"])
        
        # Update all widgets using our collected list
        for widget in self.all_widgets:
            widget_type = widget.winfo_class()
            if widget_type == 'Frame':
                widget.configure(bg=colors["bg"])
            elif widget_type == 'Label':
                widget.configure(bg=colors["bg"], fg=colors["fg"])
            elif widget_type == 'Button':
                widget.configure(
                    bg=colors["button"], 
                    fg=colors["button_fg"],
                    activebackground=colors["hover"],
                    activeforeground=colors["button_fg"]
                )
            elif widget_type == 'Entry':
                widget.configure(
                    bg=colors["entry_bg"], 
                    fg=colors["fg"],
                    insertbackground=colors["fg"]
                )
            elif widget_type == 'Checkbutton':
                widget.configure(
                    bg=colors["bg"], 
                    fg=colors["fg"],
                    activebackground=colors["bg"],
                    activeforeground=colors["fg"],
                    selectcolor=colors["entry_bg"]
                )
        
        # Special handling for download button
        if self.download_button['state'] == tk.DISABLED:
            self.download_button.configure(bg=colors["border"], fg=colors["fg"])
        else:
            self.download_button.configure(bg=colors["accent"], fg=colors["button_fg"])
        
        # Update thumbnail placeholder
        self.thumbnail_placeholder.configure(bg=colors["entry_bg"], fg=colors["fg"])
        
    def browse_location(self):
        directory = filedialog.askdirectory(initialdir=self.location_var.get())
        if directory:
            self.location_var.set(directory)
    
    def fetch_video(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
            
        # Prevent multiple fetch operations
        if self.fetching:
            return
            
        self.fetching = True
        self.status_var.set("Fetching video information...")
        self.progress_var.set(0)
        self.fetch_button.configure(state=tk.DISABLED)
        
        # Start loading animation
        self.start_loading_animation()
        
        # Use threading to prevent UI freezing
        threading.Thread(target=self._fetch_video_thread, args=(url,), daemon=True).start()
    
    def start_loading_animation(self):
        self.loading_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.loading_index = 0
        self._update_loading_animation()
    
    def _update_loading_animation(self):
        if self.fetching:
            self.loading_var.set(self.loading_frames[self.loading_index] + " Loading...")
            self.loading_index = (self.loading_index + 1) % len(self.loading_frames)
            self.root.after(100, self._update_loading_animation)
        else:
            self.loading_var.set("")
    
    def _fetch_video_thread(self, url):
        try:
            # Configure yt-dlp options for fetching info
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extractaudio': False,
                'format': 'best',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video information
                self.video_info = ydl.extract_info(url, download=False)
                self.formats = self.video_info.get('formats', [])
                
                # Update UI with video information
                self.root.after(0, self._update_video_info)
                
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.status_var.set(f"Error: {error_msg}"))
            self.root.after(0, lambda: messagebox.showerror(
                "Error", 
                f"Failed to fetch video information:\n\n{error_msg}\n\n"
                "This could be due to:\n"
                "1. Invalid or private video URL\n"
                "2. Network connectivity issues\n"
                "3. Region restrictions\n\n"
                "Please check the URL and try again."
            ))
            self.root.after(0, lambda: self.fetch_button.configure(state=tk.NORMAL))
            self.root.after(0, lambda: setattr(self, 'fetching', False))
    
    def _update_video_info(self):
        if not self.video_info:
            self.fetching = False
            self.fetch_button.configure(state=tk.NORMAL)
            return
        
        try:
            # Set video details
            title = self.video_info.get('title', 'Unknown Title')
            duration = self.video_info.get('duration', 0)
            uploader = self.video_info.get('uploader', 'Unknown Channel')
            view_count = self.video_info.get('view_count', 0)
            
            self.title_var.set(title)
            self.duration_var.set(f"Duration: {self._format_duration(duration)}")
            self.author_var.set(f"Channel: {uploader}")
            self.views_var.set(f"Views: {self._format_views(view_count)}")
            
            # Load thumbnail
            try:
                thumbnail_url = self.video_info.get('thumbnail')
                if thumbnail_url:
                    # Use custom headers to avoid 403 errors
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    req = Request(thumbnail_url, headers=headers)
                    
                    with urlopen(req) as u:
                        raw_data = u.read()
                    
                    image = Image.open(BytesIO(raw_data))
                    # Use LANCZOS if available, otherwise fall back to ANTIALIAS
                    resize_method = Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS
                    image = image.resize((320, 180), resize_method)
                    photo = ImageTk.PhotoImage(image)
                    
                    # Clear previous thumbnail
                    for widget in self.thumbnail_frame.winfo_children():
                        widget.destroy()
                    
                    # Display thumbnail
                    thumbnail_label = tk.Label(self.thumbnail_frame, image=photo)
                    thumbnail_label.image = photo  # Keep a reference
                    thumbnail_label.pack()
                
            except Exception as e:
                print(f"Error loading thumbnail: {e}")
                # Create a colored placeholder instead
                theme = "dark" if self.is_dark_mode.get() else "light"
                placeholder = tk.Label(
                    self.thumbnail_frame, 
                    text="Thumbnail Unavailable",
                    width=40, height=10,
                    bg=self.colors[theme]["entry_bg"],
                    fg=self.colors[theme]["fg"]
                )
                placeholder.pack(fill=tk.BOTH, expand=True)
            
            # Update format options based on current mode
            self.update_format_options()
            
            self.download_button.configure(state=tk.NORMAL)
                
            # Update download button color
            theme = "dark" if self.is_dark_mode.get() else "light"
            self.download_button.configure(
                bg=self.colors[theme]["accent"], 
                fg=self.colors[theme]["button_fg"]
            )
            
            self.status_var.set("Video information fetched successfully")
            
        except Exception as e:
            self.status_var.set(f"Error updating video info: {str(e)}")
            messagebox.showerror("Error", f"Error updating video info: {str(e)}")
        
        finally:
            self.fetching = False
            self.fetch_button.configure(state=tk.NORMAL)
    
    def download_video(self):
        if not self.video_info or not hasattr(self, 'current_formats'):
            messagebox.showerror("Error", "No video information available")
            return
        
        selected_index = self.quality_combobox.current()
        if selected_index < 0 or selected_index >= len(self.current_formats):
            messagebox.showerror("Error", "Please select a quality option")
            return
        
        selected_format = self.current_formats[selected_index]
        download_path = self.location_var.get()
        
        if not os.path.exists(download_path):
            messagebox.showerror("Error", "Download location does not exist")
            return
        
        self.progress_var.set(0)
        self.status_var.set("Starting download...")
        self.download_button.configure(state=tk.DISABLED)
        
        # Update download button color for disabled state
        theme = "dark" if self.is_dark_mode.get() else "light"
        self.download_button.configure(bg=self.colors[theme]["border"], fg=self.colors[theme]["fg"])
        
        # Use threading to prevent UI freezing
        threading.Thread(target=self._download_thread, args=(selected_format, download_path), daemon=True).start()
    
    def _download_thread(self, selected_format, download_path):
        try:
            # Configure progress hook
            def progress_hook(d):
                if d['status'] == 'downloading':
                    # Extract progress information
                    percent_str = d.get('_percent_str', '0%').replace('%', '')
                    try:
                        percent = float(percent_str)
                        self.root.after(0, lambda: self.progress_var.set(percent))
                        
                        # Update status with download info
                        speed = d.get('_speed_str', 'Unknown speed')
                        eta = d.get('_eta_str', 'Unknown ETA')
                        self.root.after(0, lambda: self.status_var.set(
                            f"Downloading: {percent:.1f}% - {speed} - ETA: {eta}"
                        ))
                    except (ValueError, TypeError):
                        pass
                        
                elif d['status'] == 'finished':
                    self.root.after(0, lambda: self.progress_var.set(100))
                    self.root.after(0, lambda: self.status_var.set("Download completed!"))
            
            # Configure yt-dlp options
            if self.audio_only_var.get():
                ydl_opts = {
                    'format': str(selected_format['format_id']),
                    'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [progress_hook],
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
            else:
                ydl_opts = {
                    'format': str(selected_format['format_id']),
                    'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [progress_hook],
                }
            
            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.video_info['webpage_url']])
            
            # Get the filename that was downloaded
            title = self.video_info.get('title', 'video')
            # Clean the title for filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            
            if self.audio_only_var.get():
                filename = f"{safe_title}.mp3"
            else:
                ext = selected_format.get('ext', 'mp4')
                filename = f"{safe_title}.{ext}"
            
            # Re-enable download button with proper styling
            theme = "dark" if self.is_dark_mode.get() else "light"
            self.root.after(0, lambda: self.download_button.configure(
                state=tk.NORMAL,
                bg=self.colors[theme]["accent"],
                fg=self.colors[theme]["button_fg"]
            ))
            
            self.root.after(0, lambda: messagebox.showinfo(
                "Success", 
                f"Download completed successfully!\n\nFile: {filename}\nLocation: {download_path}"
            ))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.status_var.set(f"Download failed: {error_msg}"))
            
            # Re-enable download button with proper styling
            theme = "dark" if self.is_dark_mode.get() else "light"
            self.root.after(0, lambda: self.download_button.configure(
                state=tk.NORMAL,
                bg=self.colors[theme]["accent"],
                fg=self.colors[theme]["button_fg"]
            ))
            
            self.root.after(0, lambda: messagebox.showerror("Download Error", f"Download failed:\n\n{error_msg}"))
    
    def _format_duration(self, seconds):
        """Convert seconds to human-readable format"""
        if not seconds:
            return "Unknown"
            
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    def _format_views(self, views):
        """Convert view count to human-readable format"""
        if not views:
            return "Unknown"
            
        if views >= 1_000_000:
            return f"{views / 1_000_000:.1f}M"
        elif views >= 1_000:
            return f"{views / 1_000:.1f}K"
        else:
            return str(views)
    
    def _format_size(self, bytes_size):
        """Convert bytes to human-readable format"""
        if not bytes_size:
            return "Unknown size"
            
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TB"

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()