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

# Application info
APP_VERSION = "1.0.0"
APP_WEBSITE = "https://github.com/nejawittatchy/SoftEyes"
APP_EMAIL = "nejawittatchy@example.com"

# Default settings
break_interval = 20 * 60  # 1 minute in seconds for testing
break_duration = 20       # 5 seconds for testing

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

def take_blurred_screenshot():
    print("DEBUG: Taking blurred screenshot...")
    screenshot = pyautogui.screenshot()
    blurred = screenshot.filter(ImageFilter.GaussianBlur(radius=8))
    print("DEBUG: Screenshot taken and blurred successfully")
    return blurred

def show_blur_overlay():
    print("DEBUG: Showing blur overlay...")
    img = take_blurred_screenshot()
    overlay = tk.Tk()
    overlay.attributes('-fullscreen', True)
    overlay.attributes('-topmost', True)
    overlay.configure(bg='black')

    print("DEBUG: Setting up overlay window...")
    # Convert image to Tkinter format
    tk_img = ImageTk.PhotoImage(img)
    label = tk.Label(overlay, image=tk_img)
    label.place(x=0, y=0, relwidth=1, relheight=1)

    # Message
    text = tk.Label(overlay, text="Rest your eyes 🌿\nLook 20 feet away", 
                    fg='white', bg='black', font=('Helvetica', 32), justify='center')
    text.place(relx=0.5, rely=0.5, anchor='center')

    print(f"DEBUG: Overlay will close in {break_duration} seconds")
    # Destroy after break_duration
    overlay.after(break_duration * 1000, overlay.destroy)
    overlay.mainloop()

def update_tray_title():
    global next_break_time, tray_icon
    while True:
        if tray_icon and not paused:
            if time.time() >= snoozed_until:  # Only update if not snoozed
                remaining = max(0, next_break_time - time.time())
                minutes = int(remaining // 60)
                # Update icon with just the minutes
                new_icon = create_tray_image(str(minutes))
                tray_icon.icon = new_icon
            else:
                # Show remaining snooze time
                remaining = max(0, snoozed_until - time.time())
                minutes = int(remaining // 60)
                new_icon = create_tray_image(f"S{minutes}")
                tray_icon.icon = new_icon
        elif tray_icon and paused:
            new_icon = create_tray_image("P")
            tray_icon.icon = new_icon
        time.sleep(1)

def reminder_loop():
    global paused, snoozed_until, next_break_time
    print("DEBUG: Starting reminder loop...")
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
        time.sleep(break_interval)
        
        if not paused and time.time() >= snoozed_until:
            print("DEBUG: Triggering break reminder")
            threading.Thread(target=show_blur_overlay).start()

# --- Control Functions ---

def toggle_pause(icon, item):
    global paused
    paused = not paused
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

def open_settings(icon, item):
    global break_interval, break_duration
    print("DEBUG: Opening settings dialog...")

    root = tk.Tk()
    root.withdraw()

    new_interval = simpledialog.askinteger("Settings", "Break Interval (minutes):", initialvalue=break_interval // 60, minvalue=1)
    new_duration = simpledialog.askinteger("Settings", "Break Duration (seconds):", initialvalue=break_duration, minvalue=5)

    if new_interval:
        break_interval = new_interval * 60
        print(f"DEBUG: Break interval updated to {new_interval} minutes")
    if new_duration:
        break_duration = new_duration
        print(f"DEBUG: Break duration updated to {new_duration} seconds")

    # Add startup option
    add_startup = messagebox.askyesno("Settings", "Start SoftEyes with Windows?")
    if add_startup:
        if add_to_startup():
            messagebox.showinfo("Success", "SoftEyes will now start with Windows")
        else:
            if not getattr(sys, 'frozen', False):
                messagebox.showwarning("Note", "Startup feature only works with the executable version")
            else:
                messagebox.showerror("Error", "Failed to add to startup")

    root.destroy()


def open_about(icon, item):
    """Show an About dialog with developer details and clickable links."""
    about_window = tk.Toplevel()
    about_window.title("About SoftEyes")
    about_window.geometry("400x500")
    about_window.resizable(False, False)
    
    # Style
    style = ttk.Style()
    style.configure("Link.TLabel", foreground="blue", cursor="hand2")
    
    # Create a main frame with padding
    main_frame = ttk.Frame(about_window, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_label = ttk.Label(main_frame, text="SoftEyes", font=("Helvetica", 24, "bold"))
    title_label.pack(pady=(0, 10))
    
    version_label = ttk.Label(main_frame, text=f"Version {APP_VERSION}")
    version_label.pack()
    
    # Description
    desc_text = "Your friendly eye care companion that helps\nremind you to take regular breaks."
    desc_label = ttk.Label(main_frame, text=desc_text, justify=tk.CENTER)
    desc_label.pack(pady=(10, 20))
    
    # Developer info with clickable links
    dev_frame = ttk.Frame(main_frame)
    dev_frame.pack(fill=tk.X, pady=(0, 20))
    
    ttk.Label(dev_frame, text="Developer: Neja Wittatchy").pack()
    
    # Email link
    email_label = ttk.Label(dev_frame, text=APP_EMAIL, style="Link.TLabel")
    email_label.pack()
    email_label.bind("<Button-1>", lambda e: webbrowser.open(f"mailto:{APP_EMAIL}"))
    
    # Website link
    website_label = ttk.Label(dev_frame, text="Visit Website", style="Link.TLabel")
    website_label.pack()
    website_label.bind("<Button-1>", lambda e: webbrowser.open(APP_WEBSITE))
    
    # Add a separator
    ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
    
    # Features
    features_text = """
    Key Features:
    • Smart break reminders every 20 minutes
    • Gentle screen blur during breaks
    • Customizable break duration
    • System tray integration
    • Startup with Windows option
    """
    features_label = ttk.Label(main_frame, text=features_text, justify=tk.LEFT)
    features_label.pack(pady=10)
    
    # Close button at bottom
    ttk.Button(main_frame, text="Close", command=about_window.destroy).pack(pady=(20, 0))
    
    # Center the window on screen
    about_window.update_idletasks()
    width = about_window.winfo_width()
    height = about_window.winfo_height()
    x = (about_window.winfo_screenwidth() // 2) - (width // 2)
    y = (about_window.winfo_screenheight() // 2) - (height // 2)
    about_window.geometry(f"+{x}+{y}")
    
    # Make window modal
    about_window.transient(about_window.master)
    about_window.grab_set()
    about_window.focus_set()

def quit_app(icon, item):
    print("DEBUG: Quitting application...")
    icon.stop()
    os._exit(0)

def setup_tray():
    global tray_icon
    print("DEBUG: Setting up tray...")
    # Create initial icon with "0" minutes
    image = create_tray_image("0")
    print("DEBUG: Tray icon created.")
    menu = (
        item(lambda item: "Pause" if not paused else "Resume", toggle_pause),
        item('Snooze 1 Hour', snooze),
        item('About', open_about),
        item('Settings', open_settings),
        item('Quit', quit_app)
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