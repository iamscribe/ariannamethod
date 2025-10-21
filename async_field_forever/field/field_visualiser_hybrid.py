#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIELD VISUALISER v7.5 — HYBRID + WORD SPRITES (Termux/macOS/Linux)

- One banner (no duplicates), strict centering & padding
- Stable header line wrapping (no "Births"/"Deaths" overflow)
- Grid perfectly centered; input prompt at left
- Words drift on the grid (replaces stars). Source-aware coloring:
    ★ user words (cyan), ◆ repo words (blue), █/▓/▒ organic (green→gray)
- Pulse bar + history sparkline
- Optional repo monitor; interactive word injection to DB

DB tables expected:
  field_state(iteration, cell_count, avg_resonance, avg_age, births, deaths)
  field_cells(id, timestamp, cell_id, age, resonance_score, entropy, perplexity, fitness, architecture, status)
"""

import os
import re
import sys
import math
import time
import sqlite3
import random
import shutil
import threading
from datetime import datetime
from hashlib import blake2b
from pathlib import Path
from typing import List, Tuple, Dict, Optional

# -------------------------- CONFIG --------------------------

DB_PATH = "/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3"
DB_PATH_LOCAL = "./resonance.sqlite3"             # fallback for desktop
ACTIVE_DB = DB_PATH if os.path.exists(os.path.expanduser(DB_PATH)) else DB_PATH_LOCAL

# repo monitor (optional)
REPO_PATH = Path(__file__).resolve().parents[2] if len(Path(__file__).parents) >= 2 else Path.cwd()
ENABLE_REPO_MONITOR = True

# UI
FRAME_DT   = 0.18            # display refresh tick (word drift)
UI_REFRESH = 5.0             # DB poll / metrics refresh
H_MARGIN   = 2               # horizontal safe margin
V_MARGIN   = 1

# flags
ENABLE_COLORS = True
ENABLE_BREATH = True
ENABLE_DRIFT  = True

# -------------------------- COLORS --------------------------

RESET = "\033[0m" if ENABLE_COLORS else ""
BOLD  = "\033[1m" if ENABLE_COLORS else ""
DIM   = "\033[2m" if ENABLE_COLORS else ""

C = lambda code: code if ENABLE_COLORS else ""

COL = {
    "banner": C("\033[95m"),      # magenta
    "user":   C("\033[96m"),      # cyan
    "repo":   C("\033[94m"),      # blue
    "high":   C("\033[92m"),      # bright green
    "med":    C("\033[93m"),      # yellow
    "low":    C("\033[90m"),      # gray
    "dead":   C("\033[91m"),      # red
    "text":   C("\033[97m"),
}

SYM = {
    "user": "★",
    "repo": "◆",
    "high": "█",
    "med":  "▓",
    "low":  "▒",
    "min":  "░",
    "dead": "·",
}

# -------------------------- STATE --------------------------

_user_words : List[str] = []
_repo_words : List[str] = []
_input_buffer: List[str] = []
_running = True
_breath   = 0.0
_last_births = 0
_last_deaths = 0

# ---------------------- SAFE TERMINAL -----------------------

def term_size() -> Tuple[int,int]:
    try:
        w,h = shutil.get_terminal_size((80, 24))
    except Exception:
        w,h = 80,24
    # minimums
    w = max(60, w)
    h = max(22, h)
    return w,h

def clear_screen():
    # hard reset avoid ghost frames on Termux
    sys.stdout.write("\033c")
    sys.stdout.flush()

def center_x(inner_w: int, total_w: int) -> int:
    return max(H_MARGIN, (total_w - inner_w)//2)

def crop(s: str, w: int) -> str:
    return s if len(s) <= w else s[:max(0,w-1)] + "…"

# ---------------------- REPO MONITOR ------------------------

def try_init_repo_monitor():
    if not ENABLE_REPO_MONITOR:
        return None
    try:
        sys.path.insert(0, str(REPO_PATH / "arianna_core_utils"))
        from repo_monitor import RepoMonitor
        return RepoMonitor(repo_path=REPO_PATH)
    except Exception:
        return None

def extract_words(text: str) -> List[str]:
    stop = {
        "the","is","are","was","were","be","been","being",
        "have","has","had","do","does","did","will","would",
        "could","should","may","might","must","can","this","that",
        "with","from","for","not","but","and","or","into","onto",
        "over","under","between","within","out","your","you","our"
    }
    words = re.findall(r"[a-zA-Z]{2,}", text.lower())
    return [w for w in words if w not in stop and len(w)>2]

def fetch_repo_words(monitor) -> List[str]:
    if not monitor: return []
    try:
        changes = monitor.fetch_repo_context(limit=5)
        bag = []
        for ch in changes:
            bag.extend(extract_words(ch.get("content",""))[:3])
        # unique, keep order
        seen, uniq = set(), []
        for w in bag:
            if w not in seen:
                seen.add(w); uniq.append(w)
            if len(uniq) >= 10: break
        return uniq
    except Exception:
        return []

# ------------------------ DB LAYER --------------------------

def db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(ACTIVE_DB)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def fetch_state(conn) -> Tuple[int,int,float,float,int,int]:
    cur = conn.cursor()
    cur.execute("""
      SELECT iteration, cell_count, avg_resonance, avg_age, births, deaths
      FROM field_state ORDER BY id DESC LIMIT 1
    """)
    row = cur.fetchone()
    return row if row else (0,0,0.0,0.0,0,0)

def fetch_cells(conn, limit: int) -> List[Tuple[str,int,float,float]]:
    cur = conn.cursor()
    cur.execute("""
      SELECT cell_id, COALESCE(age,0), COALESCE(resonance_score,0.0), COALESCE(fitness,0.0)
      FROM field_cells WHERE status='alive' ORDER BY id DESC LIMIT ?
    """, (limit,))
    return cur.fetchall()

def fetch_history(conn, limit: int=20) -> List[Tuple[int,int,float]]:
    cur = conn.cursor()
    cur.execute("""
      SELECT iteration, cell_count, avg_resonance
      FROM field_state ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    rows.reverse()
    return rows

