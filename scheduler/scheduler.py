import time
import sys
from producer import produce
from database import get_router_info

def scheduler():
    INTERVAL = 10.0
    next_run = time.monotonic()
    count = 0

    while True:
        now = time.time()
        now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
        ms = int((now % 1) * 1000)
        now_str_with_ms = f"{now_str}.{ms:03d}"
        print(f"[{now_str_with_ms}] run #{count}", flush=True)

        try:
            for data in get_router_info():
                router_ip = data.get("ip") or data.get("host")
                username = data.get("username")
                password = data.get("password")

                produce(router_ip, username, password)
        except Exception as e:
            print(f"Error fetching/producing router data: {e}", flush=True)
            time.sleep(3)
            
        count += 1
        next_run += INTERVAL
        time.sleep(max(0.0, next_run - time.monotonic()))

if __name__ == "__main__":
    print("Initializing Scheduler service...", flush=True)
    
    # Wait for RabbitMQ/Mongo dependencies to stabilize before launching scheduler
    time.sleep(5) 
    
    try:
        scheduler()
    except Exception as e:
        print(f"Fatal error in scheduler loop: {e}", file=sys.stderr, flush=True)
        sys.exit(1)