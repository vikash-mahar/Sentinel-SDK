import time
import re
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from graph import repair_code

# --- CONFIGURATION (Paths ko apne hisab se ek baar check kar lo) ---
# Agar tum sentinel_agent folder mein ho, toh app-to-fix bahar hoga.
LOG_DIR = os.path.abspath("../app-to-fix/src/logs") 
LOG_FILE = os.path.join(LOG_DIR, "error.log")

class SentinelHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # Full path check karte hain taaki galti na ho
        if os.path.abspath(event.src_path) == os.path.abspath(LOG_FILE):
            print("🔍 Log file modification detected...")
            self.process_latest_error()

    def process_latest_error(self):
        try:
            with open(LOG_FILE, "r") as f:
                content = f.read()
                if not content: return
                
                # Get the last error block
                errors = content.strip().split("---")
                if len(errors) < 2: return # Not enough content
                
                last_error = errors[-2].strip()
                
                # Extract file path using Regex
                file_match = re.search(r"FILE: (.+)", last_error)
                if file_match:
                    file_path = file_match.group(1).strip()
                    print(f"🚨 Crash detected in: {file_path}")
                    # AI Repair logic call
                    repair_code(last_error, file_path)
        except Exception as e:
            print(f"⚠️ Error reading log file: {e}")

if __name__ == "__main__":
    if not os.path.exists(LOG_DIR):
        print(f"❌ Error: Directory {LOG_DIR} nahi mil rahi! Path check karo.")
    else:
        observer = Observer()
        # Hum poore folder ko monitor kar rahe hain
        observer.schedule(SentinelHandler(), path=LOG_DIR, recursive=False)
        observer.start()
        print(f"🕵️ Sentinel Watchdog is active.")
        print(f"👀 Monitoring: {LOG_FILE}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()