import tkinter as tk
from tkinter import ttk, messagebox, font
import requests
import json
from datetime import datetime, timedelta
import time
import threading
import os
from PIL import Image, ImageTk
import io
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
import math  # Added missing math import
import random
matplotlib.use("TkAgg")

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather Dashboard")
        self.root.geometry("1200x700")
        self.root.minsize(800, 600)
        
        # API Key
        self.api_key = "290b9713fcca9656f3a75ebb43e6a2dc"
        
        # Default location
        self.default_country = "Nigeria"
        self.default_city = "Bauchi"
        
        # Dark mode state
        self.dark_mode = tk.BooleanVar(value=True)
        
        # Saved locations
        self.saved_locations = [
            {"country": "Nigeria", "city": "Bauchi"},
            {"country": "Nigeria", "city": "Lagos"},
            {"country": "Nigeria", "city": "Abuja"},
            {"country": "United States", "city": "New York"},
            {"country": "United Kingdom", "city": "London"},
        ]
        
        # Temperature unit (metric by default)
        self.temp_unit = tk.StringVar(value="metric")
        
        # Load custom font
        self.custom_font = font.Font(family="Helvetica", size=10)
        self.header_font = font.Font(family="Helvetica", size=14, weight="bold")
        self.title_font = font.Font(family="Helvetica", size=18, weight="bold")
        
        # Create UI
        self.create_ui()
        
        # Apply initial theme
        self.apply_theme()
        
        # Start with default location
        self.get_weather(self.default_country, self.default_city)
        
        # Start background update thread
        self.update_thread = threading.Thread(target=self.background_update, daemon=True)
        self.update_thread.start()
    
    def create_ui(self):
        # Main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top bar with controls
        self.top_bar = ttk.Frame(self.main_frame)
        self.top_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Dark mode toggle
        self.dark_mode_check = ttk.Checkbutton(
            self.top_bar, 
            text="Dark Mode", 
            variable=self.dark_mode,
            command=self.apply_theme
        )
        self.dark_mode_check.pack(side=tk.RIGHT, padx=5)
        
        # Temperature unit selector
        self.unit_frame = ttk.Frame(self.top_bar)
        self.unit_frame.pack(side=tk.RIGHT, padx=10)
        
        ttk.Label(self.unit_frame, text="Units:").pack(side=tk.LEFT)
        ttk.Radiobutton(
            self.unit_frame, 
            text="°C", 
            variable=self.temp_unit, 
            value="metric",
            command=lambda: self.refresh_weather()
        ).pack(side=tk.LEFT)
        
        ttk.Radiobutton(
            self.unit_frame, 
            text="°F", 
            variable=self.temp_unit, 
            value="imperial",
            command=lambda: self.refresh_weather()
        ).pack(side=tk.LEFT)
        
        # Left sidebar for location selection
        self.sidebar = ttk.Frame(self.main_frame, width=250)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Location selection
        ttk.Label(
            self.sidebar, 
            text="Select Location", 
            font=self.header_font
        ).pack(fill=tk.X, pady=(0, 10))
        
        # Country entry
        ttk.Label(self.sidebar, text="Country:").pack(anchor=tk.W)
        self.country_var = tk.StringVar(value=self.default_country)
        self.country_entry = ttk.Entry(self.sidebar, textvariable=self.country_var)
        self.country_entry.pack(fill=tk.X, pady=(0, 10))
        
        # City entry
        ttk.Label(self.sidebar, text="City:").pack(anchor=tk.W)
        self.city_var = tk.StringVar(value=self.default_city)
        self.city_entry = ttk.Entry(self.sidebar, textvariable=self.city_var)
        self.city_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Search button
        self.search_btn = ttk.Button(
            self.sidebar, 
            text="Search", 
            command=lambda: self.get_weather(self.country_var.get(), self.city_var.get())
        )
        self.search_btn.pack(fill=tk.X, pady=(0, 20))
        
        # Saved locations
        ttk.Label(
            self.sidebar, 
            text="Saved Locations", 
            font=self.header_font
        ).pack(fill=tk.X, pady=(0, 10))
        
        # Listbox for saved locations
        self.locations_listbox = tk.Listbox(self.sidebar, height=10)
        self.locations_listbox.pack(fill=tk.X, pady=(0, 10))
        
        # Populate saved locations
        for location in self.saved_locations:
            self.locations_listbox.insert(tk.END, f"{location['city']}, {location['country']}")
        
        # Bind selection event
        self.locations_listbox.bind('<<ListboxSelect>>', self.on_location_select)
        
        # Add/Remove location buttons
        self.loc_buttons_frame = ttk.Frame(self.sidebar)
        self.loc_buttons_frame.pack(fill=tk.X)
        
        self.add_loc_btn = ttk.Button(
            self.loc_buttons_frame, 
            text="Add Current", 
            command=self.add_current_location
        )
        self.add_loc_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.remove_loc_btn = ttk.Button(
            self.loc_buttons_frame, 
            text="Remove", 
            command=self.remove_selected_location
        )
        self.remove_loc_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Main content area with notebook tabs
        self.content = ttk.Frame(self.main_frame)
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Notebook for different views
        self.notebook = ttk.Notebook(self.content)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Current weather tab
        self.current_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.current_tab, text="Current Weather")
        
        # Forecast tab
        self.forecast_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.forecast_tab, text="Forecast")
        
        # Historical tab
        self.historical_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.historical_tab, text="Historical Data")
        
        # Maps tab
        self.maps_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.maps_tab, text="Weather Maps")
        
        # Alerts tab
        self.alerts_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.alerts_tab, text="Alerts")
        
        # Setup current weather tab
        self.setup_current_tab()
        
        # Setup forecast tab
        self.setup_forecast_tab()
        
        # Setup historical tab
        self.setup_historical_tab()
        
        # Setup maps tab
        self.setup_maps_tab()
        
        # Setup alerts tab
        self.setup_alerts_tab()
        
        # Status bar
        self.status_bar = ttk.Label(
            self.root, 
            text="Ready", 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_current_tab(self):
        # Current weather display
        self.current_frame = ttk.Frame(self.current_tab, padding=20)
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        # Location and time header
        self.location_label = ttk.Label(
            self.current_frame, 
            text="Loading...", 
            font=self.title_font
        )
        self.location_label.pack(pady=(0, 5))
        
        self.time_label = ttk.Label(
            self.current_frame, 
            text="", 
            font=self.custom_font
        )
        self.time_label.pack(pady=(0, 20))
        
        # Current conditions frame
        self.conditions_frame = ttk.Frame(self.current_frame)
        self.conditions_frame.pack(fill=tk.X, pady=10)
        
        # Weather icon placeholder
        self.icon_label = ttk.Label(self.conditions_frame)
        self.icon_label.pack(side=tk.LEFT, padx=20)
        
        # Temperature and conditions
        self.temp_frame = ttk.Frame(self.conditions_frame)
        self.temp_frame.pack(side=tk.LEFT, padx=20)
        
        self.temp_label = ttk.Label(
            self.temp_frame, 
            text="--°C", 
            font=self.title_font
        )
        self.temp_label.pack()
        
        self.condition_label = ttk.Label(
            self.temp_frame, 
            text="--", 
            font=self.custom_font
        )
        self.condition_label.pack()
        
        # Details frame
        self.details_frame = ttk.LabelFrame(
            self.current_frame, 
            text="Weather Details", 
            padding=10
        )
        self.details_frame.pack(fill=tk.X, pady=20)
        
        # Create a grid for details
        self.details_grid = ttk.Frame(self.details_frame)
        self.details_grid.pack(fill=tk.X)
        
        # Row 1
        ttk.Label(self.details_grid, text="Feels Like:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.feels_like_label = ttk.Label(self.details_grid, text="--")
        self.feels_like_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(self.details_grid, text="Humidity:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.humidity_label = ttk.Label(self.details_grid, text="--")
        self.humidity_label.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Row 2
        ttk.Label(self.details_grid, text="Wind:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.wind_label = ttk.Label(self.details_grid, text="--")
        self.wind_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(self.details_grid, text="Pressure:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.pressure_label = ttk.Label(self.details_grid, text="--")
        self.pressure_label.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Row 3
        ttk.Label(self.details_grid, text="Visibility:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.visibility_label = ttk.Label(self.details_grid, text="--")
        self.visibility_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(self.details_grid, text="Sunrise:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        self.sunrise_label = ttk.Label(self.details_grid, text="--")
        self.sunrise_label.grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Row 4
        ttk.Label(self.details_grid, text="UV Index:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.uv_label = ttk.Label(self.details_grid, text="--")
        self.uv_label.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(self.details_grid, text="Sunset:").grid(row=3, column=2, sticky=tk.W, padx=5, pady=5)
        self.sunset_label = ttk.Label(self.details_grid, text="--")
        self.sunset_label.grid(row=3, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Last updated
        self.last_updated_label = ttk.Label(
            self.current_frame, 
            text="Last updated: Never", 
            font=self.custom_font
        )
        self.last_updated_label.pack(pady=10)
        
        # Refresh button
        self.refresh_btn = ttk.Button(
            self.current_frame, 
            text="Refresh", 
            command=self.refresh_weather
        )
        self.refresh_btn.pack(pady=10)
    
    def setup_forecast_tab(self):
        # Forecast display
        self.forecast_frame = ttk.Frame(self.forecast_tab, padding=20)
        self.forecast_frame.pack(fill=tk.BOTH, expand=True)
        
        # Forecast header
        ttk.Label(
            self.forecast_frame, 
            text="5-Day Weather Forecast", 
            font=self.title_font
        ).pack(pady=(0, 20))
        
        # Forecast container
        self.forecast_container = ttk.Frame(self.forecast_frame)
        self.forecast_container.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder for forecast data
        for i in range(5):
            frame = ttk.LabelFrame(
                self.forecast_container, 
                text=f"Day {i+1}"
            )
            frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            
            # Date
            ttk.Label(frame, text="--").pack(pady=2)
            
            # Icon placeholder
            ttk.Label(frame, text="[Icon]").pack(pady=2)
            
            # Temp
            ttk.Label(frame, text="--°C").pack(pady=2)
            
            # Condition
            ttk.Label(frame, text="--").pack(pady=2)
        
        # Make columns expandable
        for i in range(5):
            self.forecast_container.columnconfigure(i, weight=1)
    
    def setup_historical_tab(self):
        # Historical data display
        self.historical_frame = ttk.Frame(self.historical_tab, padding=20)
        self.historical_frame.pack(fill=tk.BOTH, expand=True)
        
        # Historical header
        ttk.Label(
            self.historical_frame, 
            text="Historical Weather Data", 
            font=self.title_font
        ).pack(pady=(0, 10))
        
        # Date range selection
        self.date_frame = ttk.Frame(self.historical_frame)
        self.date_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(self.date_frame, text="Select Period:").pack(side=tk.LEFT, padx=5)
        
        self.period_var = tk.StringVar(value="7days")
        periods = [
            ("Last 7 Days", "7days"),
            ("Last 30 Days", "30days"),
            ("Last 90 Days", "90days")
        ]
        
        for text, value in periods:
            ttk.Radiobutton(
                self.date_frame, 
                text=text, 
                variable=self.period_var, 
                value=value,
                command=self.update_historical_data
            ).pack(side=tk.LEFT, padx=5)
        
        # Graph frame
        self.graph_frame = ttk.Frame(self.historical_frame)
        self.graph_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create figure for matplotlib
        self.fig = plt.Figure(figsize=(10, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initial plot
        self.ax.set_title("Temperature History")
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Temperature (°C)")
        self.ax.grid(True)
        self.canvas.draw()
        
        # Note about simulated data
        ttk.Label(
            self.historical_frame,
            text="Note: Historical data is simulated for demonstration purposes.",
            font=self.custom_font,
            foreground="#666666"
        ).pack(pady=10)
    
    def setup_maps_tab(self):
        # Weather maps display
        self.maps_frame = ttk.Frame(self.maps_tab, padding=20)
        self.maps_frame.pack(fill=tk.BOTH, expand=True)
        
        # Maps header
        ttk.Label(
            self.maps_frame, 
            text="Weather Maps", 
            font=self.title_font
        ).pack(pady=(0, 10))
        
        # Map type selection
        self.map_type_frame = ttk.Frame(self.maps_frame)
        self.map_type_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(self.map_type_frame, text="Map Type:").pack(side=tk.LEFT, padx=5)
        
        self.map_type_var = tk.StringVar(value="temp")
        map_types = [
            ("Temperature", "temp"),
            ("Precipitation", "precipitation"),
            ("Clouds", "clouds"),
            ("Wind", "wind"),
            ("Pressure", "pressure")
        ]
        
        for text, value in map_types:
            ttk.Radiobutton(
                self.map_type_frame, 
                text=text, 
                variable=self.map_type_var, 
                value=value,
                command=self.update_weather_map
            ).pack(side=tk.LEFT, padx=5)
        
        # Map display frame
        self.map_display_frame = ttk.Frame(self.maps_frame, relief=tk.SUNKEN, borderwidth=1)
        self.map_display_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Map placeholder
        self.map_label = ttk.Label(
            self.map_display_frame, 
            text="Weather map will be displayed here"
        )
        self.map_label.pack(fill=tk.BOTH, expand=True)
        
        # Note about maps implementation
        ttk.Label(
            self.maps_frame,
            text="""
Note: In a full implementation, this tab would display interactive weather maps using OpenWeatherMap's map tiles.
This would require additional API calls and integration with a mapping library.

For a production version, you could use:
- OpenWeatherMap's map tiles API
- A mapping library like Folium (for web) or tkintermapview (for desktop)
- Layer controls for different weather data visualizations
            """,
            font=self.custom_font,
            foreground="#666666",
            justify=tk.LEFT
        ).pack(pady=10)
    
    def setup_alerts_tab(self):
        # Weather alerts display
        self.alerts_frame = ttk.Frame(self.alerts_tab, padding=20)
        self.alerts_frame.pack(fill=tk.BOTH, expand=True)
        
        # Alerts header
        ttk.Label(
            self.alerts_frame, 
            text="Weather Alerts & Notifications", 
            font=self.title_font
        ).pack(pady=(0, 10))
        
        # Alert settings
        self.alert_settings_frame = ttk.LabelFrame(
            self.alerts_frame, 
            text="Alert Settings", 
            padding=10
        )
        self.alert_settings_frame.pack(fill=tk.X, pady=10)
        
        # Enable alerts
        self.enable_alerts_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.alert_settings_frame, 
            text="Enable Weather Alerts", 
            variable=self.enable_alerts_var
        ).pack(anchor=tk.W, pady=5)
        
        # Alert types
        ttk.Label(
            self.alert_settings_frame, 
            text="Alert Types:"
        ).pack(anchor=tk.W, pady=5)
        
        self.alert_types_frame = ttk.Frame(self.alert_settings_frame)
        self.alert_types_frame.pack(fill=tk.X, pady=5)
        
        # Alert type checkboxes
        self.severe_storm_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.alert_types_frame, 
            text="Severe Storms", 
            variable=self.severe_storm_var
        ).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.extreme_temp_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.alert_types_frame, 
            text="Extreme Temperatures", 
            variable=self.extreme_temp_var
        ).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        self.precipitation_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.alert_types_frame, 
            text="Heavy Precipitation", 
            variable=self.precipitation_var
        ).grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.wind_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.alert_types_frame, 
            text="High Winds", 
            variable=self.wind_var
        ).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Custom thresholds
        self.thresholds_frame = ttk.LabelFrame(
            self.alerts_frame, 
            text="Custom Alert Thresholds", 
            padding=10
        )
        self.thresholds_frame.pack(fill=tk.X, pady=10)
        
        # Temperature threshold
        ttk.Label(
            self.thresholds_frame, 
            text="Temperature Threshold (°C):"
        ).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.temp_threshold_var = tk.StringVar(value="35")
        ttk.Entry(
            self.thresholds_frame, 
            textvariable=self.temp_threshold_var, 
            width=5
        ).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Wind threshold
        ttk.Label(
            self.thresholds_frame, 
            text="Wind Speed Threshold (km/h):"
        ).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.wind_threshold_var = tk.StringVar(value="50")
        ttk.Entry(
            self.thresholds_frame, 
            textvariable=self.wind_threshold_var, 
            width=5
        ).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Save button
        ttk.Button(
            self.alerts_frame, 
            text="Save Alert Settings", 
            command=self.save_alert_settings
        ).pack(pady=10)
        
        # Active alerts
        self.active_alerts_frame = ttk.LabelFrame(
            self.alerts_frame, 
            text="Active Alerts", 
            padding=10
        )
        self.active_alerts_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Alerts listbox
        self.alerts_listbox = tk.Listbox(self.active_alerts_frame, height=10)
        self.alerts_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # No alerts message
        self.alerts_listbox.insert(tk.END, "No active weather alerts for this location")
    
    def apply_theme(self):
        # Apply dark or light theme based on the toggle
        if self.dark_mode.get():
            # Dark theme
            self.root.configure(bg="#1e1e1e")
            style = ttk.Style()
            style.theme_use('clam')
            
            # Configure colors
            style.configure("TFrame", background="#1e1e1e")
            style.configure("TLabel", background="#1e1e1e", foreground="#ffffff")
            style.configure("TButton", background="#3a3a3a", foreground="#ffffff")
            style.configure("TCheckbutton", background="#1e1e1e", foreground="#ffffff")
            style.configure("TRadiobutton", background="#1e1e1e", foreground="#ffffff")
            style.configure("TLabelframe", background="#1e1e1e", foreground="#ffffff")
            style.configure("TLabelframe.Label", background="#1e1e1e", foreground="#ffffff")
            style.configure("TNotebook", background="#1e1e1e", foreground="#ffffff")
            style.configure("TNotebook.Tab", background="#3a3a3a", foreground="#ffffff")
            
            # Configure the listbox colors
            self.locations_listbox.configure(bg="#2a2a2a", fg="#ffffff")
            self.alerts_listbox.configure(bg="#2a2a2a", fg="#ffffff")
            
            # Configure matplotlib
            self.fig.patch.set_facecolor('#1e1e1e')
            self.ax.set_facecolor('#2a2a2a')
            self.ax.tick_params(colors='white')
            self.ax.xaxis.label.set_color('white')
            self.ax.yaxis.label.set_color('white')
            self.ax.title.set_color('white')
            self.canvas.draw()
        else:
            # Light theme
            self.root.configure(bg="#f0f0f0")
            style = ttk.Style()
            style.theme_use('clam')
            
            # Configure colors
            style.configure("TFrame", background="#f0f0f0")
            style.configure("TLabel", background="#f0f0f0", foreground="#000000")
            style.configure("TButton", background="#e0e0e0", foreground="#000000")
            style.configure("TCheckbutton", background="#f0f0f0", foreground="#000000")
            style.configure("TRadiobutton", background="#f0f0f0", foreground="#000000")
            style.configure("TLabelframe", background="#f0f0f0", foreground="#000000")
            style.configure("TLabelframe.Label", background="#f0f0f0", foreground="#000000")
            style.configure("TNotebook", background="#f0f0f0", foreground="#000000")
            style.configure("TNotebook.Tab", background="#e0e0e0", foreground="#000000")
            
            # Configure the listbox colors
            self.locations_listbox.configure(bg="#ffffff", fg="#000000")
            self.alerts_listbox.configure(bg="#ffffff", fg="#000000")
            
            # Configure matplotlib
            self.fig.patch.set_facecolor('#f0f0f0')
            self.ax.set_facecolor('#ffffff')
            self.ax.tick_params(colors='black')
            self.ax.xaxis.label.set_color('black')
            self.ax.yaxis.label.set_color('black')
            self.ax.title.set_color('black')
            self.canvas.draw()
    
    def get_weather(self, country, city):
        try:
            self.status_bar.config(text=f"Fetching weather data for {city}, {country}...")
            
            # Current weather API call
            units = self.temp_unit.get()
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={self.api_key}&units={units}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                self.update_current_weather(data)
                
                # Get forecast data
                self.get_forecast(city, country)
                
                # Get historical data
                self.update_historical_data()
                
                # Update weather map
                self.update_weather_map()
                
                # Check for alerts
                self.check_weather_alerts(data)
                
                # Update status
                self.status_bar.config(text=f"Weather data updated for {city}, {country}")
                
                # Save current location for reference
                self.current_location = {"city": city, "country": country}
            else:
                messagebox.showerror("Error", f"Could not fetch weather data: {response.json().get('message', 'Unknown error')}")
                self.status_bar.config(text="Error fetching weather data")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_bar.config(text="Error fetching weather data")
    
    def update_current_weather(self, data):
        # Update location and time
        self.location_label.config(text=f"{data['name']}, {data['sys']['country']}")
        
        # Get local time at the location
        timezone_offset = data['timezone']  # in seconds from UTC
        local_time = datetime.utcnow() + timedelta(seconds=timezone_offset)
        self.time_label.config(text=f"Local time: {local_time.strftime('%A, %B %d, %Y %H:%M')}")
        
        # Update temperature and condition
        temp_unit = "°C" if self.temp_unit.get() == "metric" else "°F"
        self.temp_label.config(text=f"{data['main']['temp']:.1f}{temp_unit}")
        self.condition_label.config(text=data['weather'][0]['description'].capitalize())
        
        # Update weather icon
        icon_code = data['weather'][0]['icon']
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
        
        try:
            icon_response = requests.get(icon_url)
            if icon_response.status_code == 200:
                icon_data = icon_response.content
                icon_image = Image.open(io.BytesIO(icon_data))
                icon_photo = ImageTk.PhotoImage(icon_image)
                self.icon_label.config(image=icon_photo)
                self.icon_label.image = icon_photo  # Keep a reference
        except Exception as e:
            print(f"Error loading weather icon: {e}")
        
        # Update details
        self.feels_like_label.config(text=f"{data['main']['feels_like']:.1f}{temp_unit}")
        self.humidity_label.config(text=f"{data['main']['humidity']}%")
        
        # Wind speed unit
        wind_unit = "km/h" if self.temp_unit.get() == "metric" else "mph"
        self.wind_label.config(text=f"{data['wind']['speed']} {wind_unit}, {self.get_wind_direction(data['wind']['deg'])}")
        
        self.pressure_label.config(text=f"{data['main']['pressure']} hPa")
        
        # Visibility (convert from meters)
        visibility_km = data['visibility'] / 1000
        self.visibility_label.config(text=f"{visibility_km:.1f} km")
        
        # Sunrise and sunset (convert from unix timestamp to local time)
        sunrise_time = datetime.fromtimestamp(data['sys']['sunrise'] + data['timezone'])
        sunset_time = datetime.fromtimestamp(data['sys']['sunset'] + data['timezone'])
        
        self.sunrise_label.config(text=sunrise_time.strftime('%H:%M'))
        self.sunset_label.config(text=sunset_time.strftime('%H:%M'))
        
        # UV Index (would need another API call, using placeholder)
        self.uv_label.config(text="N/A")
        
        # Update last updated time
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.last_updated_label.config(text=f"Last updated: {current_time}")
    
    def get_wind_direction(self, degrees):
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                      "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    def get_forecast(self, city, country):
        try:
            units = self.temp_unit.get()
            url = f"https://api.openweathermap.org/data/2.5/forecast?q={city},{country}&appid={self.api_key}&units={units}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                self.update_forecast_display(data)
            else:
                print(f"Error fetching forecast: {response.json().get('message', 'Unknown error')}")
        except Exception as e:
            print(f"Error in get_forecast: {e}")
    
    def update_forecast_display(self, data):
        # Clear existing forecast widgets
        for widget in self.forecast_container.winfo_children():
            widget.destroy()
        
        # Get daily forecasts (the API returns 3-hour forecasts, we'll take one per day)
        daily_forecasts = []
        current_date = None
        
        for item in data['list']:
            forecast_date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
            
            if forecast_date != current_date:
                current_date = forecast_date
                daily_forecasts.append(item)
                
                if len(daily_forecasts) >= 5:  # We only need 5 days
                    break
        
        # Create forecast cards
        for i, forecast in enumerate(daily_forecasts):
            date = datetime.fromtimestamp(forecast['dt'])
            temp_unit = "°C" if self.temp_unit.get() == "metric" else "°F"
            
            frame = ttk.LabelFrame(
                self.forecast_container, 
                text=date.strftime('%A')
            )
            frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            
            # Date
            ttk.Label(
                frame, 
                text=date.strftime('%b %d')
            ).pack(pady=2)
            
            # Try to get weather icon
            icon_code = forecast['weather'][0]['icon']
            icon_url = f"http://openweathermap.org/img/wn/{icon_code}.png"
            
            try:
                icon_response = requests.get(icon_url)
                if icon_response.status_code == 200:
                    icon_data = icon_response.content
                    icon_image = Image.open(io.BytesIO(icon_data))
                    icon_photo = ImageTk.PhotoImage(icon_image)
                    icon_label = ttk.Label(frame, image=icon_photo)
                    icon_label.image = icon_photo  # Keep a reference
                    icon_label.pack(pady=2)
                else:
                    ttk.Label(frame, text="[Icon]").pack(pady=2)
            except Exception as e:
                print(f"Error loading forecast icon: {e}")
                ttk.Label(frame, text="[Icon]").pack(pady=2)
            
            # Temperature
            ttk.Label(
                frame, 
                text=f"{forecast['main']['temp']:.1f}{temp_unit}"
            ).pack(pady=2)
            
            # Condition
            ttk.Label(
                frame, 
                text=forecast['weather'][0]['description'].capitalize()
            ).pack(pady=2)
            
            # Additional info
            ttk.Label(
                frame, 
                text=f"Humidity: {forecast['main']['humidity']}%"
            ).pack(pady=2)
            
            wind_unit = "km/h" if self.temp_unit.get() == "metric" else "mph"
            ttk.Label(
                frame, 
                text=f"Wind: {forecast['wind']['speed']} {wind_unit}"
            ).pack(pady=2)
        
        # Make columns expandable
        for i in range(5):
            self.forecast_container.columnconfigure(i, weight=1)
    
    def update_historical_data(self):
        # In a real app, this would fetch historical data from an API
        # For this demo, we'll generate some random data
        
        # Clear the plot
        self.ax.clear()
        
        # Determine date range based on selected period
        period = self.period_var.get()
        if period == "7days":
            days = 7
        elif period == "30days":
            days = 30
        else:  # 90days
            days = 90
        
        # Generate dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = [start_date + timedelta(days=i) for i in range(days)]
        
        # Generate random temperature data with a realistic pattern
        base_temp = 25  # Base temperature
        temp_range = 10  # Temperature variation
        temps = []
        
        for i in range(days):
            # Add some seasonality and randomness
            seasonal_factor = math.sin(i / days * 2 * math.pi) * 5
            random_factor = random.uniform(-3, 3)
            temp = base_temp + seasonal_factor + random_factor
            temps.append(temp)
        
        # Plot the data
        self.ax.plot(dates, temps, 'b-', linewidth=2)
        
        # Format the plot
        self.ax.set_title(f"Temperature History - Last {days} Days")
        self.ax.set_xlabel("Date")
        
        temp_unit = "°C" if self.temp_unit.get() == "metric" else "°F"
        self.ax.set_ylabel(f"Temperature ({temp_unit})")
        
        self.ax.grid(True)
        self.fig.autofmt_xdate()  # Rotate date labels
        
        # Update the canvas
        self.canvas.draw()
    
    def update_weather_map(self):
        # In a real app, this would fetch map data from an API
        # For this demo, we'll show a message
        map_type = self.map_type_var.get()
        
        # Clear any existing content
        for widget in self.map_display_frame.winfo_children():
            widget.destroy()
        
        # Display a message with more details about the selected map type
        map_descriptions = {
            "temp": "Temperature map showing global or regional temperature patterns with color gradients.",
            "precipitation": "Precipitation map showing rainfall and snowfall patterns with intensity indicators.",
            "clouds": "Cloud coverage map showing the percentage of cloud cover across regions.",
            "wind": "Wind map showing wind direction and speed with arrows and color coding.",
            "pressure": "Atmospheric pressure map showing high and low pressure systems."
        }
        
        description = map_descriptions.get(map_type, "")
        
        ttk.Label(
            self.map_display_frame, 
            text=f"Weather Map: {map_type.capitalize()}\n\n{description}\n\n"
                 f"In a full implementation, this would show an interactive map\n"
                 f"using OpenWeatherMap's map tiles or a similar service.\n\n"
                 f"API Endpoint: https://tile.openweathermap.org/map/{map_type}/{{z}}/{{x}}/{{y}}.png?appid={self.api_key}",
            justify=tk.CENTER
        ).pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    def check_weather_alerts(self, data):
        # Clear existing alerts
        self.alerts_listbox.delete(0, tk.END)
        
        if not self.enable_alerts_var.get():
            self.alerts_listbox.insert(tk.END, "Weather alerts are disabled")
            return
        
        alerts = []
        
        # Check temperature
        if self.extreme_temp_var.get():
            try:
                temp_threshold = float(self.temp_threshold_var.get())
                current_temp = data['main']['temp']
                
                if current_temp > temp_threshold:
                    alerts.append(f"High Temperature Alert: Current temperature ({current_temp:.1f}°) exceeds threshold ({temp_threshold:.1f}°)")
            except ValueError:
                pass
        
        # Check wind
        if self.wind_var.get():
            try:
                wind_threshold = float(self.wind_threshold_var.get())
                current_wind = data['wind']['speed']
                wind_unit = "km/h" if self.temp_unit.get() == "metric" else "mph"
                
                if current_wind > wind_threshold:
                    alerts.append(f"High Wind Alert: Current wind speed ({current_wind} {wind_unit}) exceeds threshold ({wind_threshold} {wind_unit})")
            except ValueError:
                pass
        
        # Check for severe weather conditions
        if self.severe_storm_var.get():
            weather_id = data['weather'][0]['id']
            
            # Thunderstorm
            if 200 <= weather_id < 300:
                alerts.append("Severe Weather Alert: Thunderstorm conditions detected")
            
            # Heavy rain
            elif 500 <= weather_id < 600 and weather_id >= 502:
                alerts.append("Severe Weather Alert: Heavy rainfall detected")
            
            # Snow
            elif 600 <= weather_id < 700 and weather_id >= 602:
                alerts.append("Severe Weather Alert: Heavy snowfall detected")
        
        # Display alerts
        if alerts:
            for alert in alerts:
                self.alerts_listbox.insert(tk.END, alert)
                
                # In a real app, you might show a notification here
                # For this demo, we'll just print to console
                print(f"ALERT: {alert}")
        else:
            self.alerts_listbox.insert(tk.END, "No active weather alerts for this location")
    
    def save_alert_settings(self):
        messagebox.showinfo("Settings Saved", "Your alert settings have been saved successfully.")
    
    def on_location_select(self, event):
        # Get selected location
        selection = self.locations_listbox.curselection()
        if selection:
            index = selection[0]
            location = self.saved_locations[index]
            
            # Update entry fields
            self.country_var.set(location['country'])
            self.city_var.set(location['city'])
            
            # Get weather for selected location
            self.get_weather(location['country'], location['city'])
    
    def add_current_location(self):
        # Check if we have a current location
        if hasattr(self, 'current_location'):
            # Check if location already exists
            location_exists = False
            for loc in self.saved_locations:
                if (loc['city'] == self.current_location['city'] and 
                    loc['country'] == self.current_location['country']):
                    location_exists = True
                    break
            
            if not location_exists:
                # Add to saved locations
                self.saved_locations.append(self.current_location)
                
                # Update listbox
                self.locations_listbox.insert(
                    tk.END, 
                    f"{self.current_location['city']}, {self.current_location['country']}"
                )
                
                messagebox.showinfo(
                    "Location Added", 
                    f"{self.current_location['city']}, {self.current_location['country']} added to saved locations."
                )
            else:
                messagebox.showinfo(
                    "Location Exists", 
                    f"{self.current_location['city']}, {self.current_location['country']} is already in your saved locations."
                )
    
    def remove_selected_location(self):
        # Get selected location
        selection = self.locations_listbox.curselection()
        if selection:
            index = selection[0]
            location = self.saved_locations[index]
            
            # Remove from saved locations
            self.saved_locations.pop(index)
            
            # Update listbox
            self.locations_listbox.delete(index)
            
            messagebox.showinfo(
                "Location Removed", 
                f"{location['city']}, {location['country']} removed from saved locations."
            )
    
    def refresh_weather(self):
        # Refresh weather for current location
        if hasattr(self, 'current_location'):
            self.get_weather(
                self.current_location['country'], 
                self.current_location['city']
            )
    
    def background_update(self):
        # Background thread to update weather periodically
        while True:
            # Sleep for 15 minutes
            time.sleep(900)
            
            # Refresh weather if we have a current location
            if hasattr(self, 'current_location'):
                # Use threading to avoid blocking the UI
                self.root.after(
                    0, 
                    lambda: self.get_weather(
                        self.current_location['country'], 
                        self.current_location['city']
                    )
                )

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()