import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk, ImageFilter, ImageDraw, ImageFont
import pyautogui
import threading
import time
import pystray
from pystray import MenuItem as item
import sys
import os
import shutil
import webbrowser
from tkinter import ttk
from PIL import ImageDraw, ImageFont, ImageTk
from win10toast import ToastNotifier
from screeninfo import get_monitors
import pygame
import numpy as np

# Initialize toast notifier
toast = ToastNotifier()

# Application info
APP_VERSION = "1.0.0"
APP_WEBSITE = "https://nejawittatchy.github.io/"
APP_EMAIL = "neja.developer@gmail.com"

# Settings management
import json
import appdirs

# Import Windows API modules
import win32gui
import win32process
import psutil
import re

# Initialize pygame mixer for audio
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Default settings
DEFAULT_SETTINGS = {
    'break_interval': 20 * 60,  # 20 minutes in seconds
    'break_duration': 20,       # 20 seconds
    'notification_enabled': True,
    'notification_sound': True,
    'start_with_windows': False,
    'blur_intensity': 8,        # Gaussian blur radius
    'dim_screen': True,        # Dim screen during break
    'auto_pause': True,        # Auto-pause during video calls
    'break_music_enabled': True,  # Play calming music during breaks
    'break_music_volume': 0.3,    # Volume (0.0 to 1.0)
    'auto_pause_apps': [       # Apps that trigger auto-pause
        'zoom',
        'teams',
        'skype',
        'webex',
        'discord',
        'slack',
        'meet.google.com',
        'gotomeeting'
    ]
}

# Get user config directory
CONFIG_DIR = appdirs.user_config_dir('SoftEyes', 'nejawittatchy')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'settings.json')

def load_settings():
    """Load settings from disk or return defaults if no saved settings exist."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                saved = json.load(f)
                # Merge with defaults to ensure all keys exist
                return {**DEFAULT_SETTINGS, **saved}
    except Exception as e:
        print(f"DEBUG: Failed to load settings: {e}")
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """Save settings to disk."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"DEBUG: Failed to save settings: {e}")
        return False

# Load or initialize settings
current_settings = load_settings()
break_interval = current_settings['break_interval']
break_duration = current_settings['break_duration']

paused = False
snoozed_until = 0
next_break_time = 0
tray_icon = None

