#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIELD VISUALISER v7.9 — Flat-Line Centered Edition
- One single horizontal line under header (no box)
- Perfectly centered grid (adaptive to terminal width)
- Stars for user-injected cells kept
- Sound alerts (birth/death/extinction)
- Color + breathing/drift motion
- Clean input prompt at line start

Termux / macOS / Linux compatible (ANSI).
"""

import os
import re
import sys
import math
import time
import shutil
import random
import sqlite3
import threading
from hashlib import blake2b
from datetime import datetime
from typing import List, Tuple

# =========================
# Terminal/Render Settings
# =========================
def term_size() -> Tuple[int, int]:
    try:
        w, h = shutil.get_terminal_size((80, 24))
    except Exception:
        w, h = 80, 24
    return max(40, w), max(20, h)

TERM_W, TERM_H = term_size()

# Grid size (adaptive but stable)
GRID_W = 48 if TERM_W >= 90 else (40 if TERM_W >= 72 else 32)
GRID_H = 18 if TERM_H >= 28 else (14 if TERM_H >= 24 else 12)

# Left margin so grid is visually centered
def grid_left_margin() -> int:
    margin = (TERM_W - GRID_W) // 2
    return max(0, margin)

LEFT_PAD = grid_left_margin()

# UI cadence
FRAME_DT = 0.15      # simulation refresh
UI_REFRESH = 0.9     # re-render interval (sec)

# =========================
# Feature Flags
# =========================
ENABLE_COLOR = True
ENABLE_SOUND = True
ENABLE_BREATH = True
ENABLE_DRIFT = True

# =========================
# Colors & Symbols
# =========================
RESET = "\033[0m" if ENABLE_COLOR else ""
BOLD  = "\033[1m" if ENABLE_COLOR else ""
DIM   = "\033[2m" if ENABLE_COLOR else ""
COL = {
    "banner": "\033[95m" if ENABLE_COLOR else "",
    "high":   "\033[92m" if ENABLE_COLOR else "",
    "med":    "\033[93m" if ENABLE_COLOR else "",
    "low":    "\033[90m" if ENABLE_COLOR else "",
    "dead":   "\033[91m" if ENABLE_COLOR else "",
    "user":   "\033[96m" if ENABLE_COLOR else "",
    "repo":   "\033[94m" if ENABLE_COLOR else "",
    "white":  "\033[97m" if ENABLE_COLOR else "",
}

SYMBOL = {
    "high": "█",
    "med":  "▓",
    "low":  "▒",
    "min":  "░",
    "dead": "·",
    "user": "★",   # keep star near user cells
    "repo": "◆",
}

# =========================
# DB Paths
# =========================
DB_PATH_TERMUX = "/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3"
DB_PATH_LOCAL  = "./field_test.sqlite3"
ACTIVE_DB = DB_PATH_TERMUX if os.path.exists(DB_PATH_TERMUX) else DB_PATH_LOCAL

# =========================
# Runtime State
# =========================
_running = True
_breath_phase = 0.0
_user_words: List[str] = []    # track user-injected tokens to colorize
_last_births = 0
_last_deaths = 0

# =========================
# Input thread
# =========================
_input_buf: List[str] = []

def input_thread():
    global _running
    while _running:
        try:
            s = input()
            if s.strip():
                _input_buf.append(s.strip())
        except (EOFError, KeyboardInterrupt):
            _running = False
            break

# =========================
# Word extraction
# =========================
STOP = {
    "the","is","are","was","were","be","been","being","have","has","had","do","does","did",
    "will","would","could","should","may","might","must","can","this","that","with","from",
    "for","not","but","and","or","into","onto","over","under","between","within","out","in","to","of","on"
}

def extract_words(text: str) -> List[str]:
    words = re.findall(r"\b[a-z]{2,}\b", text.lower())
    return [w for w in words if w not in STOP and len(w) > 2][:24]

# =========================
# SQLite helpers
# =========================
def fetch_state(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("""
        SELECT iteration, cell_count, avg_resonance, avg_age, births, deaths
        FROM field_state ORDER BY id DESC LIMIT 1
    """)
    row = cur.fetchone()
    if not row:
        return (0, 0, 0.0, 0.0, 0, 0)
    return row

def fetch_cells(conn: sqlite3.Connection, limit: int = 120):
    cur = conn.cursor()
    cur.execute("""
        SELECT cell_id, age, COALESCE(resonance_score,0.0), COALESCE(fitness,0.0)
        FROM field_cells
        WHERE status='alive'
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    return cur.fetchall()

