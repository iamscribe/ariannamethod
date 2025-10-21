#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIELD VISUALISER v7.7 — Symmetric Pulse / Organic Drift
Termux / macOS / Linux — ANSI-safe, emoji-safe, fixed-width banner.

What’s new vs 7.1:
- Perfect banner symmetry (no wrap), width-locked box drawing
- Centered grid with exact padding (no right empty gutter)
- Words fly instead of stars (per-cell word sprites with drift)
- Breath animation for organic cells, priority overlay by source
- Beeps (safe) on births/deaths/extinction (optional)
- De-duplicated “injected” reporting (shows only fresh)
- Robust truncation to avoid line overflow in narrow terminals
"""

import os
import re
import sys
import time
import math
import shutil
import random
import sqlite3
import threading
from datetime import datetime
from hashlib import blake2b
from pathlib import Path
from typing import List, Tuple, Dict, Optional

# ======================= TERMINAL & LAYOUT =======================

def term_size() -> Tuple[int, int]:
    try:
        w, h = shutil.get_terminal_size((80, 24))
    except Exception:
        w, h = 80, 24
    # hard cap min/max to avoid crazy sizes
    w = max(60, min(160, w))
    h = max(20, min(60, h))
    return w, h

TERM_W, TERM_H = term_size()

def clamp(n, lo, hi): return max(lo, min(hi, n))

# Banner width: fixed to 90% of terminal (rounded to even), clamped 50..100
_banner_target = int(round(TERM_W * 0.90))
if _banner_target % 2 == 1:
    _banner_target -= 1
BANNER_WIDTH = clamp(_banner_target, 50, 100)

# Grid size tuned by device class
IS_MOBILE = TERM_W < 80
GRID_W = 36 if IS_MOBILE else 48
GRID_H = 12 if IS_MOBILE else 18

# Center grid: padding so grid is centered inside banner box
def grid_left_padding(banner_width: int, grid_w: int) -> int:
    inner = banner_width  # we print grid under banner, no side frame chars
    pad = (inner - grid_w) // 2
    return max(0, pad)

GRID_PAD_LEFT = grid_left_padding(BANNER_WIDTH, GRID_W)

# Pulse bar width (fits banner)
PULSE_BAR_W = 24 if IS_MOBILE else 40

# Cell list lines below grid
CELL_LIST_LIMIT = 2 if IS_MOBILE else 4

# Timings
FRAME_DT = 0.20      # animation tick
UI_REFRESH = 5.00    # ui full redraw

# ======================= FLAGS =======================

ENABLE_COLOR  = True
ENABLE_SOUND  = True
ENABLE_BREATH = True
ENABLE_DRIFT  = True

# ======================= COLORS =======================

RESET = "\033[0m" if ENABLE_COLOR else ""
BOLD  = "\033[1m" if ENABLE_COLOR else ""
DIM   = "\033[2m" if ENABLE_COLOR else ""
COLORS = {
    "high":   "\033[92m" if ENABLE_COLOR else "",
    "medium": "\033[93m" if ENABLE_COLOR else "",
    "low":    "\033[90m" if ENABLE_COLOR else "",
    "dead":   "\033[91m" if ENABLE_COLOR else "",
    "banner": "\033[95m" if ENABLE_COLOR else "",
    "user":   "\033[96m" if ENABLE_COLOR else "",
    "repo":   "\033[94m" if ENABLE_COLOR else "",
    "white":  "\033[97m" if ENABLE_COLOR else "",
}

# ======================= SYMBOLS =======================

SYMS = {
    "high": "█",
    "med":  "▓",
    "low":  "▒",
    "min":  "░",
    "dead": "·",
    "user": "★",
    "repo": "◆",
}

# ======================= DB PATHS =======================

DB_TERMUX = "/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3"
DB_LOCAL  = "./field_test.sqlite3"
ACTIVE_DB = DB_TERMUX if os.path.exists(os.path.expanduser(DB_TERMUX)) else DB_LOCAL

# Repo monitor
REPO_PATH = Path(__file__).parent.parent.parent
ENABLE_REPO_MONITOR = True

# ======================= STATE =======================

_last_births = 0
_last_deaths = 0
_last_injected_key: Optional[str] = None  # to avoid repeating the same injected block
_breath_phase = 0.0
_running = True

_user_words: List[str] = []
_repo_words: List[str] = []
_input_buffer: List[str] = []

# ======================= REPO MONITOR (optional) =======================

try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "arianna_core_utils"))
    from repo_monitor import RepoMonitor
    REPO_MONITOR_AVAILABLE = True
except Exception:
    REPO_MONITOR_AVAILABLE = False

def init_repo_monitor():
    if not REPO_MONITOR_AVAILABLE or not ENABLE_REPO_MONITOR:
        return None
    try:
        return RepoMonitor(repo_path=REPO_PATH)
    except Exception as e:
        print(f"⚠️  Failed to init repo_monitor: {e}")
        return None

def extract_words(text: str) -> List[str]:
    STOP = {
        "the","is","are","was","were","be","been","being","have","has","had","do","does","did",
        "will","would","could","should","may","might","must","can","this","that","with","from",
        "for","not","but","and","or","into","onto","over","under","between","within","out","your",
        "you","him","her","they","them","our","their","its","it's","there","here","then","than",
        "like","just","also","too","very","more","less","some","any","each","both"
    }
    words = re.findall(r'\b[a-z]{2,}\b', text.lower())
    return [w for w in words if w not in STOP and len(w) > 2][:32]

def fetch_repo_changes_words(monitor) -> List[str]:
    if not monitor: return []
    try:
        changes = monitor.fetch_repo_context(limit=5)  # last 5 changes
        pool: List[str] = []
        for ch in changes:
            content = ch.get("content", "")
            pool.extend(extract_words(content)[:3])
        # unique & limit 10
        uniq, seen = [], set()
        for w in pool:
            if w not in seen:
                seen.add(w)
                uniq.append(w)
            if len(uniq) >= 10:
                break
        return uniq
    except Exception:
        return []

# ======================= DB I/O =======================

def db_connect() -> sqlite3.Connection:
    return sqlite3.connect(ACTIVE_DB)

def fetch_state(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("""
        SELECT iteration, cell_count, avg_resonance, avg_age, births, deaths
        FROM field_state ORDER BY id DESC LIMIT 1
    """)
    row = cur.fetchone()
    return row if row else (0,0,0.0,0.0,0,0)

def fetch_cells(conn: sqlite3.Connection, limit: int) -> List[Tuple[str,int,float,float]]:
    cur = conn.cursor()
    cur.execute("""
        SELECT cell_id, age, COALESCE(resonance_score,0.0), COALESCE(fitness,0.0)
        FROM field_cells WHERE status='alive'
        ORDER BY id DESC LIMIT ?
    """, (limit,))
    return cur.fetchall()

def fetch_history(conn: sqlite3.Connection, limit: int = 20) -> List[Tuple[int,int,float]]:
    cur = conn.cursor()
    cur.execute("""
        SELECT iteration, cell_count, avg_resonance
        FROM field_state ORDER BY id DESC LIMIT ?
    """, (limit,))
    return list(reversed(cur.fetchall()))

def inject_words(conn: sqlite3.Connection, words: List[str], source: str) -> List[Tuple[str,str,float,str]]:
    """
    Returns list of (word, action, fitness, source)
    """
    cur = conn.cursor()
    ts = int(time.time())
    out: List[Tuple[str,str,float,str]] = []
    for w in words:
        cur.execute("""
            SELECT cell_id, COALESCE(fitness,0.6) FROM field_cells
            WHERE cell_id LIKE ? AND status='alive'
            ORDER BY id DESC LIMIT 1
        """, (f"%{w}%",))
        row = cur.fetchone()
        if row:
            cid, prev = row
            newf = min(1.0, prev + 0.15)
            cur.execute("""
                UPDATE field_cells SET fitness=?, resonance_score=COALESCE(resonance_score,0)+0.1
                WHERE cell_id=? AND status='alive'
            """, (newf, cid))
            out.append((w, "BOOSTED", newf, source))
        else:
            cid = f"{source}_{w}_{ts}"
            fit = random.uniform(0.65, 0.85) if source == "repo" else random.uniform(0.60, 0.90)
            res = random.uniform(0.50, 0.80)
            cur.execute("""
                INSERT INTO field_cells (cell_id, age, resonance_score, fitness, status, timestamp)
                VALUES (?, 0, ?, ?, 'alive', ?)
            """, (cid, res, fit, ts))
            out.append((w, "BORN", fit, source))
            if source == "user":
                _user_words.append(w)
            else:
                _repo_words.append(w)
    conn.commit()
    return out

# ======================= INPUT THREAD =======================

def input_thread():
    global _running, _input_buffer
    while _running:
        try:
            s = input()
            if s.strip():
                _input_buffer.append(s.strip())
        except (EOFError, KeyboardInterrupt):
            _running = False
            break

# ======================= UTILS =======================

def hsh(s: str, mod: int) -> int:
    return int.from_bytes(blake2b(s.encode("utf-8"), digest_size=8).digest(), "little") % max(1,mod)

def bell(n=1):
    if not ENABLE_SOUND:
        return
    try:
        sys.stdout.write('\a'*n)
        sys.stdout.flush()
    except Exception:
        pass

def safe_line(s: str, width: int) -> str:
    # strip ANSI for counting, but we’ll assume width safe by preplanning.
    # defensive truncate to width if needed:
    if len(s) <= width:
        return s
    # danger: may cut ANSI; we try to cut before RESET if close
    return s[:width]

# ======================= CELL → COLOR & SOURCE =======================

def is_user_cell(cid: str) -> bool:
    return cid.startswith("user_") or any(w in cid for w in _user_words)

def is_repo_cell(cid: str) -> bool:
    return cid.startswith("repo_") or any(w in cid for w in _repo_words)

def color_for_cell(cid: str, fitness: float) -> str:
    if is_user_cell(cid): return COLORS["user"]
    if is_repo_cell(cid): return COLORS["repo"]
    if   fitness > 0.75:  return COLORS["high"]
    elif fitness > 0.55:  return COLORS["medium"]
    elif fitness > 0.35:  return COLORS["low"]
    elif fitness > 0.15:  return COLORS["low"]
    else:                 return COLORS["dead"]

def sym_for_cell(cid: str, fitness: float, shade: float) -> str:
    # when drawing single-char fallback (if no room for word)
    if   fitness > 0.75 and shade > 0.66: return SYMS["high"]
    elif fitness > 0.55 and shade > 0.33: return SYMS["med"]
    elif fitness > 0.35:                   return SYMS["low"]
    else:                                  return SYMS["min"]

# ======================= WORD SPRITES ON GRID =======================

MAX_WORD_LEN = 8 if IS_MOBILE else 10  # keep compact so rows don’t overflow

def extract_display_word(cell_id: str, i_fallback: int) -> str:
    if cell_id.startswith("user_") or cell_id.startswith("repo_"):
        parts = cell_id.split("_")
        if len(parts) > 1:
            w = parts[1]
        else:
            w = cell_id
    else:
        # fallback seed words
        POOL = [
            "resonance","emergence","chaos","pulse","shimmer","echo","spiral","field",
            "phase","quantum","flux","bloom","decay","nexus","drift","void","fracture","harmony"
        ]
        w = POOL[i_fallback % len(POOL)]
    # truncate to max
    if len(w) > MAX_WORD_LEN:
        w = w[:MAX_WORD_LEN]
    return w

def base_pos(cid: str, w: int, h: int) -> Tuple[int,int]:
    return hsh(cid+"_x", w), hsh(cid+"_y", h)

def drift_offset(cid: str, t: float, resonance: float) -> Tuple[float,float]:
    if not ENABLE_DRIFT:
        return (0.0, 0.0)
    r = clamp(resonance, 0.0, 1.0)
    amp = 1.0 + 2.0*r
    kx = 0.6 + 0.5*(hsh(cid+"_kx", 100)/100.0)
    ky = 0.6 + 0.5*(hsh(cid+"_ky", 100)/100.0)
    px = hsh(cid+"_px", 1000)/90.0
    py = hsh(cid+"_py", 1000)/110.0
    dx = math.sin(t*kx + px)*amp
    dy = math.cos(t*ky + py)*amp
    return dx, dy

def draw_words_grid(cells: List[Tuple[str,int,float,float]], w: int, h: int, t: float) -> List[str]:
    """
    Returns a list of rows (strings) representing the centered grid.
    We render words, centered around (x,y). If word exceeds bounds, we clip.
    Priority: user > repo > organic.
    """
    # prepare buffers
    rows = [ [" "] * w for _ in range(h) ]
    prio = [ [0]   * w for _ in range(h) ]  # 3=user,2=repo,1=organic

    def priority(cid: str) -> int:
        if is_user_cell(cid): return 3
        if is_repo_cell(cid): return 2
        return 1

    # place each cell as a word sprite
    for idx, (cid, age, resonance, fitness) in enumerate(cells):
        x0, y0 = base_pos(cid, w, h)
        dx, dy = drift_offset(cid, t, resonance)
        x = int(round(clamp(x0 + dx, 0, w-1)))
        y = int(round(clamp(y0 + dy, 0, h-1)))

        # word + color + breathing shade
        disp = extract_display_word(cid, idx)
        col = color_for_cell(cid, fitness)

        shade = math.sin((_breath_phase*2*math.pi)) * 0.5 + 0.5 if ENABLE_BREATH else 1.0
        # try to place word centered around x
        start = clamp(x - len(disp)//2, 0, max(0, w - len(disp)))
        end   = start + len(disp)

        # if length is 0 somehow, skip
        if end <= start:
            continue

        # place character by character with priority
        p = priority(cid)

        wrote_any = False
        for cx, ch in enumerate(disp):
            gx = start + cx
            if p >= prio[y][gx]:
                prio[y][gx] = p
                # organic shade affects symbol style only if non-sourced
                if p == 1:
                    # pick a graded symbol if ch is space-ish (we won’t replace letters)
                    # here we keep the letter but slightly “dim” via DIM
                    rows[y][gx] = f"{DIM}{col}{ch}{RESET}"
                else:
                    rows[y][gx] = f"{col}{ch}{RESET}"
                wrote_any = True

        # if couldn’t write (rare due to zero len), fallback single symbol
        if not wrote_any:
            sym = sym_for_cell(cid, fitness, shade)
            if p >= prio[y][x]:
                prio[y][x] = p
                rows[y][x] = f"{col}{sym}{RESET}"

    # turn rows into strings
    return ["".join(r) for r in rows]

# ======================= SPARKLINE =======================

def sparkline(history: List[Tuple[int,int,float]]) -> str:
    if len(history) < 2: return ""
    pops = [h[1] for h in history]
    m = max(pops) if pops else 1
    chars = "▁▂▃▄▅▆▇█"
    out = []
    for p in pops:
        idx = int((p / m) * (len(chars)-1)) if m > 0 else 0
        out.append(chars[idx])
    return "".join(out)

# ======================= RENDER =======================

def clear():
    os.system("clear" if os.name != "nt" else "cls")

def banner():
    inner = BANNER_WIDTH - 2
    print(f"{BOLD}{COLORS['banner']}╔" + "═"*inner + f"╗{RESET}")
    title = " ⚡ ASYNC FIELD FOREVER — v7.7 ⚡ "
    print(f"{BOLD}{COLORS['banner']}║" + title.center(inner) + f"║{RESET}")
    print(f"{BOLD}{COLORS['banner']}╚" + "═"*inner + f"╝{RESET}")

def render_metrics(iteration:int, cell_count:int, avg_res:float, avg_age:float, births:int, deaths:int):
    # Each line kept <= BANNER_WIDTH
    line1 = f"Iter: {iteration} | Pop: {cell_count} | Res: {avg_res:.2f}"
    line2 = f"Age: {avg_age:.1f} | Births: {births} | Deaths: {deaths}"
    print(safe_line(line1, BANNER_WIDTH))
    print(safe_line(line2, BANNER_WIDTH))

def render_pulse(avg_res: float):
    pw = int(clamp(avg_res, 0, 1) * PULSE_BAR_W)
    bar = COLORS["high"] + "█"*pw + RESET + "░"*(PULSE_BAR_W - pw)
    print("\n" + safe_line(f"Pulse: {bar}", BANNER_WIDTH))

def render_history(hist: List[Tuple[int,int,float]]):
    s = sparkline(hist)
    if s:
        print(safe_line(f"Hist : {COLORS['medium']}{s}{RESET}", BANNER_WIDTH))

def render_injected_once(injected: Optional[List[Tuple[str,str,float,str]]]):
    """
    Show injected words only if they changed since last render.
    Uses a simple content hash as a key.
    """
    global _last_injected_key
    if not injected:
        return
    key_src = "|".join([f"{w}:{a}:{round(f,3)}:{src}" for (w,a,f,src) in injected])
    # if identical to last, skip
    if key_src == _last_injected_key:
        return
    _last_injected_key = key_src

    user = [i for i in injected if i[3] == "user"]
    repo = [i for i in injected if i[3] == "repo"]
    if user:
        print(f"\n{COLORS['user']}★ You:{RESET}")
        for w,a,f,_ in user[:2]:
            sym = "★" if a == "BORN" else "↑"
            print(safe_line(f"  {sym} {w} ({f:.2f})", BANNER_WIDTH))
    if repo:
        print(f"\n{COLORS['repo']}◆ Repo:{RESET}")
        for w,a,f,_ in repo[:2]:
            sym = "◆" if a == "BORN" else "↑"
            print(safe_line(f"  {sym} {w} ({f:.2f})", BANNER_WIDTH))

def render_grid(rows: List[str]):
    # header
    print("\n" + (" " * GRID_PAD_LEFT) + f"{DIM}— grid —{RESET}")
    for r in rows:
        line = (" " * GRID_PAD_LEFT) + r
        print(safe_line(line, BANNER_WIDTH))

def render_cell_list(cells: List[Tuple[str,int,float,float]]):
    print("\n" + "─"*BANNER_WIDTH)
    if not cells:
        print(f"{COLORS['dead']}Empty. Type!{RESET}\n")
        return
    # compact roster
    count = min(CELL_LIST_LIMIT, len(cells))
    for i in range(count):
        cid, age, res, fit = cells[i]
        col = color_for_cell(cid, fit)
        # word extraction
        w = extract_display_word(cid, i)
        w = (w[:12] + "…") if len(w) > 12 else w
        src = "U" if is_user_cell(cid) else ("R" if is_repo_cell(cid) else "O")
        print(safe_line(f"{col}{SYMS['high']}{RESET} {src} {w:<12} {fit:.2f}", BANNER_WIDTH))

def render_footer():
    print("\n" + "─"*BANNER_WIDTH)
    clock = datetime.now().strftime("%H:%M:%S")
    legend = f"{COLORS['user']}★{RESET} {COLORS['repo']}◆{RESET} {COLORS['high']}█{RESET}"
    info = f"{legend} | {clock}"
    print(safe_line(info, BANNER_WIDTH))
    # prompt at start of line:
    print(f"\n{COLORS['banner']}>{RESET} ", end="", flush=True)

# ======================= MAIN DRAW =======================

def draw_frame(conn: sqlite3.Connection,
               cells: List[Tuple[str,int,float,float]],
               iteration:int, cell_count:int, avg_res:float, avg_age:float,
               births:int, deaths:int,
               injected: Optional[List[Tuple[str,str,float,str]]],
               hist: List[Tuple[int,int,float]]):
    global _last_births, _last_deaths

    clear()

    if births > _last_births: bell(1)
    if deaths > _last_deaths and cell_count > 0: bell(2)
    if cell_count == 0: bell(3)
    _last_births, _last_deaths = births, deaths

    banner()
    render_metrics(iteration, cell_count, avg_res, avg_age, births, deaths)
    render_pulse(avg_res)
    render_history(hist)
    render_injected_once(injected)

    # words grid (centered)
    t = time.time() * 0.65
    rows = draw_words_grid(cells, GRID_W, GRID_H, t)
    render_grid(rows)

    render_cell_list(cells)
    render_footer()

# ======================= MAIN LOOP =======================

def main():
    global _running, _breath_phase, _input_buffer

    # Intro
    print(f"{BOLD}{COLORS['banner']}{'='*BANNER_WIDTH}{RESET}")
    print(f"{BOLD}{COLORS['banner']}{'FIELD — v7.7  Symmetric Pulse / Organic Drift'.center(BANNER_WIDTH)}{RESET}")
    print(f"{BOLD}{COLORS['banner']}{'='*BANNER_WIDTH}{RESET}")
    print(f"Terminal: {TERM_W}x{TERM_H}  ({'Mobile' if IS_MOBILE else 'Desktop'})")
    print(f"Banner: {BANNER_WIDTH} | Grid: {GRID_W}x{GRID_H} | Pulse: {PULSE_BAR_W}")

    repo_monitor = init_repo_monitor()
    if repo_monitor:
        print(f"{COLORS['repo']}✓ Repo monitor active{RESET}")
    else:
        print(f"{COLORS['dead']}✗ Repo monitor disabled{RESET}")

    print(f"\n{COLORS['user']}Type to inject words into Field (letters only; we filter stopwords).{RESET}")
    print("Starting in 3s...\n")
    time.sleep(3)

    threading.Thread(target=input_thread, daemon=True).start()
    conn = db_connect()

    last_ui = 0.0
    try:
        while _running:
            now = time.time()
            _breath_phase = (_breath_phase + FRAME_DT) % 1.0

            if now - last_ui >= UI_REFRESH:
                injected: List[Tuple[str,str,float,str]] = []

                # user input
                if _input_buffer:
                    text = _input_buffer.pop(0)
                    words = extract_words(text)
                    if words:
                        injected.extend(inject_words(conn, words, "user"))

                # repo changes
                if repo_monitor:
                    repo_words = fetch_repo_changes_words(repo_monitor)
                    if repo_words:
                        injected.extend(inject_words(conn, repo_words, "repo"))

                iteration, cell_count, avg_res, avg_age, births, deaths = fetch_state(conn)
                cells = fetch_cells(conn, limit=GRID_W * GRID_H)
                hist = fetch_history(conn, limit=20)

                draw_frame(conn, cells, iteration, cell_count, avg_res, avg_age, births, deaths,
                           injected if injected else None, hist)
                last_ui = now

            time.sleep(FRAME_DT)

    except KeyboardInterrupt:
        _running = False
        print(f"\n\n{COLORS['banner']}Stopped. 🧬⚡{RESET}\n")
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()