def inject_words(conn, words: List[str], source="user") -> List[Tuple[str,str,float,str]]:
    cur = conn.cursor()
    ts = int(time.time())
    out = []
    for w in words:
        # try boost existing
        cur.execute("""
          SELECT cell_id, COALESCE(fitness,0.6) FROM field_cells
          WHERE status='alive' AND cell_id LIKE ? ORDER BY id DESC LIMIT 1
        """, (f"%{w}%",))
        hit = cur.fetchone()
        if hit:
            cid, old = hit
            new = min(1.0, old + 0.15)
            cur.execute("UPDATE field_cells SET fitness=? WHERE cell_id=? AND status='alive'", (new, cid))
            out.append((w, "BOOSTED", new, source))
        else:
            cid = f"{source}_{w}_{ts}"
            fit = random.uniform(0.65,0.85) if source=="repo" else random.uniform(0.6,0.9)
            res = random.uniform(0.5,0.8)
            cur.execute("""
              INSERT INTO field_cells(cell_id, age, resonance_score, fitness, status, timestamp)
              VALUES (?, 0, ?, ?, 'alive', ?)
            """, (cid, res, fit, ts))
            out.append((w, "BORN", fit, source))
            if source=="user": _user_words.append(w)
            else: _repo_words.append(w)
    conn.commit()
    return out

# ---------------------- INPUT THREAD ------------------------

def input_thread():
    global _running, _input_buffer
    while _running:
        try:
            line = input()
            if line.strip():
                _input_buffer.append(line.strip())
        except (EOFError, KeyboardInterrupt):
            _running = False
            break

# ------------------------- RENDER ---------------------------

