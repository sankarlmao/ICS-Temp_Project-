import curses
import time
from pymodbus.client import ModbusTcpClient

ZONES = ["Hospital", "Mall", "Residential", "Industrial"]
SCADA_IP = "scada-server"

def safe_addstr(stdscr, y, x, string, attr=0):
    try:
        max_y, max_x = stdscr.getmaxyx()
        if y < max_y and x + len(string) < max_x:
            stdscr.addstr(y, x, string, attr)
    except:
        pass

def draw_dashboard(stdscr, zones_state):
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    
    if max_y < 12 or max_x < 50:
        stdscr.addstr(0, 0, "Terminal too small! Resize to at least 80x24.")
        stdscr.refresh()
        return

    safe_addstr(stdscr, 1, 2, "GRID CONTROL CONSOLE - HMI v1.2 (Manual Control Active)", curses.A_BOLD)
    safe_addstr(stdscr, 2, 2, "=======================================================", curses.A_BOLD)
    
    safe_addstr(stdscr, 4, 2, "Zone", curses.A_UNDERLINE)
    safe_addstr(stdscr, 4, 15, "Status", curses.A_UNDERLINE)
    safe_addstr(stdscr, 4, 25, "Key", curses.A_UNDERLINE)

    for idx, zone in enumerate(ZONES):
        y = 5 + idx
        state = "ONLINE " if zones_state[idx] else "OFFLINE"
        color = curses.color_pair(1) if zones_state[idx] else curses.color_pair(2)
        
        safe_addstr(stdscr, y, 2, zone)
        safe_addstr(stdscr, y, 15, state, color | curses.A_BOLD)
        safe_addstr(stdscr, y, 25, f"[{idx}]")

    safe_addstr(stdscr, 10, 2, "-------------------------------------------------------")
    safe_addstr(stdscr, 11, 2, "COMMANDS: Press [0-3] to TOGGLE. Press [q] to QUIT.")
    stdscr.refresh()

def main(stdscr):
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    stdscr.nodelay(True) # Make getch() non-blocking
    
    client = ModbusTcpClient(SCADA_IP, port=502)
    zones_state = [True] * 4 # Default state
    
    while True:
        try:
            if not client.connected:
                client.connect()
            
            # 1. Update the display
            rr = client.read_coils(0, count=4, device_id=1)
            if not rr.isError():
                zones_state = rr.bits[:4]
            
            draw_dashboard(stdscr, zones_state)
            
            # 2. Check for manual input frequently
            # We check 10 times during our 0.5s cycle for better responsiveness
            for _ in range(5):
                key = stdscr.getch()
                if key == ord('q'):
                    return
                elif ord('0') <= key <= ord('3'):
                    idx = int(chr(key))
                    new_state = not zones_state[idx]
                    client.write_coil(idx, new_state, device_id=1)
                    # Small break to prevent "double toggles"
                    time.sleep(0.1)
                    break 
                time.sleep(0.1)
                
        except Exception:
            # If server is restarting, wait and retry
            time.sleep(1)

if __name__ == "__main__":
    curses.wrapper(main)
