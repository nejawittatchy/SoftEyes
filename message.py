import tkinter as tk
from tkinter import messagebox
from pystray import Icon, MenuItem as item
from PIL import Image
import threading
import time

def show_message():
    print("Initializing Tkinter...")
    root = tk.Tk()
    print("Tkinter initialized. Hiding main window...")
    root.withdraw()  # Hide the main window
    print("Displaying message box...")
    messagebox.showinfo("Message", "Hi")
    print("Message box closed. Destroying Tkinter root...")
    root.destroy()
    print("Tkinter root destroyed.")

def on_quit(icon, item):
    icon.stop()

def setup_tray():
    print("Setting up tray...")
    image = Image.new('RGB', (64, 64), color='black')
    print("Tray icon created.")
    icon = Icon("MessageApp", image, "MessageApp", menu=(item("Quit", on_quit),))
    print("Starting tray application...")
    icon.run()
    print("Tray application stopped.")

if __name__ == "__main__":
    print("Hi, this is Message App")
    tray_thread = threading.Thread(target=setup_tray, daemon=True)
    tray_thread.start()

    try:
        for i in range(10, 0, -1):
            print(f"Tray will stay active for {i} seconds...")
            time.sleep(1)
        print("Destroying tray and terminating application after countdown...")
        tray_thread.join(timeout=1)  # Ensure the tray thread finishes
        exit(0)  # Terminate the application
    except KeyboardInterrupt:
        print("Exiting program...")
        exit(0)