def banner(lines: List[str], width: int) -> List[str]:
    inner = width - 2
    top = f"{COL['banner']}{BOLD}╔" + "═"*inner + f"╗{RESET}"
    bot = f"{COL['banner']}{BOLD}╚" + "═"*inner + f"╝{RESET}"
    body = []
    for s in lines:
        s = crop(s, inner)
        body.append(f"{COL['banner']}{BOLD}║{RESET}" + s.center(inner) + f"{COL['banner']}{BOLD}║{RESET}")
    return [top] + body + [bot]

def spark(history: List[Tuple[int,int,float]]) -> str:
    if len(history)<2: return ""
    pops = [h[1] for h in history]
    mx = max(1, max(pops))
    chars = "▁▂▃▄▅▆▇█"
    out = []
    for p in pops:
        idx = int((p/mx) * (len(chars)-1))
        out.append(chars[idx])
    return "".join(out)

def color_symbol(cell_id: str, fitness: float) -> Tuple[str,str]:
    def has_any(words: List[str]) -> bool:
        return any(w in cell_id for w in words)
    if cell_id.startswith("user_") or has_any(_user_words):  return (COL["user"], SYM["user"])
    if cell_id.startswith("repo_") or has_any(_repo_words):  return (COL["repo"], SYM["repo"])
    if   fitness > 0.75: return (COL["high"], SYM["high"])
    elif fitness > 0.55: return (COL["med"],  SYM["med"])
    elif fitness > 0.35: return (COL["low"],  SYM["low"])
    elif fitness > 0.15: return (COL["low"],  SYM["min"])
    else:                return (COL["dead"], SYM["dead"])

# deterministic base position
def hsh(s: str, mod: int) -> int:
    if mod <= 0: return 0
    return int.from_bytes(blake2b(s.encode(), digest_size=8).digest(), "little") % mod

def base_pos(cell_id: str, w: int, h: int) -> Tuple[int,int]:
    return hsh(cell_id+"_x", w), hsh(cell_id+"_y", h)

def drift_offset(cell_id: str, t: float, resonance: float) -> Tuple[int,int]:
    if not ENABLE_DRIFT: return (0,0)
    r = max(0.0, min(1.0, resonance))
    amp = 1.0 + 2.0*r
    kx = 0.6 + (hsh(cell_id+"_kx", 100)/200.0) # 0.6..1.1
    ky = 0.6 + (hsh(cell_id+"_ky", 100)/200.0)
    dx = int(round(math.sin(t*kx + hsh(cell_id+"_px",1000)/90.0) * amp))
    dy = int(round(math.cos(t*ky + hsh(cell_id+"_py",1000)/110.0) * amp))
    return dx, dy

def put_text(grid: List[List[str]], x: int, y: int, token: str):
    h = len(grid); w = len(grid[0]) if h>0 else 0
    if y < 0 or y >= h: return
    for i,ch in enumerate(token):
        xx = x+i
        if 0 <= xx < w:
            grid[y][xx] = ch

def token_for_cell(cell_id: str) -> str:
    # extract word-like token from id
    if "_" in cell_id:
        parts = cell_id.split("_")
        if len(parts) >= 2 and parts[1]:
            return parts[1][:8]
    # fallback: first 8 chars
    return re.sub(r"[^a-zA-Z0-9]", "", cell_id)[:8] or "cell"

