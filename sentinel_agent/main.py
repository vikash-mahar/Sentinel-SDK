import time
import re
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
# graph.py se naye wrapper functions import ho rahe hain
from graph import repair_code, optimize_code 

# --- CONFIGURATION ---
LOG_DIR = os.path.abspath("../app-to-fix/src/logs") 
ERROR_LOG = os.path.normpath(os.path.join(LOG_DIR, "error.log"))
PERF_LOG = os.path.normpath(os.path.join(LOG_DIR, "performance.log"))

class SentinelHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return

        src_path = os.path.abspath(event.src_path)
        
        # 1. Check for Crashes (error.log)
        if src_path == os.path.abspath(ERROR_LOG):
            print("\n🚨 [DETECTOR] Crash detected in error.log!")
            self.process_latest_error()
            
        # 2. Check for Slowness (performance.log)
        elif src_path == os.path.abspath(PERF_LOG): 
            print("\n⚡ [DETECTOR] Performance issue detected!")
            self.process_performance_issue()

    def process_latest_error(self):
        try:
            time.sleep(1) # OS ko file write finish karne do
            with open(ERROR_LOG, "r") as f:
                content = f.read().strip().split("---")
                if len(content) < 2: return
                last_error = content[-2].strip()
                
                file_match = re.search(r"FILE: (.+)", last_error)
                if file_match:
                    file_path = file_match.group(1).strip()
                    # Yeh ab graph.py ke AGENTS ko trigger karega
                    repair_code(last_error, file_path)
        except Exception as e:
            print(f"⚠️ Error processing crash: {e}")

    def process_performance_issue(self):
        try:
            time.sleep(1)
            with open(PERF_LOG, "r") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
                if not lines: return
                
                last_perf_issue = lines[-1]
                target_file = os.path.abspath("../app-to-fix/src/server.js") 
                
                # Yeh ab graph.py ke AGENTS ko optimization ke liye trigger karega
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
    observer.schedule(SentinelHandler(), path=LOG_DIR, recursive=False)
    observer.start()
    
    print("\n" + "="*50)
    print("🕵️  SENTINEL MULTI-AGENT SYSTEM ACTIVE")
    print("🤖 Roles: Scout, Architect, Reviewer are Ready!")
    print(f"👀 Monitoring: {LOG_DIR}")
    print("="*50 + "\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()