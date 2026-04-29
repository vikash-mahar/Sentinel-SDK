import time
import re
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from graph import repair_code, optimize_code 

# Paths ko normalize kar lete hain taaki OS ka koi chakkar na rahe
LOG_DIR = os.path.abspath("../app-to-fix/src/logs") 
ERROR_LOG = os.path.normpath(os.path.join(LOG_DIR, "error.log"))
PERF_LOG = os.path.normpath(os.path.join(LOG_DIR, "performance.log"))

class SentinelHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # Agar directory modify hui hai toh skip karo
        if event.is_directory:
            return

        # Current modified file ka absolute path
        src_path = os.path.abspath(event.src_path)
        
        # 1. Check for Crashes
        if src_path == os.path.abspath(ERROR_LOG):
            print("\n🔍 [EVENT] Crash Log Change Detected...")
            self.process_latest_error()
            
        # 2. Check for Slowness
        elif src_path == os.path.abspath(PERF_LOG): 
            print("\n⚡ [EVENT] Performance Log Change Detected...")
            self.process_performance_issue()

    def process_latest_error(self):
        try:
            # File read karne se pehle thoda wait (taaki OS file lock release kar de)
            time.sleep(0.5) 
            with open(ERROR_LOG, "r") as f:
                content = f.read().strip().split("---")
                if len(content) < 2: return
                last_error = content[-2].strip()
                
                file_match = re.search(r"FILE: (.+)", last_error)
                if file_match:
                    file_path = file_match.group(1).strip()
                    print(f"🚨 Repairing Crash in: {file_path}")
                    repair_code(last_error, file_path)
        except Exception as e:
            print(f"⚠️ Error processing crash: {e}")

    def process_performance_issue(self):
        try:
            time.sleep(0.5)
            with open(PERF_LOG, "r") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
                if not lines: return
                
                last_perf_issue = lines[-1]
                # Target file ka path sahi hona chahiye
                target_file = os.path.abspath("../app-to-fix/src/server.js") 
                
                print(f"🚀 Sentinel is analyzing performance: {last_perf_issue}")
                optimize_code(last_perf_issue, target_file)
        except Exception as e:
            print(f"⚠️ Error processing performance: {e}")

if __name__ == "__main__":
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    for f in [ERROR_LOG, PERF_LOG]:
        if not os.path.exists(f):
            with open(f, 'w') as dummy: pass

    observer = Observer()
    # Path normalize karke monitor karo
    observer.schedule(SentinelHandler(), path=LOG_DIR, recursive=False)
    observer.start()
    
    print("\n" + "="*40)
    print("🕵️  SENTINEL WATCHDOG ACTIVE (Dual-Mode)")
    print(f"📁 Logs Folder: {LOG_DIR}")
    print(f"🚨 Error File: {os.path.basename(ERROR_LOG)}")
    print(f"⚡ Perf File:  {os.path.basename(PERF_LOG)}")
    print("="*40 + "\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()