def create_tray_image(text):
    # Create a new image with a black background
    image = Image.new('RGB', (64, 64), color='black')
    draw = ImageDraw.Draw(image)
    
    # Add the remaining minutes text
    minutes = text if isinstance(text, str) else str(text)
    
    # Use a bold font
    try:
        font = ImageFont.truetype("arialbd.ttf", 40)  # Arial Bold font
    except:
        try:
            # Fallback to regular arial with simulated bold
            font = ImageFont.truetype("arial.ttf", 40)
            # We'll draw the text twice with a slight offset to simulate bold
            is_simulated_bold = True
        except:
            font = None
            is_simulated_bold = False
    
    # Calculate text position to center it (with the new font)
    text_bbox = draw.textbbox((0, 0), minutes, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    x = (64 - text_width) // 2
    y = (64 - text_height) // 2
    
    if font and 'is_simulated_bold' in locals() and is_simulated_bold:
        # Simulate bold by drawing text multiple times with slight offsets
        draw.text((x-1, y), minutes, fill='white', font=font)
        draw.text((x+1, y), minutes, fill='white', font=font)
        draw.text((x, y-1), minutes, fill='white', font=font)
        draw.text((x, y+1), minutes, fill='white', font=font)
    
    # Draw the main text
    draw.text((x, y), minutes, fill='white', font=font)
    
    return image

def generate_calming_tone(duration=20, frequency=432):
    """Generate a calming ambient tone at 432 Hz (healing frequency)."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    
    # Generate a soft sine wave with gentle harmonics
    t = np.linspace(0, duration, n_samples, False)
    
    # Base tone at 432 Hz (known as healing frequency)
    tone = np.sin(2 * np.pi * frequency * t)
    
    # Add soft harmonics for richness
    tone += 0.3 * np.sin(2 * np.pi * (frequency * 2) * t)  # Octave
    tone += 0.2 * np.sin(2 * np.pi * (frequency * 3) * t)  # Fifth
    
    # Apply fade in/out for smooth transitions
    fade_duration = int(sample_rate * 2)  # 2 second fade
    fade_in = np.linspace(0, 1, fade_duration)
    fade_out = np.linspace(1, 0, fade_duration)
    tone[:fade_duration] *= fade_in
    tone[-fade_duration:] *= fade_out
    
    # Normalize and convert to 16-bit
    tone = (tone * 32767 * 0.5).astype(np.int16)  # 50% max volume
    
    # Stereo (duplicate for both channels)
    stereo_tone = np.column_stack((tone, tone))
    
    return pygame.sndarray.make_sound(stereo_tone)

def play_break_music():
    """Play calming music during break."""
    if not current_settings.get('break_music_enabled', True):
        return
    
    try:
        duration = break_duration
        sound = generate_calming_tone(duration=duration, frequency=432)
        
        # Set volume from settings
        volume = current_settings.get('break_music_volume', 0.3)
        sound.set_volume(volume)
        
        # Play the sound
        sound.play()
        print("DEBUG: Playing calming break music")
    except Exception as e:
        print(f"DEBUG: Failed to play break music: {e}")

def stop_break_music():
    """Stop any playing break music."""
    try:
        pygame.mixer.stop()
        print("DEBUG: Stopped break music")
    except Exception as e:
        print(f"DEBUG: Failed to stop music: {e}")

def take_blurred_screenshots():
    """Take and blur screenshots of all monitors."""
    print("DEBUG: Taking blurred screenshots for all monitors...")
    blur_radius = current_settings['blur_intensity']
    screenshots = []
    
    try:
        monitors = get_monitors()
        for monitor in monitors:
            # Take screenshot of this monitor
            screenshot = pyautogui.screenshot(region=(monitor.x, monitor.y, 
                                                    monitor.width, monitor.height))
            # Apply blur
            blurred = screenshot.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            screenshots.append((monitor, blurred))
            print(f"DEBUG: Screenshot taken for monitor at {monitor.x},{monitor.y}")
    except Exception as e:
        print(f"DEBUG: Error taking screenshots: {e}")
        # Fallback to single screen if multi-monitor fails
        screenshot = pyautogui.screenshot()
        blurred = screenshot.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        screenshots.append((None, blurred))
    
    return screenshots

class OverlayWindow(tk.Toplevel):
    """A class to manage each monitor's overlay window."""
    def __init__(self, parent, monitor, image):
        super().__init__()
        
        # Remove window decorations and make it stay on top
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        
        # Position window on the correct monitor
        if monitor:
            self.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
        else:
            self.attributes('-fullscreen', True)
        
        # Apply screen dimming if enabled
        bg_color = 'black' if current_settings['dim_screen'] else 'white'
        self.configure(bg=bg_color)
        
        # Add blurred background
        self.image = ImageTk.PhotoImage(image)
        bg_label = tk.Label(self, image=self.image)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Add message
        text = tk.Label(self, text="Rest your eyes 🌿\nLook 20 feet away",
                       fg='white', bg='black', font=('Helvetica', 32),
                       justify='center')
        text.place(relx=0.5, rely=0.5, anchor='center')
        
        # Schedule window destruction
        self.after(break_duration * 1000, self.destroy)

def show_blur_overlay():
    """Show blur overlay on all monitors."""
    print("DEBUG: Showing blur overlay on all monitors...")
    
    # Start playing calming music
    play_break_music()
    
    # Create a hidden root window to manage overlays
    root = tk.Tk()
    root.withdraw()
    
    # Create overlay for each monitor
    screenshots = take_blurred_screenshots()
    overlays = []
    
    for monitor, screenshot in screenshots:
        try:
            overlay = OverlayWindow(root, monitor, screenshot)
            overlays.append(overlay)
        except Exception as e:
            print(f"DEBUG: Error creating overlay: {e}")
    
    if overlays:
        print(f"DEBUG: Created {len(overlays)} overlay windows")
        print(f"DEBUG: Overlays will close in {break_duration} seconds")
        
        # Stop music and destroy windows after break
        def cleanup():
            stop_break_music()
            root.destroy()
        
        root.after(break_duration * 1000 + 500, cleanup)
        root.mainloop()
    else:
        print("DEBUG: No overlays created, destroying root")
        stop_break_music()
        root.destroy()

def format_time_remaining(seconds):
    """Format remaining time in a human-readable way."""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    if seconds == 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    return f"{minutes}:{seconds:02d}"

def update_tray_title():
    global next_break_time, tray_icon
    while True:
        if not tray_icon:
            time.sleep(1)
            continue

        current_time = time.time()
        
        if paused:
            new_icon = create_tray_image("P")
        elif current_time >= snoozed_until:  # Not snoozed
            remaining = max(0, next_break_time - current_time)
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            
            # Update icon
            if remaining <= 60:  # Last minute: show seconds
                new_icon = create_tray_image(str(seconds))
            else:
                new_icon = create_tray_image(str(minutes))
        else:
            # Show remaining snooze time
            remaining = max(0, snoozed_until - current_time)
            minutes = int(remaining // 60)
            new_icon = create_tray_image(f"S{minutes}")
        
        try:
            # Update tray icon, tooltip, and menu status
            tray_icon.icon = new_icon
            # Only update the tooltip
            tray_icon.title = get_status_text()
            # The menu item text will update automatically through the lambda
        except Exception as e:
            print(f"DEBUG: Error updating tray: {e}")
        
        time.sleep(1)  # Update every second

def reminder_loop():
    global paused, snoozed_until, next_break_time
    print("DEBUG: Starting reminder loop...")
    
    def show_notification(message, duration=5):
        """Show a Windows notification if enabled in settings."""
        if current_settings['notification_enabled']:
            try:
                toast.show_toast(
                    "SoftEyes",
                    message,
                    duration=duration,
                    icon_path=None,  # You can add an icon path here
                    threaded=True
                )
            except Exception as e:
                print(f"DEBUG: Failed to show notification: {e}")
    
    # Start auto-pause check thread
    def auto_pause_check():
        while True:
            update_auto_pause()
            time.sleep(2)  # Check every 2 seconds
    
    threading.Thread(target=auto_pause_check, daemon=True).start()
    print("DEBUG: Started auto-pause detection thread")
    
    while True:
        time.sleep(1)
        if paused:
            print("DEBUG: App is paused, skipping reminder")
            continue
        if time.time() < snoozed_until:
            print("DEBUG: App is snoozed, skipping reminder")
            continue
        
        next_break_time = time.time() + break_interval
        print(f"DEBUG: Waiting {break_interval} seconds until next reminder")
        
        # Wait for break, but check every second for pause/snooze
        seconds_waited = 0
        while seconds_waited < break_interval:
            if paused or time.time() < snoozed_until:
                break
            
            # Show notification 10 seconds before break
            if break_interval - seconds_waited == 10:
                show_notification("Break time in 10 seconds! Get ready to rest your eyes.")
            
            time.sleep(1)
            seconds_waited += 1
        
        if not paused and time.time() >= snoozed_until:
            print("DEBUG: Triggering break reminder")
            # Show notification for break start
            show_notification("Time to rest your eyes! Look 20 feet away for 20 seconds.")
            threading.Thread(target=show_blur_overlay).start()

# --- App Detection and Auto-Pause ---

class AppDetector:
    """Detect active applications and manage auto-pause."""
    
    def __init__(self):
        self.last_check = 0
        self.check_interval = 2  # Check every 2 seconds
        self.cached_result = False
    
    def is_video_call_active(self):
        """Check if any video conferencing app is active."""
        current_time = time.time()
        
        # Use cached result if checked recently
        if current_time - self.last_check < self.check_interval:
            return self.cached_result
        
        self.last_check = current_time
        
        try:
            # Get foreground window info
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Get process info
            try:
                process = psutil.Process(pid)
                process_name = process.name().lower()
                window_title = win32gui.GetWindowText(hwnd).lower()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.cached_result = False
                return False
            
            # Check if process name or window title matches any video call app
            for app in current_settings['auto_pause_apps']:
                if (app in process_name or 
                    app in window_title or 
                    app.replace('.', '').replace('/', '') in process_name):
                    self.cached_result = True
                    return True
            
            self.cached_result = False
            return False
            
        except Exception as e:
            print(f"DEBUG: Error checking active apps: {e}")
            self.cached_result = False
            return False

# Initialize app detector and pause tracking
app_detector = AppDetector()
manual_pause = False

def update_auto_pause():
    """Check and update auto-pause state."""
    global paused, manual_pause
    
    if not current_settings['auto_pause']:
        return
    
    video_call_active = app_detector.is_video_call_active()
    
    if video_call_active and not paused:
        # Auto-pause if video call detected
        paused = True
        if current_settings['notification_enabled']:
            toast.show_toast(
                "SoftEyes",
                "Breaks paused - Video call detected",
                duration=3,
                threaded=True
            )
        print("DEBUG: Auto-paused due to video call")
    elif not video_call_active and paused and not manual_pause:
        # Auto-resume if no video call and wasn't manually paused
        paused = False
        if current_settings['notification_enabled']:
            toast.show_toast(
                "SoftEyes",
                "Breaks resumed - Video call ended",
                duration=3,
                threaded=True
            )
        print("DEBUG: Auto-resumed after video call")

# --- Control Functions ---

def toggle_pause(icon, item):
    global paused, manual_pause
    paused = not paused
    manual_pause = paused  # Track if pause was manual
    print(f"DEBUG: Pause state changed to: {paused}")
    icon.update_menu()

def snooze(icon, item):
    global snoozed_until
    snoozed_until = time.time() + 3600  # 1 hour
    print("DEBUG: App snoozed for 1 hour")

def add_to_startup():
    try:
        # Get the path of the executable
        if getattr(sys, 'frozen', False):
            app_path = sys.executable
        else:
            return False  # Only proceed if running as exe
            
        # Get startup folder path
        startup_folder = os.path.join(
            os.getenv('APPDATA'),
            r'Microsoft\Windows\Start Menu\Programs\Startup'
        )
        
        # Create destination path
        dest_path = os.path.join(startup_folder, 'SoftEyes.exe')
        
        # Copy the executable
        shutil.copy2(app_path, dest_path)
        return True
    except Exception as e:
        print(f"DEBUG: Failed to add to startup: {e}")
        return False

def get_app_root():
    if not hasattr(get_app_root, "root"):
        get_app_root.root = tk.Tk()
        get_app_root.root.withdraw()
    return get_app_root.root

def open_settings(icon, item):
    """Open settings in a new window - simple, clean approach."""
    def show_settings():
        global break_interval, break_duration, current_settings
        
        # Create new window
        win = tk.Tk()
        win.title("SoftEyes Settings")
        win.geometry("450x600")
        win.resizable(False, False)
        
        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(win)
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Main frame inside scrollable area
        frame = ttk.Frame(scrollable_frame, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Enable mousewheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Style
        style = ttk.Style()
        style.configure("H.TLabel", font=("Arial", 11, "bold"))
        
        # Timer Settings
        ttk.Label(frame, text="Timer Settings", style="H.TLabel").pack(anchor="w", pady=(0,10))
        tf = ttk.LabelFrame(frame, padding=10)
        tf.pack(fill="x", pady=(0,15))
        
        # Interval
        f1 = ttk.Frame(tf)
        f1.pack(fill="x", pady=5)
        ttk.Label(f1, text="Break Interval:").pack(side="left")
        iv = tk.StringVar(value=str(break_interval//60))
        ttk.Entry(f1, textvariable=iv, width=10).pack(side="left", padx=5)
        ttk.Label(f1, text="minutes").pack(side="left")
        
        # Duration
        f2 = ttk.Frame(tf)
        f2.pack(fill="x", pady=5)
        ttk.Label(f2, text="Break Duration:").pack(side="left")
        dv = tk.StringVar(value=str(break_duration))
        ttk.Entry(f2, textvariable=dv, width=10).pack(side="left", padx=5)
        ttk.Label(f2, text="seconds").pack(side="left")
        
        # Notifications
        ttk.Label(frame, text="Notifications", style="H.TLabel").pack(anchor="w", pady=(0,10))
        nf = ttk.LabelFrame(frame, padding=10)
        nf.pack(fill="x", pady=(0,15))
        nev = tk.BooleanVar(value=current_settings['notification_enabled'])
        ttk.Checkbutton(nf, text="Show notifications before breaks", variable=nev).pack(anchor="w")
        sev = tk.BooleanVar(value=current_settings['notification_sound'])
        ttk.Checkbutton(nf, text="Play sound on break start/end", variable=sev).pack(anchor="w")
        
        # Break Screen
        ttk.Label(frame, text="Break Screen", style="H.TLabel").pack(anchor="w", pady=(0,10))
        bf = ttk.LabelFrame(frame, padding=10)
        bf.pack(fill="x", pady=(0,15))
        f3 = ttk.Frame(bf)
        f3.pack(fill="x", pady=5)
        ttk.Label(f3, text="Blur Intensity:").pack(side="left")
        bv = tk.IntVar(value=current_settings['blur_intensity'])
        ttk.Scale(f3, from_=1, to=15, variable=bv, orient="horizontal").pack(side="left", fill="x", expand=True, padx=5)
        dev = tk.BooleanVar(value=current_settings['dim_screen'])
        ttk.Checkbutton(bf, text="Dim screen during break", variable=dev).pack(anchor="w")
        
        # Startup
        ttk.Label(frame, text="Startup", style="H.TLabel").pack(anchor="w", pady=(0,10))
        sf = ttk.LabelFrame(frame, padding=10)
        sf.pack(fill="x", pady=(0,15))
        sv = tk.BooleanVar(value=current_settings['start_with_windows'])
        ttk.Checkbutton(sf, text="Start SoftEyes with Windows", variable=sv).pack(anchor="w")
        
        # Auto-Pause
        ttk.Label(frame, text="Auto-Pause", style="H.TLabel").pack(anchor="w", pady=(0,10))
        af = ttk.LabelFrame(frame, padding=10)
        af.pack(fill="x", pady=(0,15))
        av = tk.BooleanVar(value=current_settings['auto_pause'])
        ttk.Checkbutton(af, text="Auto pause during video calls", variable=av).pack(anchor="w")
        
        # Break Music
        ttk.Label(frame, text="Break Music", style="H.TLabel").pack(anchor="w", pady=(0,10))
        mf = ttk.LabelFrame(frame, padding=10)
        mf.pack(fill="x", pady=(0,15))
        mv = tk.BooleanVar(value=current_settings.get('break_music_enabled', True))
        ttk.Checkbutton(mf, text="Play calming music during breaks", variable=mv).pack(anchor="w")
        
        # Volume slider
        vol_frame = ttk.Frame(mf)
        vol_frame.pack(fill="x", pady=5)
        ttk.Label(vol_frame, text="Volume:").pack(side="left")
        volv = tk.DoubleVar(value=current_settings.get('break_music_volume', 0.3))
        vol_slider = ttk.Scale(vol_frame, from_=0, to=1, variable=volv, orient="horizontal")
        vol_slider.pack(side="left", fill="x", expand=True, padx=5)
        vol_label = ttk.Label(vol_frame, text=f"{int(volv.get()*100)}%")
        vol_label.pack(side="left")
        
        # Update volume label when slider moves
        def update_vol_label(*args):
            vol_label.config(text=f"{int(volv.get()*100)}%")
        volv.trace('w', update_vol_label)
        
        # Test sound button
        def test_sound():
            try:
                # Generate a short 5-second test tone
                test_tone = generate_calming_tone(duration=5, frequency=432)
                test_tone.set_volume(volv.get())
                test_tone.play()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to play test sound: {e}")
        
        ttk.Button(mf, text="🔊 Test Sound", command=test_sound).pack(anchor="w", pady=(5,0))
        
        # Buttons
        bf2 = ttk.Frame(frame)
        bf2.pack(fill="x", pady=(15,0))
        
        def save():
            try:
                ni = int(iv.get())
                nd = int(dv.get())
                if ni < 1 or nd < 5:
                    messagebox.showerror("Error", "Invalid values")
                    return
                
                global break_interval, break_duration
                break_interval = ni * 60
                break_duration = nd
                current_settings.update({
                    'break_interval': break_interval,
                    'break_duration': break_duration,
                    'notification_enabled': nev.get(),
                    'notification_sound': sev.get(),
                    'blur_intensity': bv.get(),
                    'dim_screen': dev.get(),
                    'start_with_windows': sv.get(),
                    'auto_pause': av.get(),
                    'break_music_enabled': mv.get(),
                    'break_music_volume': volv.get()
                })
                
                if sv.get():
                    add_to_startup()
                
                if save_settings(current_settings):
                    canvas.unbind_all("<MouseWheel>")
                    win.destroy()
                else:
                    messagebox.showerror("Error", "Failed to save")
            except:
                messagebox.showerror("Error", "Invalid input")
        
        ttk.Button(bf2, text="Save", command=save).pack(side="right", padx=5)
        
        def close_window():
            canvas.unbind_all("<MouseWheel>")
            win.destroy()
        
        ttk.Button(bf2, text="Cancel", command=close_window).pack(side="right")
        win.protocol("WM_DELETE_WINDOW", close_window)
        
        # Center window
        win.update_idletasks()
        w = win.winfo_width()
        h = win.winfo_height()
        x = (win.winfo_screenwidth()//2) - (w//2)
        y = (win.winfo_screenheight()//2) - (h//2)
        win.geometry(f"+{x}+{y}")
        
        win.mainloop()
    
    threading.Thread(target=show_settings, daemon=True).start()




def load_changelog():
    """Load the changelog content."""
    try:
        with open('CHANGELOG.md', 'r') as f:
            return f.read()
    except Exception as e:
        print(f"DEBUG: Failed to load changelog: {e}")
        return "Changelog not available"

def open_about(icon, item):
    """Show About window - simple, clean approach."""
    def show_about():
        # Create new window
        win = tk.Tk()
        win.title("About SoftEyes")
        win.geometry("550x650")
        win.resizable(False, False)
        
        # Main frame
        frame = ttk.Frame(win, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # App icon
        try:
            img = Image.open("app_icon.png")
            img = img.resize((64, 64), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            lbl = ttk.Label(frame, image=photo)
            lbl.image = photo
            lbl.pack(pady=(0, 10))
        except:
            pass
        
        # Title and version
        ttk.Label(frame, text="SoftEyes", font=("Arial", 18, "bold")).pack()
        ttk.Label(frame, text=f"Version {APP_VERSION}", font=("Arial", 10)).pack(pady=5)
        ttk.Label(frame, text="Your friendly eye care companion", 
                 font=("Arial", 9, "italic")).pack(pady=(0, 15))
        
        # Tabs
        tabs = ttk.Notebook(frame)
        tabs.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Developer Tab
        dev = ttk.Frame(tabs, padding=15)
        tabs.add(dev, text="Developer Info")
        
        ttk.Label(dev, text="Developer: Neja Wittatchy", font=("Arial", 10, "bold")).pack(pady=5)
        
        # Links
        style = ttk.Style()
        style.configure("Link.TLabel", foreground="blue", cursor="hand2")
        
        email = ttk.Label(dev, text=APP_EMAIL, style="Link.TLabel")
        email.pack(pady=2)
        email.bind("<Button-1>", lambda e: webbrowser.open(f"mailto:{APP_EMAIL}"))
        
        web = ttk.Label(dev, text="Visit Portfolio", style="Link.TLabel")
        web.pack(pady=2)
        web.bind("<Button-1>", lambda e: webbrowser.open(APP_WEBSITE))
        
        ttk.Separator(dev, orient="horizontal").pack(fill="x", pady=15)
        
        # Features
        features = """Key Features:
• Smart break reminders (20-20-20 rule)
• Multi-monitor support
• Customizable intervals and duration
• Screen blur during breaks
• Desktop notifications
• System tray integration
• Auto-pause during video calls
• Start with Windows option"""
        
        ttk.Label(dev, text=features, justify="left", font=("Arial", 9)).pack(anchor="w", padx=10)
        
        # Changelog Tab
        log = ttk.Frame(tabs, padding=10)
        tabs.add(log, text="Changelog")
        
        # Changelog text with scrollbar
        log_frame = ttk.Frame(log)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        txt = tk.Text(log_frame, wrap="word", height=20, width=60, font=("Consolas", 9))
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        
        txt.pack(side="left", fill=tk.BOTH, expand=True)
        scroll.pack(side="right", fill="y")
        
        # Load changelog
        try:
            with open('CHANGELOG.md', 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            content = "Changelog not available"
        
        txt.insert("1.0", content)
        txt.configure(state="disabled")
        
        # Close button
        ttk.Button(frame, text="Close", command=win.destroy).pack(pady=(10, 0))
        
        # Center window
        win.update_idletasks()
        w = win.winfo_width()
        h = win.winfo_height()
        x = (win.winfo_screenwidth()//2) - (w//2)
        y = (win.winfo_screenheight()//2) - (h//2)
        win.geometry(f"+{x}+{y}")
        
        win.mainloop()
    
    threading.Thread(target=show_about, daemon=True).start()

def quit_app(icon, item):
    print("DEBUG: Quitting application...")
    icon.stop()
    os._exit(0)

def get_status_text(menu_item=None):
    """Generate the status text for the tray menu."""
    interval_min = break_interval // 60
    duration_sec = break_duration
    
    if paused:
        status = "⏸️ Paused"
    elif time.time() < snoozed_until:
        remaining = max(0, snoozed_until - time.time())
        status = f"💤 Snoozed for {format_time_remaining(remaining)}"
    else:
        remaining = max(0, next_break_time - time.time())
        status = f"⏳ Next break in {format_time_remaining(remaining)}"
    
    return f"{status}\n📅 {interval_min}min break every {duration_sec}sec"

def setup_tray():
    global tray_icon
    print("DEBUG: Setting up tray...")
    # Create initial icon with "0" minutes
    image = create_tray_image("0")
    print("DEBUG: Tray icon created.")
    menu = (
        # Status display (disabled menu item)
        item(lambda item: get_status_text(item), lambda _: None, enabled=False),
        # Separator
        item('─' * 25, lambda _: None, enabled=False),
        # Action items
        item(lambda item: "⏸️ Pause" if not paused else "▶️ Resume", toggle_pause),
        item('💤 Snooze 1 Hour', snooze),
        item('ℹ️ About', open_about),
        item('⚙️ Settings', open_settings),
        item('❌ Quit', quit_app)
    )

    tray_icon = pystray.Icon("SoftEyes", image, "SoftEyes", menu)
    print("DEBUG: Starting reminder loop thread...")
    threading.Thread(target=reminder_loop, daemon=True).start()
    threading.Thread(target=update_tray_title, daemon=True).start()
    tray_icon.run()

if __name__ == "__main__":
    print("Hi, this is SoftEyeV1 App")
    # Initialize next break time
    next_break_time = time.time() + break_interval
    setup_tray()