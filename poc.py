import time
import csv
import psutil
import os
import logging
from pynput import keyboard, mouse
from datetime import datetime
import threading
import sys
import shutil

# Create results directory if it doesn't exist, or delete and recreate it
if os.path.exists("results"):
    shutil.rmtree("results")  # Delete the entire results folder
os.makedirs("results", exist_ok=True)

# Set up logging
logging.basicConfig(
    filename="results/activity_log.csv", level=logging.INFO, format="%(message)s"
)

# CSV Headers
with open("results/activity_log.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Timestamp", "Event", "Details"])


# Function to get active window title
def get_active_window():
    try:
        if os.name == "nt":  # Windows
            import win32gui

            window = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(window)
        elif os.name == "posix":  # macOS/Linux
            import subprocess

            if "Darwin" in os.uname().sysname:  # macOS
                result = subprocess.run(
                    [
                        "osascript",
                        "-e",
                        'tell application "System Events" to get name of (processes whose frontmost is true)',
                    ],
                    capture_output=True,
                    text=True,
                )
                return result.stdout.strip()
            else:  # Linux (X11-based)
                result = subprocess.run(
                    ["xdotool", "getwindowfocus", "getwindowname"],
                    capture_output=True,
                    text=True,
                )
                return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"


# Track keyboard activity
def on_key_press(key):
    try:
        key_str = key.char if hasattr(key, "char") else str(key)
        log_event("KeyPress", key_str)
        # Print key press to terminal in real-time
        print(f"KeyPress: {key_str}")
    except Exception as e:
        log_event("KeyPress", f"Error: {e}")
        print(f"KeyPress Error: {e}")


# Track mouse clicks
def on_click(x, y, button, pressed):
    action = "Pressed" if pressed else "Released"
    # Get screen resolution for context

    import screeninfo

    monitors = screeninfo.get_monitors()
    if monitors:
        primary = monitors[0]
        screen_info = f" (Screen: {primary.width}x{primary.height})"
    else:
        screen_info = ""

    click_details = f"{button} {action} at coordinates ({x}, {y}){screen_info}"
    log_event("MouseClick", click_details)
    # Print mouse click to terminal in real-time
    print(f"MouseClick: {click_details}")


# Log events to CSV
def log_event(event, details):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("results/activity_log.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, event, details])
    logging.info(f"{timestamp},{event},{details}")


# Track active application window changes
def monitor_active_window():
    last_window = None
    while True:
        active_window = get_active_window()
        if active_window and active_window != last_window:
            log_event("ActiveWindow", active_window)
            last_window = active_window
        time.sleep(2)


# Start tracking in background threads
def start_tracking():
    keyboard_listener = keyboard.Listener(on_press=on_key_press)
    mouse_listener = mouse.Listener(on_click=on_click)

    keyboard_listener.start()
    mouse_listener.start()

    window_thread = threading.Thread(target=monitor_active_window, daemon=True)
    window_thread.start()

    keyboard_listener.join()
    mouse_listener.join()


# Print all key logs from the CSV file
def print_key_logs():
    try:
        with open("results/activity_log.csv", "r", newline="") as f:
            reader = csv.reader(f)
            # Skip header row
            next(reader, None)

            print("\n--- Key Press Logs ---")
            print("Timestamp\t\tDetails")
            print("-" * 50)

            for row in reader:
                if len(row) >= 3 and row[1] == "KeyPress":
                    timestamp, _, details = row
                    print(f"{timestamp}\t{details}")

            print("-" * 50)
    except FileNotFoundError:
        print("No activity log file found.")
    except Exception as e:
        print(f"Error reading logs: {e}")


# Save key logs to a text file
def save_key_logs_to_txt():
    try:
        with open("results/activity_log.csv", "r", newline="") as f:
            reader = csv.reader(f)
            # Skip header row
            next(reader, None)

            # Create a text file with timestamp in filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            txt_filename = f"results/key_logs_{timestamp}.txt"

            with open(txt_filename, "w") as txt_file:
                txt_file.write("--- Key Press Logs ---\n")
                txt_file.write("Timestamp\t\tDetails\n")
                txt_file.write("-" * 50 + "\n")

                for row in reader:
                    if len(row) >= 3 and row[1] == "KeyPress":
                        timestamp, _, details = row
                        txt_file.write(f"{timestamp}\t{details}\n")

                txt_file.write("-" * 50 + "\n")

            print(f"Key logs saved to {txt_filename}")
    except FileNotFoundError:
        print("No activity log file found.")
    except Exception as e:
        print(f"Error saving logs: {e}")


# Save mouse clicks to a separate file
def save_mouse_clicks_to_txt():
    try:
        with open("results/activity_log.csv", "r", newline="") as f:
            reader = csv.reader(f)
            # Skip header row
            next(reader, None)

            # Create a text file with timestamp in filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            txt_filename = f"results/mouse_clicks_{timestamp}.txt"

            with open(txt_filename, "w") as txt_file:
                txt_file.write("--- Mouse Click Logs ---\n")
                txt_file.write("Timestamp\t\tDetails\n")
                txt_file.write("-" * 60 + "\n")

                for row in reader:
                    if len(row) >= 3 and row[1] == "MouseClick":
                        timestamp, _, details = row
                        txt_file.write(f"{timestamp}\t{details}\n")

                txt_file.write("-" * 60 + "\n")

            print(f"Mouse clicks saved to {txt_filename}")
    except FileNotFoundError:
        print("No activity log file found.")
    except Exception as e:
        print(f"Error saving logs: {e}")


# Run tracking
if __name__ == "__main__":
    print("Tracking keyboard, mouse, and active applications... Press CTRL+C to stop.")

    # Install screeninfo if not already installed
    try:
        import screeninfo
    except ImportError:
        print("Installing screeninfo package for better screen tracking...")
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "screeninfo"])
        print("Installation complete.")

    try:
        # Start the tracking first
        start_tracking()
    except KeyboardInterrupt:
        print("\nTracking stopped.")
        # Print and save logs when stopping
        print_key_logs()
        save_key_logs_to_txt()
        save_mouse_clicks_to_txt()  # Also save mouse clicks
        sys.exit(0)
