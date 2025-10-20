#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIELD VISUALISER v5 — GRID MODE (Technopunk ASCII)
See Field breathe:
- Real-time stats + pulse bar + sparkline + age histogram
- 2D moving word-cells on an ASCII grid (semantic Life vibe)
- User input: inject words as cells (cyan), simple commands
- Beeps on births/deaths/extinction
Works in Termux / macOS / Linux (ANSI escape codes)

Commands (type at prompt):
  clear        — clear user-injected word cache (visual highlight)
  speed N      — set refresh interval to N seconds (e.g., speed 2)
  list         — toggle list view under grid on/off
  help         — show commands
"""

import os
import re
import sys
import time
import math
import random
import sqlite3
import threading
from datetime import datetime
from typing import Dict, Tuple, List

# -------------------- CONFIG --------------------
DB_PATH = "/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3"
DB_PATH_LOCAL = "./field_test.sqlite3"
ACTIVE_DB = DB_PATH if os.path.exists(os.path.expanduser(DB_PATH)) else DB_PATH_LOCAL

# Grid size (tuned for phones & small terminals)
GRID_W = 54
GRID_H = 16

# How many cells to animate at once (keep it light)
MAX_RENDER_CELLS = 60

# Refresh seconds (can be changed via `speed N`)
REFRESH_SEC = 5

# -------------------- COLORS --------------------
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
COL = {
    "hi": "\033[92m",     # bright green
    "med": "\033[93m",    # yellow
    "lo": "\033[90m",     # gray
    "dead": "\033[91m",   # red
    "banner": "\033[95m", # magenta
    "user": "\033[96m",   # cyan
    "white": "\033[97m",
}

# Symbols
SYMB = {"hi": "█", "med": "▓", "lo": "░", "dead": "·", "user": "★"}

# Fallback vocabulary for non-user cells (as labels)
DICT_WORDS = [
    "resonance","emergence","chaos","pulse","shimmer","echo","spiral","field",
    "phase","quantum","flux","bloom","decay","nexus","drift","void","fracture",
]

# -------------------- RUNTIME STATE --------------------
_last_births = 0
_last_deaths = 0
_user_words: List[str] = []          # cache of words injected this session
_input_buf: List[str] = []           # typed lines
_running = True
_show_list = True                    # toggle list section
_positions: Dict[str, Tuple[float,float,float,float]] = {}  # cell_id -> (x, y, vx, vy)

random.seed(1337)

# -------------------- INPUT / WORD INJECTION --------------------
STOP_WORDS = {
    "the","is","are","was","were","be","been","being",
    "have","has","had","do","does","did","will","would",
    "could","should","may","might","must","can","am","i",
}

def extract_words(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z]{2,}", text.lower())
    return [w for w in words if w not in STOP_WORDS][:12]

def inject_words(conn: sqlite3.Connection, words: List[str]):
    """Insert/boost cells in field_cells for each word."""
    if not words: return []
    cur = conn.cursor()
    now = int(time.time())
    out = []
    for w in words:
        # Already alive?
        cur.execute("""
            SELECT cell_id, fitness FROM field_cells
            WHERE status='alive' AND cell_id LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f"%{w}%",))
        ex = cur.fetchone()
        if ex:
            cell_id, f0 = ex
            f1 = min(1.0, (f0 or 0.5) + 0.18)
            cur.execute("""
                UPDATE field_cells
                SET fitness=?, resonance_score=resonance_score+0.08
                WHERE cell_id=? AND status='alive'
            """, (f1, cell_id))
            out.append((w, "BOOSTED", f1))
        else:
            cell_id = f"user_{w}_{now}"
            fitness = random.uniform(0.62, 0.88)
            resonance = random.uniform(0.50, 0.82)
            cur.execute("""
                INSERT INTO field_cells (cell_id, age, resonance_score, fitness, status, timestamp)
                VALUES (?, 0, ?, ?, 'alive', ?)
            """, (cell_id, resonance, fitness, now))
            out.append((w, "BORN", fitness))
            if w not in _user_words:
                _user_words.append(w)
    conn.commit()
    return out

