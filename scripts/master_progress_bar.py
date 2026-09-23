import redis
import time
import sys

def draw_bar(percentage, length=30):
    filled = int(length * percentage)
    bar = '█' * filled + '-' * (length - filled)
    return f"|{bar}| {percentage*100:.1f}%"

def main():
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    regions = ["Northeast", "Northwest", "Southeast", "Southwest"]
    
    # Wait for regions to start pushing
    print("Waiting for regional dispatchers to initialize...")
    time.sleep(5)
    
    # Hide cursor
    sys.stdout.write('\033[?25l')
    
    try:
        while True:
            output_lines = ["\033[K" + "=== Hierarchical Regional Dispatcher Training ==="]
            all_done = True
            
            for region in regions:
                val = r.get(f"progress:{region}")
                if val:
                    current, total = map(int, val.split('/'))
                    percentage = current / total
                    output_lines.append(f"\033[KRegion {region:<10}: {draw_bar(percentage)} ({current}/{total})")
                    if current < total:
                        all_done = False
                else:
                    output_lines.append(f"\033[KRegion {region:<10}: Waiting for data...")
                    all_done = False
                    
            # Move cursor up by the number of lines we print, then print
            # (We don't move up on the very first iteration, so we use \r and \033[F)
            sys.stdout.write('\r' + '\n'.join(output_lines))
            sys.stdout.write(f'\033[{len(output_lines)-1}A')
            sys.stdout.flush()
            
            if all_done:
                # Move cursor down past the bars so the terminal prompt doesn't overwrite it
                sys.stdout.write(f'\033[{len(output_lines)}B\n')
                print("All regional trainings completed successfully!")
                break
                
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        pass
    finally:
        # Show cursor
        sys.stdout.write('\033[?25h\n')

if __name__ == "__main__":
    main()
