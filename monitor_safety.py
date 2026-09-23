import psutil
import time
import os
import signal
import datetime

# Configuration
CPU_THRESHOLD = 98.0
RAM_THRESHOLD = 95.0
SUSTAINED_SECONDS = 60 # Must be above CPU threshold for this many seconds
CHECK_INTERVAL = 1

def log_message(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    
    # Only print to terminal if it's a critical error (to keep terminal clean for progress bar)
    if "CRITICAL" in msg or "terminated" in msg:
        print(formatted)
        
    with open("logs/safety_monitor.log", "a") as f:
        f.write(formatted + "\n")

def find_training_process():
    """Finds the PID of train_advanced.py"""
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = p.info.get('cmdline')
            if cmdline and ('train_advanced.py' in cmdline or 'train_dispatcher.py' in cmdline) and 'python' in cmdline[0]:
                return p
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

def kill_process_tree(parent_pid):
    try:
        parent = psutil.Process(parent_pid)
        children = parent.children(recursive=True)
        for child in children:
            child.kill()
        parent.kill()
        log_message(f"Successfully killed process tree for PID {parent_pid}")
    except psutil.NoSuchProcess:
        pass

def main():
    os.makedirs("logs", exist_ok=True)
    log_message("Safety Monitor Started. Watching CPU and RAM...")
    
    high_cpu_counter = 0
    
    # Do an initial check to get baseline (psutil cpu_percent returns 0.0 on first call)
    psutil.cpu_percent(interval=1)
    
    while True:
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        
        # Monitor RAM (Immediate kill if > threshold)
        if ram >= RAM_THRESHOLD:
            log_message(f"CRITICAL: RAM usage at {ram}% (Threshold: {RAM_THRESHOLD}%). Commencing shutdown.")
            p = find_training_process()
            if p:
                kill_process_tree(p.pid)
                log_message("Training process terminated due to RAM exhaustion.")
            else:
                log_message("Training process not found. Is it running?")
                break
                
        # Monitor CPU (Sustained kill)
        if cpu >= CPU_THRESHOLD:
            high_cpu_counter += CHECK_INTERVAL
            if high_cpu_counter >= SUSTAINED_SECONDS:
                log_message(f"CRITICAL: CPU usage sustained at {cpu}% for {SUSTAINED_SECONDS}s. Commencing shutdown.")
                p = find_training_process()
                if p:
                    kill_process_tree(p.pid)
                    log_message("Training process terminated due to CPU lockup risk.")
                else:
                    log_message("Training process not found. Is it running?")
                break
        else:
            high_cpu_counter = 0
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