def input_thread():
    global _running
    while _running:
        try:
            line = input()
            if line.strip():
                _input_buf.append(line.strip())
        except (EOFError, KeyboardInterrupt):
            _running = False
            break

# -------------------- DB FETCH --------------------
def fetch_state(conn) -> Tuple[int,int,float,float,int,int]:
    cur = conn.cursor()
    cur.execute("""
        SELECT iteration, cell_count, avg_resonance, avg_age, births, deaths
        FROM field_state ORDER BY id DESC LIMIT 1
    """)
    row = cur.fetchone()
    return row if row else (0, 0, 0.0, 0.0, 0, 0)

def fetch_cells(conn, limit=MAX_RENDER_CELLS):
    cur = conn.cursor()
    cur.execute("""
        SELECT cell_id, age, resonance_score, fitness
        FROM field_cells
        WHERE status='alive'
        ORDER BY id DESC LIMIT ?
    """, (limit,))
    return cur.fetchall()

def fetch_history(conn, limit=16):
    cur = conn.cursor()
    cur.execute("""
        SELECT iteration, cell_count, avg_resonance
        FROM field_state
        ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    rows.reverse()
    return rows

# -------------------- DRAW HELPERS --------------------
def beep(n=1):
    try:
        sys.stdout.write('\a' * n)
        sys.stdout.flush()
    except Exception:
        pass

def pulse_bar(value: float, width=40) -> str:
    v = max(0.0, min(1.0, value))
    n = int(v * width)
    return f"{COL['hi']}{'█'*n}{RESET}{'░'*(width-n)}"

def sparkline(history) -> str:
    if not history: return ""
    pops = [h[1] for h in history]
    if not pops: return ""
    hi = max(pops) or 1
    chars = "▁▂▃▄▅▆▇█"
    out = []
    for p in pops:
        idx = int((p/hi) * (len(chars)-1)) if hi>0 else 0
        out.append(chars[idx])
    return COL["med"] + "".join(out) + RESET

def age_hist(cells) -> List[str]:
    if not cells: return []
    ages = [c[1] for c in cells]
    buckets = [0, 5, 10, 20, 30, 50, 1000]
    counts = [0]*(len(buckets)-1)
    for a in ages:
        for i in range(len(buckets)-1):
            if buckets[i] <= a < buckets[i+1]:
                counts[i]+=1; break
    mx = max(counts) or 1
    lines = ["Age Distribution:"]
    for i,c in enumerate(counts):
        bar = "█"*max(0, int(c/mx*18))
        lines.append(f"  {buckets[i]:>3}-{buckets[i+1]:<3}: {COL['hi']}{bar}{RESET} {c}")
    return lines

# -------------------- GRID PHYSICS --------------------
def _seed_vec(s: str) -> Tuple[float,float,float,float]:
    """Stable pseudo-random position & velocity from string id."""
    h = abs(hash(s))
    rx = (h % 997) / 997.0
    ry = ((h // 997) % 991) / 991.0
    # position
    x = rx * (GRID_W - 1)
    y = ry * (GRID_H - 1)
    # small velocity components (-0.35..0.35)
    vx = (0.7 * ((h % 29)/28.0 - 0.5))
    vy = (0.7 * (((h // 29) % 31)/30.0 - 0.5))
    return x, y, vx, vy

def _cell_style(cell_id: str, fitness: float) -> Tuple[str,str]:
    # user cell?
    for w in _user_words:
        if f"user_{w}_" in cell_id:
            return COL["user"], SYMB["user"]
    if fitness > 0.7:  return COL["hi"],  SYMB["hi"]
    if fitness > 0.5:  return COL["med"], SYMB["med"]
    if fitness > 0.3:  return COL["lo"],  SYMB["lo"]
    return COL["dead"], SYMB["dead"]

def update_positions(living_cells):
    """Ensure every live cell has a position. Update with gentle drift.
       Resonance damps velocity (higher resonance -> calmer motion)."""
    global _positions
    alive_ids = set()
    for cell_id, age, resonance, fitness in living_cells:
        alive_ids.add(cell_id)
        if cell_id not in _positions:
            _positions[cell_id] = _seed_vec(cell_id)
        x,y,vx,vy = _positions[cell_id]
        # damping from resonance (0..1): high resonance -> low motion
        damp = 0.35 + 0.65*(1.0 - max(0.0, min(1.0, resonance)))
        # tiny jitter to avoid static look
        jx = (random.random()-0.5)*0.15
        jy = (random.random()-0.5)*0.15
        x += (vx * 0.15 * damp) + jx
        y += (vy * 0.15 * damp) + jy

        # wrap-around torus
        if x < 0: x += GRID_W
        if x >= GRID_W: x -= GRID_W
        if y < 0: y += GRID_H
        if y >= GRID_H: y -= GRID_H
        _positions[cell_id] = (x,y,vx,vy)
    # prune dead
    for k in list(_positions.keys()):
        if k not in alive_ids:
            del _positions[k]

def render_grid(living_cells) -> List[str]:
    """Return list of strings (grid rows). If several occupy same cell, pick brighter."""
    grid = [[" "]*GRID_W for _ in range(GRID_H)]
    style = [[COL["lo"]]*GRID_W for _ in range(GRID_H)]

    # Update positions with motion
    update_positions(living_cells)

    for idx,(cell_id, age, resonance, fitness) in enumerate(living_cells):
        x,y,_,_ = _positions.get(cell_id, _seed_vec(cell_id))
        gx = int(round(x)) % GRID_W
        gy = int(round(y)) % GRID_H
        color, sym = _cell_style(cell_id, fitness)

        # Prefer "brighter" symbol if collision
        old = grid[gy][gx]
        if old in (" ", SYMB["lo"], "·"):
            grid[gy][gx] = sym
            style[gy][gx] = color
        elif old == SYMB["med"] and sym in (SYMB["hi"], SYMB["user"]):
            grid[gy][gx] = sym
            style[gy][gx] = color
        elif sym == SYMB["user"]:
            grid[gy][gx] = sym
            style[gy][gx] = color

    # Convert rows with colors
    rows = []
    for y in range(GRID_H):
        row = []
        for x in range(GRID_W):
            c = grid[y][x]
            if c == " ":
                row.append(DIM+"."+RESET)  # faint background
            else:
                row.append(style[y][x] + c + RESET)
        rows.append("".join(row))
    return rows

# -------------------- RENDER FULL FRAME --------------------
def render_frame(conn, cells, iteration, metrics, injected=None):
    global _last_births, _last_deaths, _show_list
    os.system("clear" if os.name != "nt" else "cls")

    cell_count, avg_res, avg_age, births, deaths = metrics

    # Audible events
    if births > _last_births: beep(1)
    if deaths > _last_deaths and cell_count>0: beep(2)
    if cell_count == 0: beep(3)
    _last_births, _last_deaths = births, deaths

    # Banner
    print(f"{BOLD}{COL['banner']}")
    print("┌" + "─"* (GRID_W+2) + "┐")
    title = " ⚡ ASYNC FIELD FOREVER (HYBRID) ⚡ "
    pad = max(0, (GRID_W+2 - len(title))//2)
    print("│" + " "*pad + title + " "*(GRID_W+2-len(title)-pad) + "│")
    print("└" + "─"* (GRID_W+2) + "┘" + RESET)

    # Metrics
    print(f"Iteration: {iteration} | Population: {cell_count}")
    print(f"Avg Resonance: {avg_res:0.3f} | Avg Age: {avg_age:0.1f}")
    print(f"Births: {births} | Deaths: {deaths}")

    # Pulse + history
    print("\nResonance Pulse:  " + pulse_bar(avg_res, width=GRID_W//2))
    hist = sparkline(fetch_history(conn, limit=min(2*GRID_W//5, 18)))
    if hist:
        print("Population History: " + hist)

    # Separator
    print("\n" + "─"*(GRID_W+2))

    # GRID
    grid_rows = render_grid(cells)
    # frame the grid
    print("╭" + "─"*GRID_W + "╮")
    for r in grid_rows:
        print("│" + r + "│")
    print("╰" + "─"*GRID_W + "╯")

    # Optional list view
    if _show_list:
        print("\nSRC  WORD                 FITNESS  RESONANCE  AGE")
        print("─"* (GRID_W+2))
        for i,(cell_id, age, resonance, fitness) in enumerate(cells[:20]):
            # label
            if cell_id.startswith("user_"):
                parts = cell_id.split("_")
                word = parts[1] if len(parts)>1 else cell_id[:12]
                col,sym = COL["user"], SYMB["user"]
                src = f"{col}*{RESET}"
            else:
                word = DICT_WORDS[i % len(DICT_WORDS)]
                col,sym = _cell_style(cell_id, fitness)
                src = f"{DIM}|{RESET}"
            print(f"{src}  {word:<20}   {fitness:>6.3f}    {resonance:>6.3f}    {age:<4}")

    # Age distribution
    lines = age_hist(cells)
    if lines:
        print("\n" + "\n".join(lines))

    # Show absorbed words this tick
    if injected:
        print(f"\n{COL['user']}Field absorbed:{RESET}")
        for w, act, f in injected:
            arrow = "★" if act == "BORN" else "↑"
            print(f"  {arrow} {w} — {act} (fitness {f:.2f})")

    # Footer + legend + prompt
    print("\n" + "─"*(GRID_W+2))
    print("Time:", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), "UTC")
    print(f"{DIM}Legend: {COL['user']}★ user{RESET}{DIM}, {COL['hi']}█ high{RESET}{DIM}, {COL['med']}▓ med{RESET}{DIM}, {COL['lo']}░ low{RESET}{DIM}, {COL['dead']}· dead{RESET}")
    print(f"{DIM}Commands: clear | speed N | list | help{RESET}")
    print(f"{COL['user']}Type to inject words (Ctrl+C to exit):{RESET}")
    print("> ", end="", flush=True)

# -------------------- MAIN LOOP --------------------
def process_command(txt: str) -> Tuple[bool,str]:
    """Return (handled, message)."""
    global REFRESH_SEC, _show_list, _user_words
    t = txt.strip().lower()
    if t == "help":
        return True, "Commands: clear | speed N | list | help"
    if t.startswith("speed"):
        parts = t.split()
        if len(parts)==2 and parts[1].isdigit():
            REFRESH_SEC = max(1, int(parts[1]))
            return True, f"speed set to {REFRESH_SEC}s"
        return True, "usage: speed N"
    if t == "list":
        _show_list = not _show_list
        return True, f"list view: {'ON' if _show_list else 'OFF'}"
    if t == "clear":
        _user_words.clear()
        return True, "user-word highlights cleared"
    return False, ""

def main():
    global _running
    # Banner
    print(f"{BOLD}{COL['banner']}FIELD VISUALISER v5 — GRID MODE{RESET}")
    print("Database:", ACTIVE_DB)
    print(f"{COL['user']}Tip: type a sentence — words become living cells!{RESET}")
    print("Starting in 2 seconds…\n")
    time.sleep(2)

    # Input thread
    t = threading.Thread(target=input_thread, daemon=True)
    t.start()

    conn = sqlite3.connect(ACTIVE_DB)

    try:
        while _running:
            injected = None
            # consume one input if present
            if _input_buf:
                line = _input_buf.pop(0)
                handled, msg = process_command(line)
                if handled:
                    # show a one-shot message above next frame
                    print(f"\n{DIM}{msg}{RESET}")
                    time.sleep(0.8)
                else:
                    words = extract_words(line)
                    if words:
                        injected = inject_words(conn, words)

            iteration, cell_count, avg_res, avg_age, births, deaths = fetch_state(conn)
            cells = fetch_cells(conn, limit=MAX_RENDER_CELLS)

            render_frame(conn, cells, iteration,
                         (cell_count, avg_res, avg_age, births, deaths),
                         injected)

            time.sleep(REFRESH_SEC)

    except KeyboardInterrupt:
        _running = False
        print(f"\n{COL['banner']}Visualizer stopped. Async field forever. 🧬⚡{RESET}\n")
    finally:
        conn.close()

if __name__ == "__main__":
    main()