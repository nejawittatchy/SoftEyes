# This file is created to test the tray functionality of the SoftEyesApp.

from softeyes import setup_tray
from pystray import Icon, MenuItem as item
from PIL import Image
import threading
import time

print("Hi, this is Test App")

def on_quit(icon, item):
    icon.stop()

def setup_tray():
    print("Setting up tray...")
    image = Image.new('RGB', (64, 64), color='black')
    print("Tray icon created.")
    icon = Icon("TestApp", image, "TestApp", menu=(item("Quit", on_quit),))
    print("Starting tray application...")
    threading.Thread(target=icon.run, daemon=True).start()
    print("Tray application running in a separate thread.")

if __name__ == "__main__":
    print("Starting test for tray icon setup")
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