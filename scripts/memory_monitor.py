#!/usr/bin/env python3
"""
Monitor memory usage during processing.
"""

import psutil
import os
import time

# ANSI color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def monitor_memory(interval=1.0):
    """Monitor memory usage at regular intervals."""
    process = psutil.Process(os.getpid())
    print(f"{GREEN}[MONITOR] Starting memory monitoring (PID: {os.getpid()}){RESET}")
    print(f"{'Time':<10} {'RSS (MB)':<12} {'% RAM':<8} {'CPU %':<8}")
    print("-" * 50)

    try:
        while True:
            mem = process.memory_info()
            cpu = process.cpu_percent(interval=0.1)

            rss_mb = mem.rss / 1024 / 1024
            percent = process.memory_percent()

            print(f"{time.strftime('%H:%M:%S'):<10} "
                  f"{rss_mb:<12.2f} "
                  f"{percent:<8.2f} "
                  f"{cpu:<8.2f}")

            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n{GREEN}[MONITOR] Monitoring stopped.{RESET}")

if __name__ == "__main__":
    monitor_memory()
