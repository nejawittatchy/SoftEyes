import tkinter as tk
from tkinter import simpledialog
from PIL import Image, ImageTk, ImageFilter
import pyautogui
import threading
import time
import pystray
from pystray import MenuItem as item
import sys
import os

# Default settings
break_interval = 20 * 60  # 20 minutes in seconds
break_duration = 20       # 20 seconds

paused = False
snoozed_until = 0

def take_blurred_screenshot():
    print("Taking blurred screenshot")
    screenshot = pyautogui.screenshot()
    blurred = screenshot.filter(ImageFilter.GaussianBlur(radius=8))
    return blurred


def show_blur_overlay():
    print("Showing blur overlay")
    img = take_blurred_screenshot()
    
    overlay = tk.Tk()
    overlay.attributes('-fullscreen', True)
    overlay.attributes('-topmost', True)
    overlay.configure(bg='black')
    
    # Convert image to Tkinter format
    tk_img = ImageTk.PhotoImage(img)
    label = tk.Label(overlay, image=tk_img)
    label.place(x=0, y=0, relwidth=1, relheight=1)
    
    # Message
    text = tk.Label(overlay, text="Rest your eyes 🌿\nLook 20 feet away", 
                    fg='white', bg='black', font=('Helvetica', 32), justify='center')
    text.place(relx=0.5, rely=0.5, anchor='center')
    
    # Destroy after break_duration
    overlay.after(break_duration * 1000, overlay.destroy)
    overlay.mainloop()


def reminder_loop():
    print("Starting reminder loop")
    global paused, snoozed_until
    while True:
        time.sleep(1)
        if paused or time.time() < snoozed_until:
            continue
        time.sleep(break_interval)
        if not paused and time.time() >= snoozed_until:
            threading.Thread(target=show_blur_overlay).start()

# --- Control Functions ---

def toggle_pause(icon, item):
    print("Toggling pause")
    global paused
    paused = not paused
    icon.update_menu()

def snooze(icon, item):
    print("Snoozing for 1 hour")
    global snoozed_until
    snoozed_until = time.time() + 3600  # 1 hour

def open_settings(icon, item):
    print("Opening settings dialog")
    global break_interval, break_duration

    root = tk.Tk()
    root.withdraw()

    new_interval = simpledialog.askinteger("Settings", "Break Interval (minutes):", initialvalue=break_interval // 60, minvalue=1)
    new_duration = simpledialog.askinteger("Settings", "Break Duration (seconds):", initialvalue=break_duration, minvalue=5)

    if new_interval:
        break_interval = new_interval * 60
    if new_duration:
        break_duration = new_duration

    root.destroy()

def quit_app(icon, item):
    print("Quitting application")
    icon.stop()
os._exit(0)

def setup_tray():
    print("Setting up system tray icon")
    icon_image = Image.new('RGB', (64, 64), color='black')
    menu = (
        item(lambda icon, item: "Pause" if not paused else "Resume", toggle_pause),
        item('Snooze 1 Hour', snooze),
        item('Settings', open_settings),
        item('Quit', quit_app)
    )

    tray_icon = pystray.Icon("SoftEyes", icon_image, "SoftEyes", menu)
    threading.Thread(target=reminder_loop, daemon=True).start()
    tray_icon.run()

if __name__ == "__main__":
    print("Starting SoftEyes application")
    setup_tray()