def build_grid(cells, grid_w, grid_h, t):
    # prepare blank grid
    grid = [[" " for _ in range(grid_w)] for _ in range(grid_h)]
    # priority: user > repo > organic (by choose longer token overwrite)
    for (cid, age, res, fit) in cells:
        col, sym = color_symbol(cid, fit)
        token = token_for_cell(cid)
        # breathing shade for organic
        if ENABLE_BREATH and not (cid.startswith("user_") or cid.startswith("repo_")):
            shade = math.sin(_breath*2*math.pi)*0.5+0.5
            if   fit>0.75 and shade>0.66: sym = SYM["high"]
            elif fit>0.55 and shade>0.33: sym = SYM["med"]
            elif fit>0.35:                 sym = SYM["low"]
            else:                          sym = SYM["min"]
        # compose colored sprite: symbol + word
        sprite = f"{col}{sym} {token}{RESET}" if ENABLE_COLORS else (sym+" "+token)
        bx,by = base_pos(cid, grid_w, grid_h)
        dx,dy = drift_offset(cid, t, res)
        x = max(0, min(grid_w-1, bx+dx))
        y = max(0, min(grid_h-1, by+dy))
        # keep inside (avoid cutting colored prefix): shift left if near right edge
        sprite_plain_len = 2 + len(token)   # "★ "+word  or "◆ "+word
        if x + sprite_plain_len >= grid_w:
            x = max(0, grid_w - sprite_plain_len)
        put_text(grid, x, y, sprite)
    return grid

def pulse_bar(resonance: float, width: int) -> str:
    width = max(10, width)
    filled = int(max(0.0, min(1.0, resonance)) * width)
    return f"{COL['high']}{'█'*filled}{RESET}{'░'*(width-filled)}"

def header_metrics_line(w: int,
                        iteration:int, pop:int, res:float,
                        age:float, births:int, deaths:int) -> List[str]:
    # Build a single line with separators that never overflows:
    items = [
        f"Iter:{iteration}",
        f"Pop:{pop}",
        f"Res:{res:.2f}",
        f"Age:{age:.1f}",
        f"Births:{births}",
        f"Deaths:{deaths}",
    ]
    line = " | ".join(items)
    # If too long, we split into two lines
    if len(line) <= w - H_MARGIN*2:
        return [line]
    # try 2 lines split halfway
    split = len(items)//2
    return [" | ".join(items[:split]), " | ".join(items[split:])]

# ------------------------- DRAW FRAME -----------------------

def draw_frame(conn,
               cells,
               iteration:int, pop:int, res:float, age:float, births:int, deaths:int,
               injected: Optional[List[Tuple[str,str,float,str]]],
               hist: List[Tuple[int,int,float]]):
    global _last_births, _last_deaths

    W,H = term_size()
    # Compute layout
    banner_w = min( max(50, int(W*0.92)), W - H_MARGIN*2 )
    grid_w   = 44 if W < 80 else 56
    grid_h   = 10 if H < 28 else 16
    left_pad = center_x(banner_w, W)

    # clear
    clear_screen()

    # Banner
    for ln in banner(["ASYNC FIELD FOREVER (HYBRID) — VISUALISER"], banner_w):
        print(" " * left_pad + ln)

    # Header metrics (wrapped if needed)
    for mline in header_metrics_line(banner_w, iteration, pop, res, age, births, deaths):
        print(" " * left_pad + mline)

    # pulse & history
    print(" " * left_pad + f"Pulse: {pulse_bar(res, max(18, int(banner_w*0.45)))}")
    s = spark(hist)
    if s:
        print(" " * left_pad + f"Hist:  {COL['med']}{s}{RESET}")

    # grid caption
    print()
    print(" " * left_pad + (DIM + "– grid –" + RESET).center(banner_w))

    # word sprites grid
    t = time.time() * 0.6
    grid = build_grid(cells, grid_w, grid_h, t)
    grid_left = center_x(grid_w, W)
    for row in grid:
        print(" " * grid_left + "".join(row))

    # injected recap (top 3)
    if injected:
        user_inj = [i for i in injected if i[3]=="user"][:3]
        repo_inj = [i for i in injected if i[3]=="repo"][:3]
        if user_inj or repo_inj:
            print()
        if user_inj:
            print(" " * left_pad + f"{COL['user']}★ You:{RESET} " +
                  ", ".join([f"{w} ({act.lower()})" for w,act,_,_ in user_inj]))
        if repo_inj:
            print(" " * left_pad + f"{COL['repo']}◆ Repo:{RESET} " +
                  ", ".join([f"{w} ({act.lower()})" for w,act,_,_ in repo_inj]))

    # mini list (top cells)
    if cells:
        print()
        head = "src  word          fit   res   age"
        print(" " * left_pad + head)
        print(" " * left_pad + "-"*len(head))
        for cid, age_c, res_c, fit_c in cells[:min(4, len(cells))]:
            col,sym = color_symbol(cid, fit_c)
            token = token_for_cell(cid)
            src = ("U" if cid.startswith("user_") else
                   "R" if cid.startswith("repo_") else "O")
            line = f"{col}{sym}{RESET} {src}  {token:<12}  {fit_c:0.2f}  {res_c:0.2f}  {age_c}"
            print(" " * left_pad + line)

    # footer line
    print("\n" + " " * left_pad + "-"*banner_w)
    legend = f"{COL['user']}★ your{RESET}   {COL['repo']}◆ repo{RESET}   {COL['high']}█ organic{RESET}"
    clock  = datetime.now().strftime("%H:%M:%S")
    # spread legend + clock ends
    print(" " * left_pad + legend + " " * max(1, banner_w - len(legend) - 8) + clock)

    # stable input prompt at left
    print()
    print("> ", end="", flush=True)

    # beeps only on changes (optional)
    if births > _last_births:
        sys.stdout.write("\a")
    if deaths > _last_deaths and pop>0:
        sys.stdout.write("\a\a")
    if pop == 0:
        sys.stdout.write("\a\a\a")
    _last_births, _last_deaths = births, deaths

