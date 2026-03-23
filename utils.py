#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  ICS Power Grid Simulator — Utility Module                   ║
║  Terminal colors, ASCII banners, formatting helpers           ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import datetime

# ─── ANSI Color Codes ────────────────────────────────────────

class Colors:
    """ANSI escape codes for terminal styling."""
    RESET      = "\033[0m"
    BOLD       = "\033[1m"
    DIM        = "\033[2m"
    UNDERLINE  = "\033[4m"
    BLINK      = "\033[5m"
    REVERSE    = "\033[7m"

    # Standard
    BLACK   = "\033[30m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"

    # Bright
    BRED    = "\033[91m"
    BGREEN  = "\033[92m"
    BYELLOW = "\033[93m"
    BBLUE   = "\033[94m"
    BMAGENTA= "\033[95m"
    BCYAN   = "\033[96m"
    BWHITE  = "\033[97m"

    # Backgrounds
    BG_RED     = "\033[41m"
    BG_GREEN   = "\033[42m"
    BG_YELLOW  = "\033[43m"
    BG_BLUE    = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN    = "\033[46m"
    BG_WHITE   = "\033[47m"
    BG_BLACK   = "\033[40m"

C = Colors  # shorthand alias


# ─── Box Drawing Characters ─────────────────────────────────

BOX_TL = "╔"
BOX_TR = "╗"
BOX_BL = "╚"
BOX_BR = "╝"
BOX_H  = "═"
BOX_V  = "║"
BOX_LT = "╠"
BOX_RT = "╣"
BOX_TT = "╦"
BOX_BT = "╩"
BOX_CROSS = "╬"

# Thin lines
THIN_H = "─"
THIN_V = "│"
THIN_TL = "┌"
THIN_TR = "┐"
THIN_BL = "└"
THIN_BR = "┘"


# ─── Terminal Helpers ────────────────────────────────────────

def get_terminal_width():
    """Get current terminal width."""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80

def clear_screen():
    """Clear the terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')

def timestamp():
    """Return current timestamp string."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ─── ASCII Art Banners ──────────────────────────────────────

MAIN_BANNER = f"""{C.BCYAN}{C.BOLD}
 ██████╗  ██████╗ ██╗    ██╗███████╗██████╗      ██████╗ ██████╗ ██╗██████╗ 
 ██╔══██╗██╔═══██╗██║    ██║██╔════╝██╔══██╗    ██╔════╝ ██╔══██╗██║██╔══██╗
 ██████╔╝██║   ██║██║ █╗ ██║█████╗  ██████╔╝    ██║  ███╗██████╔╝██║██║  ██║
 ██╔═══╝ ██║   ██║██║███╗██║██╔══╝  ██╔══██╗    ██║   ██║██╔══██╗██║██║  ██║
 ██║     ╚██████╔╝╚███╔███╔╝███████╗██║  ██║    ╚██████╔╝██║  ██║██║██████╔╝
 ╚═╝      ╚═════╝  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝     ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝{C.RESET}
{C.BYELLOW}  ╔══════════════════════════════════════════════════════════════════════════╗
  ║   ⚡  ICS / SCADA  CYBERSECURITY  SIMULATION  ENVIRONMENT  ⚡           ║
  ║          Industrial Control Systems — Vulnerability Lab                 ║
  ╚══════════════════════════════════════════════════════════════════════════╝{C.RESET}
"""

LOGIN_BANNER = f"""{C.BRED}{C.BOLD}
  ┌──────────────────────────────────────────────────────┐
  │    ⚠  AUTHORIZED PERSONNEL ONLY  ⚠                  │
  │    ICS-SCADA HMI Authentication Terminal             │
  │    Unauthorized access is a federal crime            │
  └──────────────────────────────────────────────────────┘{C.RESET}
"""

SCADA_BANNER = f"""{C.BGREEN}
  ┌──────────────────────────────────────────────────────┐
  │    ◈  SCADA MASTER CONTROL TERMINAL                  │
  │    Modbus Protocol Interface — Real-time Monitoring   │
  └──────────────────────────────────────────────────────┘{C.RESET}
"""

ALARM_BANNER = f"""{C.BRED}{C.BLINK}
  ╔══════════════════════════════════════════════════════╗
  ║  ◈◈◈  CRITICAL ALARM — SYSTEM ALERT  ◈◈◈           ║
  ╚══════════════════════════════════════════════════════╝{C.RESET}
"""


# ─── Formatting Functions ───────────────────────────────────

def box_header(title, color=C.BCYAN, width=70):
    """Create a double-line box header."""
    inner = width - 4
    title_padded = f" {title} ".center(inner)
    return (
        f"{color}{BOX_TL}{BOX_H * (width - 2)}{BOX_TR}\n"
        f"{BOX_V}{title_padded}{BOX_V}\n"
        f"{BOX_BL}{BOX_H * (width - 2)}{BOX_BR}{C.RESET}"
    )