def fetch_history(conn: sqlite3.Connection, limit: int = 18):
    cur = conn.cursor()
    cur.execute("""
        SELECT iteration, cell_count, avg_resonance
        FROM field_state ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    rows.reverse()
    return rows

def inject_words(conn: sqlite3.Connection, words: List[str]):
    """Insert/boost user words as cells; return [(word, action, fitness)]."""
    cur = conn.cursor()
    now = int(time.time())
    out = []
    for w in words:
        # try boost existing
        cur.execute("""
            SELECT cell_id, COALESCE(fitness,0.5)
            FROM field_cells
            WHERE cell_id LIKE ? AND status='alive'
            ORDER BY id DESC LIMIT 1
        """, (f"%{w}%",))
        row = cur.fetchone()
        if row:
            cid, oldf = row
            newf = min(1.0, float(oldf) + 0.15)
            cur.execute("""
                UPDATE field_cells
                SET fitness=?, resonance_score=COALESCE(resonance_score,0.0)+0.10
                WHERE cell_id=? AND status='alive'
            """, (newf, cid))
            out.append((w, "BOOSTED", newf))
        else:
            # create new alive cell
            fid = f"user_{w}_{now}"
            fit = random.uniform(0.62, 0.88)
            res = random.uniform(0.50, 0.82)
            cur.execute("""
                INSERT INTO field_cells (cell_id, age, resonance_score, fitness, status, timestamp)
                VALUES (?, 0, ?, ?, 'alive', ?)
            """, (fid, res, fit, now))
            out.append((w, "BORN", fit))
            _user_words.append(w)
    conn.commit()
    return out

# =========================
# Visual utils
# =========================
def bell(n=1):
    if not ENABLE_SOUND:
        return
    try:
        sys.stdout.write("\a"*n)
        sys.stdout.flush()
    except Exception:
        pass

def h8(s: str, mod: int) -> int:
    """Small stable hash -> 0..mod-1"""
    d = blake2b(s.encode("utf-8"), digest_size=8).digest()
    v = int.from_bytes(d, "little")
    return v % max(1, mod)

def base_pos(cell_id: str, w: int, h: int) -> Tuple[int, int]:
    return h8(cell_id+"_x", w), h8(cell_id+"_y", h)

def drift_offset(cell_id: str, t: float, resonance: float) -> Tuple[int, int]:
    if not ENABLE_DRIFT:
        return (0, 0)
    r = max(0.0, min(1.0, resonance))
    amp = 1.0 + 2.0*r  # higher resonance = wider wander
    # per-cell random-ish speeds
    kx = 0.6 + 0.5*(h8(cell_id+"_kx", 100)/100.0)
    ky = 0.6 + 0.5*(h8(cell_id+"_ky", 100)/100.0)
    dx = int(round(math.sin(t*kx + h8(cell_id+"_px", 360)/57.0) * amp))
    dy = int(round(math.cos(t*ky + h8(cell_id+"_py", 360)/63.0) * amp))
    return (dx, dy)

def is_user_cell(cell_id: str) -> bool:
    if cell_id.startswith("user_"):
        return True
    # fallback: if recent injected word inside id
    return any(w in cell_id for w in _user_words)

def color_and_symbol(cell_id: str, fitness: float) -> Tuple[str, str, bool]:
    """Return (color, symbol, is_user)."""
    if is_user_cell(cell_id):
        return COL["user"], SYMBOL["user"], True
    if fitness > 0.75:
        return COL["high"], SYMBOL["high"], False
    if fitness > 0.55:
        return COL["med"], SYMBOL["med"], False
    if fitness > 0.35:
        return COL["low"], SYMBOL["low"], False
    if fitness > 0.15:
        return COL["low"], SYMBOL["min"], False
    return COL["dead"], SYMBOL["dead"], False

def place_on_grid(cells, w: int, h: int, t: float):
    """Returns 2D grid of strings with color codes, centered by LEFT_PAD on print."""
    grid = [[" " for _ in range(w)] for _ in range(h)]
    prio = [[-1 for _ in range(w)] for _ in range(h)]

    def source_priority(cell_id: str) -> int:
        # user cells over organic
        return 2 if is_user_cell(cell_id) else 1

    for cell_id, age, resonance, fitness in cells:
        x0, y0 = base_pos(cell_id, w, h)
        dx, dy = drift_offset(cell_id, t, resonance)
        x = max(0, min(w-1, x0 + dx))
        y = max(0, min(h-1, y0 + dy))

        color, sym, is_user = color_and_symbol(cell_id, fitness)

        # subtle breathing for organic cells (not for user stars)
        if ENABLE_BREATH and not is_user:
            shade = math.sin(_breath_phase * 2.0 * math.pi) * 0.5 + 0.5
            if fitness > 0.75 and shade > 0.66:
                sym = SYMBOL["high"]
            elif fitness > 0.55 and shade > 0.33:
                sym = SYMBOL["med"]
            elif fitness > 0.35:
                sym = SYMBOL["low"]
            else:
                sym = SYMBOL["min"]

        p = source_priority(cell_id)
        if p >= prio[y][x]:
            prio[y][x] = p
            grid[y][x] = f"{color}{sym}{RESET}" if ENABLE_COLOR else sym

    return grid

def sparkline(history) -> str:
    if len(history) < 2:
        return ""
    pops = [h[1] for h in history]
    m = max(pops) if pops else 1
    chars = "▁▂▃▄▅▆▇█"
    out = []
    for p in pops:
        idx = int((p / m) * (len(chars)-1)) if m > 0 else 0
        out.append(chars[min(max(idx,0), len(chars)-1)])
    return "".join(out)

# =========================
# Render frame
# =========================
def draw_frame(iteration: int,
               cell_count: int,
               avg_res: float,
               avg_age: float,
               births: int,
               deaths: int,
               cells,
               hist,
               injected):
    global _last_births, _last_deaths

    # sounds on changes
    if births > _last_births:
        bell(1)
    if deaths > _last_deaths and cell_count > 0:
        bell(2)
    if cell_count == 0 and (births > 0 or deaths > 0):
        bell(3)

    _last_births, _last_deaths = births, deaths

    # clear
    os.system("clear" if os.name != "nt" else "cls")

    # HEADER (centered text) + single full-width line
    title = "ASYNC FIELD FOREVER — v7.9"
    hdr = f"{BOLD}{COL['banner']}{title.center(TERM_W)}{RESET}"
    print(hdr)
    print("─" * TERM_W)   # one single flat line across entire terminal

    # Metrics (keep tidy & aligned)
    left = f"Iter: {iteration:<6} Pop: {cell_count:<6} Res: {avg_res:>5.2f}"
    right = f"Age: {avg_age:>4.1f}  B: {births:<3} D: {deaths:<3}"
    pad = max(0, TERM_W - len(left) - len(right) - 1)
    print(left + " " * pad + right)

    # Pulse bar (fixed width scaled by TERM_W)
    pulse_w = 40 if TERM_W >= 80 else 28
    pw = int(max(0.0, min(1.0, avg_res)) * pulse_w)
    bar = f"{COL['high']}{'█'*pw}{RESET}{'░'*(pulse_w - pw)}"
    print(f"Pulse: {bar}")

    # History sparkline
    sp = sparkline(hist)
    if sp:
        print(f"Hist : {COL['med']}{sp}{RESET}")

    # Show recent injections (short)
    if injected:
        print(f"{COL['user']}You:{RESET}", end=" ")
        msgs = []
        for w, act, f in injected[:4]:
            sym = "★" if act == "BORN" else "↑"
            msgs.append(f"{sym} {w} ({f:.2f})")
        print(", ".join(msgs))

    # GRID (centered)
    grid = place_on_grid(cells, GRID_W, GRID_H, time.time()*0.6)
    print()
    for row in grid:
        print((" " * LEFT_PAD) + "".join(row))

    # Footer & prompt (flush at line start)
    print("\n" + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("Type to inject words (Ctrl+C to quit):")
    # input prompt at start of line — no extra spaces:
    print("> ", end="", flush=True)

# =========================
# Main loop
# =========================
def main():
    global _running, _breath_phase

    # intro (no box, just clean)
    intro = f"{BOLD}{COL['banner']}{'FIELD VISUALISER — Flat-Line v7.9'.center(TERM_W)}{RESET}"
    print(intro)
    print(f"Terminal: {TERM_W}x{TERM_H} | Grid: {GRID_W}x{GRID_H}")
    print(f"DB: {ACTIVE_DB}")
    print("Starting...\n")
    time.sleep(1.2)

    # input thread
    threading.Thread(target=input_thread, daemon=True).start()

    conn = sqlite3.connect(ACTIVE_DB)
    last_ui = 0.0
    try:
        while _running:
            t = time.time()
            _breath_phase = (_breath_phase + FRAME_DT) % 1.0

            # handle input
            injected = None
            if _input_buf:
                text = _input_buf.pop(0)
                toks = extract_words(text)
                if toks:
                    injected = inject_words(conn, toks)

            # fetch + draw periodically
            if (t - last_ui) >= UI_REFRESH:
                it, count, avg_res, avg_age, births, deaths = fetch_state(conn)
                cells = fetch_cells(conn, limit=GRID_W * GRID_H)
                hist = fetch_history(conn, limit=18)

                draw_frame(it, count, avg_res, avg_age, births, deaths, cells, hist, injected)
                last_ui = t

            time.sleep(FRAME_DT)

    except KeyboardInterrupt:
        _running = False
    finally:
        conn.close()
        print(f"\n{COL['banner']}Stopped. ⚡{RESET}")

if __name__ == "__main__":
    main()