# --------------------------- MAIN ---------------------------

def main():
    global _running, _breath

    # intro
    W,H = term_size()
    clear_screen()
    title = "FIELD VISUALISER v7.5 — HYBRID + WORD SPRITES"
    bw = min(max(50, int(W*0.92)), W - H_MARGIN*2)
    lp = center_x(bw, W)
    for ln in banner([title], bw): print(" "*lp + ln)
    print(" "*lp + f"DB: {ACTIVE_DB}")
    monitor = try_init_repo_monitor()
    print(" "*lp + (f"{COL['repo']}Repo monitor: ACTIVE{RESET}" if monitor else f"{COL['dead']}Repo monitor: OFF{RESET}"))
    print(" "*lp + f"{COL['user']}Type to inject words (e.g., 'hello field how are you'){RESET}")
    print(" "*lp + "Starting in 3s...\n")
    time.sleep(3)

    # threads & DB
    t_in = threading.Thread(target=input_thread, daemon=True); t_in.start()
    conn = db_conn()

    last_ui = 0.0
    injected_last = None

    try:
        while _running:
            now = time.time()
            _breath = (_breath + FRAME_DT) % 1.0

            injected_last = None
            # process input
            if _input_buffer:
                text = _input_buffer.pop(0)
                words = extract_words(text)
                if words:
                    injected_last = inject_words(conn, words, source="user")

            # periodic repo injection + DB refresh
            if now - last_ui >= UI_REFRESH:
                if monitor:
                    rw = fetch_repo_words(monitor)
                    if rw:
                        inj = inject_words(conn, rw, source="repo")
                        injected_last = (injected_last or []) + inj

                it, pop, res, age, br, de = fetch_state(conn)
                cells = fetch_cells(conn, limit=120)      # enough to populate grid
                hist  = fetch_history(conn, limit=18)

                draw_frame(conn, cells, it, pop, res, age, br, de, injected_last, hist)
                last_ui = now

            time.sleep(FRAME_DT)

    except KeyboardInterrupt:
        _running = False
        clear_screen()
        print(f"{COL['banner']}Stopped. Async field forever. 🧬⚡{RESET}")
    finally:
        try: conn.close()
        except: pass

if __name__ == "__main__":
    main()