def thin_box(lines, color=C.WHITE, width=70):
    """Create a thin-line box around content."""
    inner = width - 4
    result = f"{color}{THIN_TL}{THIN_H * (width - 2)}{THIN_TR}\n"
    for line in lines:
        padded = f" {line}".ljust(inner + 1)
        result += f"{THIN_V}{padded}{THIN_V}\n"
    result += f"{THIN_BL}{THIN_H * (width - 2)}{THIN_BR}{C.RESET}"
    return result

def status_indicator(label, value, status="normal"):
    """Create a colored status indicator line."""
    color_map = {
        "normal":   C.BGREEN,
        "warning":  C.BYELLOW,
        "critical": C.BRED,
        "offline":  C.DIM + C.RED,
        "info":     C.BCYAN,
    }
    color = color_map.get(status, C.WHITE)
    indicator = {
        "normal":   "●",
        "warning":  "◉",
        "critical": "◈",
        "offline":  "○",
        "info":     "◇",
    }.get(status, "●")
    return f"  {color}{indicator}{C.RESET} {C.BOLD}{label}:{C.RESET} {color}{value}{C.RESET}"

def progress_bar(value, max_val=100, width=30, color=C.BGREEN):
    """Create a terminal progress bar."""
    ratio = min(value / max_val, 1.0) if max_val > 0 else 0
    filled = int(width * ratio)
    bar = "█" * filled + "░" * (width - filled)
    pct = ratio * 100

    if pct > 90:
        bar_color = C.BRED
    elif pct > 70:
        bar_color = C.BYELLOW
    else:
        bar_color = color

    return f"{bar_color}[{bar}]{C.RESET} {pct:.1f}%"

def separator(char="─", width=70, color=C.DIM):
    """Create a separator line."""
    return f"{color}{char * width}{C.RESET}"

def menu_option(num, label, description="", color=C.BCYAN):
    """Format a menu option."""
    desc = f" {C.DIM}— {description}{C.RESET}" if description else ""
    return f"  {color}[{num}]{C.RESET} {C.BOLD}{label}{C.RESET}{desc}"

def table_row(columns, widths, color=C.WHITE):
    """Format a table row with fixed column widths."""
    cells = []
    for col, w in zip(columns, widths):
        cells.append(str(col).ljust(w)[:w])
    return f"{color}{THIN_V} {(' ' + THIN_V + ' ').join(cells)} {THIN_V}{C.RESET}"

def table_header(columns, widths, color=C.BCYAN):
    """Format a table header with separator."""
    header = table_row(columns, widths, color=f"{color}{C.BOLD}")
    sep_parts = []
    for w in widths:
        sep_parts.append(THIN_H * (w + 1))
    sep = f"{color}{THIN_V}{(THIN_H + '┼' + THIN_H).join(sep_parts)}{THIN_H}{THIN_V}{C.RESET}"
    top = f"{color}{THIN_TL}{(THIN_H + '┬' + THIN_H).join([THIN_H * (w + 1) for w in widths])}{THIN_H}{THIN_TR}{C.RESET}"
    return f"{top}\n{header}\n{sep}"

def table_footer(widths, color=C.BCYAN):
    """Format a table footer."""
    return f"{color}{THIN_BL}{(THIN_H + '┴' + THIN_H).join([THIN_H * (w + 1) for w in widths])}{THIN_H}{THIN_BR}{C.RESET}"

def typing_effect(text, delay=0.02):
    """Print text with typewriter effect."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def flash_message(message, color=C.BRED, times=3, delay=0.3):
    """Flash a message on screen."""
    for _ in range(times):
        sys.stdout.write(f"\r{color}{C.BOLD}  ⚠ {message}{C.RESET}")
        sys.stdout.flush()
        time.sleep(delay)
        sys.stdout.write(f"\r{' ' * (len(message) + 10)}")
        sys.stdout.flush()
        time.sleep(delay / 2)
    print(f"\r{color}{C.BOLD}  ⚠ {message}{C.RESET}")

def input_prompt(prompt_text, color=C.BYELLOW):
    """Styled input prompt."""
    return input(f"{color}  ▸ {prompt_text}: {C.RESET}")

def confirm_prompt(prompt_text):
    """Yes/No confirmation prompt."""
    response = input(f"{C.BYELLOW}  ▸ {prompt_text} (y/n): {C.RESET}").strip().lower()
    return response in ('y', 'yes')

def print_success(msg):
    print(f"  {C.BGREEN}✓ {msg}{C.RESET}")

def print_error(msg):
    print(f"  {C.BRED}✗ {msg}{C.RESET}")

def print_warning(msg):
    print(f"  {C.BYELLOW}⚠ {msg}{C.RESET}")

def print_info(msg):
    print(f"  {C.BCYAN}ℹ {msg}{C.RESET}")
