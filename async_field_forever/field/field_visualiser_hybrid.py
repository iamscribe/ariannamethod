#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIELD VISUALISER v7.4 — Symmetry Pass (Termux / macOS / Linux)

• Фикс: верхний отступ (TOP_PAD) — рамка не прилипает к верху
• Фикс: сетка строго по центру, без смещения
• Фикс: промпт '>' начинается в колонке 0
• Фикс: без эмодзи внутри рамки (эмодзи ломают ширину в терминалах)
• Адаптив: ширина баннера и полос, грид под терминал
"""

import time
import sqlite3
import os
import random
import sys
import threading
import re
import math
import shutil
from datetime import datetime
from typing import List, Tuple
from pathlib import Path
from hashlib import blake2b

# ========= TERMINAL ADAPT =========
def get_terminal_config():
    w, h = shutil.get_terminal_size((80, 24))
    banner_w = max(50, min(w - 2, int(w * 0.90)))  # внутри экрана, 90%
    is_mobile = w < 70
    grid_w = 36 if is_mobile else 48
    grid_h = 12 if is_mobile else 18
    pulse_w = min(40, max(20, banner_w - 18))
    cell_list_limit = 2 if is_mobile else 4
    return {
        "term_w": w,
        "term_h": h,
        "banner_w": banner_w,
        "grid_w": grid_w,
        "grid_h": grid_h,
        "pulse_w": pulse_w,
        "cell_list_limit": cell_list_limit,
    }

CFG = get_terminal_config()
TOP_PAD        = 2                       # фиксированный верхний отступ
BANNER_W       = CFG["banner_w"]
GRID_W         = CFG["grid_w"]
GRID_H         = CFG["grid_h"]
PULSE_BAR_W    = CFG["pulse_w"]
CELL_LIST_LIM  = CFG["cell_list_limit"]
FRAME_DT       = 0.2
UI_REFRESH     = 5.0

# ========= DB =========
DB_PATH = "/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3"
DB_PATH_LOCAL = "./field_test.sqlite3"
ACTIVE_DB = DB_PATH if os.path.exists(os.path.expanduser(DB_PATH)) else DB_PATH_LOCAL

REPO_PATH = Path(__file__).parent.parent.parent
ENABLE_REPO_MONITOR = True

# ========= FLAGS =========
ENABLE_COLOR = True
ENABLE_SOUND = True
ENABLE_BREATH = True
ENABLE_DRIFT = True

# ========= COLORS =========
RESET  = "\033[0m" if ENABLE_COLOR else ""
BOLD   = "\033[1m" if ENABLE_COLOR else ""
DIM    = "\033[2m" if ENABLE_COLOR else ""
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

# ========= SYMBOLS =========
STATUS = {
    "high": "█",
    "med":  "▓",
    "low":  "▒",
    "min":  "░",
    "dead": "·",
    "user": "★",
    "repo": "◆",
}

# ========= STATE =========
_last_births = 0
_last_deaths = 0
_user_words: List[str] = []
_repo_words: List[str] = []
_input_buffer: List[str] = []
_running = True
_breath_phase = 0.0

# ========= REPO MONITOR =========
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "arianna_core_utils"))
    from repo_monitor import RepoMonitor
    REPO_MON_AVAIL = True
except Exception:
    REPO_MON_AVAIL = False

def init_repo_monitor():
    if not (ENABLE_REPO_MONITOR and REPO_MON_AVAIL):
        return None
    try:
        return RepoMonitor(repo_path=REPO_PATH)
    except Exception:
        return None

# ========= WORDS / INJECTION =========
STOP = {
    "the","is","are","was","were","be","been","being","have","has","had","do","does","did",
    "will","would","could","should","may","might","must","can","this","that","with","from",
    "for","not","but","and","or","into","onto","over","under","between","within","out"
}
def extract_words(text: str) -> List[str]:
    words = re.findall(r'\b[a-z]{2,}\b', text.lower())
    return [w for w in words if w not in STOP and len(w) > 2][:32]

def inject_words_into_field(conn: sqlite3.Connection, words: List[str], source: str="user") -> List[Tuple]:
    cur = conn.cursor()
    ts = int(time.time())
    out = []
    for w in words:
        cur.execute("""
          SELECT cell_id, fitness FROM field_cells
          WHERE cell_id LIKE ? AND status='alive'
          ORDER BY id DESC LIMIT 1
        """, (f"%{w}%",))
        row = cur.fetchone()
        if row:
            cell_id, old_fit = row
            new_fit = min(1.0, (old_fit or 0.5) + 0.15)
            cur.execute("""
              UPDATE field_cells
              SET fitness=?, resonance_score=COALESCE(resonance_score,0)+0.1
              WHERE cell_id=? AND status='alive'
            """, (new_fit, cell_id))
            out.append((w, "BOOSTED", new_fit, source))
        else:
            cell_id = f"{source}_{w}_{ts}"
            fit = random.uniform(0.65, 0.85) if source=="repo" else random.uniform(0.6, 0.9)
            res = random.uniform(0.5, 0.8)
            cur.execute("""
              INSERT INTO field_cells (cell_id, age, resonance_score, fitness, status, timestamp)
              VALUES (?, 0, ?, ?, 'alive', ?)
            """, (cell_id, res, fit, ts))
            out.append((w, "BORN", fit, source))
            (_user_words if source=="user" else _repo_words).append(w)
    conn.commit()
    return out

# ========= INPUT THREAD =========
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

# ========= DB FETCH =========
def fetch_state(conn):
    cur = conn.cursor()
    cur.execute("""
      SELECT iteration, cell_count, avg_resonance, avg_age, births, deaths
      FROM field_state ORDER BY id DESC LIMIT 1
    """)
    r = cur.fetchone()
    return r if r else (0,0,0.0,0.0,0,0)

def fetch_cells(conn, limit=60):
    cur = conn.cursor()
    cur.execute("""
      SELECT cell_id, age, COALESCE(resonance_score,0.0), COALESCE(fitness,0.0)
      FROM field_cells WHERE status='alive'
      ORDER BY id DESC LIMIT ?
    """, (limit,))
    return cur.fetchall()

def fetch_history(conn, limit=15):
    cur = conn.cursor()
    cur.execute("""
      SELECT iteration, cell_count, avg_resonance
      FROM field_state ORDER BY id DESC LIMIT ?
    """, (limit,))
    return list(reversed(cur.fetchall()))

# ========= COLORS / SYMBOLS =========
def is_user_cell(cid: str) -> bool:
    return cid.startswith("user_") or any(w in cid for w in _user_words)
def is_repo_cell(cid: str) -> bool:
    return cid.startswith("repo_") or any(w in cid for w in _repo_words)

def color_and_symbol(cid: str, fit: float):
    if is_user_cell(cid): return COLORS["user"], STATUS["user"]
    if is_repo_cell(cid): return COLORS["repo"], STATUS["repo"]
    if fit > 0.75: return COLORS["high"], STATUS["high"]
    if fit > 0.55: return COLORS["medium"], STATUS["med"]
    if fit > 0.35: return COLORS["low"], STATUS["low"]
    if fit > 0.15: return COLORS["low"], STATUS["min"]
    return COLORS["dead"], STATUS["dead"]

# ========= GRID =========
def hsh(s: str, mod: int) -> int:
    return int.from_bytes(blake2b(s.encode("utf-8"), digest_size=8).digest(),"little") % max(1, mod)

def base_pos(cid: str, w: int, h: int):
    return hsh(cid+"_x", w), hsh(cid+"_y", h)

def drift_offset(cid: str, t: float, res: float):
    if not ENABLE_DRIFT: return (0,0)
    r = max(0.0, min(1.0, res))
    amp = 1.0 + 2.0*r
    kx = 0.6 + 0.5*(hsh(cid+"_kx", 100)/100.0)
    ky = 0.6 + 0.5*(hsh(cid+"_ky", 100)/100.0)
    dx = int(round(math.sin(t*kx + hsh(cid+"_px", 1000)/90.0)*amp))
    dy = int(round(math.cos(t*ky + hsh(cid+"_py", 1000)/110.0)*amp))
    return (dx, dy)

def place_cells_on_grid(cells, w, h, t):
    grid = [[" " for _ in range(w)] for _ in range(h)]
    prio = [[-1 for _ in range(w)] for _ in range(h)]
    def src_pri(cid):
        if is_user_cell(cid): return 3
        if is_repo_cell(cid): return 2
        return 1
    for (cid, age, res, fit) in cells:
        x0, y0 = base_pos(cid, w, h)
        dx, dy = drift_offset(cid, t, res)
        x = max(0, min(w-1, x0+dx))
        y = max(0, min(h-1, y0+dy))
        col, sym = color_and_symbol(cid, fit)
        if ENABLE_BREATH and not (is_user_cell(cid) or is_repo_cell(cid)):
            shade = math.sin(_breath_phase*2*math.pi)*0.5 + 0.5
            sym = STATUS["high"] if (fit>0.75 and shade>0.66) else \
                  STATUS["med"]  if (fit>0.55 and shade>0.33) else \
                  STATUS["low"]  if (fit>0.35) else STATUS["min"]
        p = src_pri(cid)
        if p >= prio[y][x]:
            prio[y][x] = p
            grid[y][x] = f"{col}{sym}{RESET}" if ENABLE_COLOR else sym
    return grid

# ========= SMALL RENDER HELPERS =========
def sparkline(hist):
    if len(hist) < 2: return ""
    pops = [h[1] for h in hist]
    mx = max(pops) if pops else 1
    chars = "▁▂▃▄▅▆▇█"
    s = []
    for p in pops:
        idx = int((p/mx)*(len(chars)-1)) if mx>0 else 0
        s.append(chars[idx])
    return "".join(s)

def bell(n=1):
    if not ENABLE_SOUND: return
    sys.stdout.write('\a'*n)
    sys.stdout.flush()

def boxed_title(title: str):
    """ASCII-only title inside a perfectly aligned box."""
    inner = BANNER_W - 2
    print(f"{BOLD}{COLORS['banner']}╔" + "═"*inner + f"╗{RESET}")
    print(f"{BOLD}{COLORS['banner']}║" + title.center(inner) + f"║{RESET}")
    print(f"{BOLD}{COLORS['banner']}╚" + "═"*inner + f"╝{RESET}")

def hr():
    print("─"*BANNER_W)

# ========= FRAME =========
def draw_frame(conn, cells, iteration, metrics, injected, hist):
    global _last_births, _last_deaths

    os.system("clear" if os.name != "nt" else "cls")
    # фиксированный верхний отступ
    if TOP_PAD: print("\n"*TOP_PAD, end="")

    cell_count, avg_r, avg_age, births, deaths = metrics

    # звуки по событиям
    if births > _last_births: bell(1)
    if deaths > _last_deaths and cell_count > 0: bell(2)
    if cell_count == 0: bell(3)
    _last_births, _last_deaths = births, deaths

    # Заголовок (ASCII — без эмодзи)
    boxed_title("ASYNC FIELD FOREVER (HYBRID)")

    # Метрики (укладываемся в ширину)
    print(f"Iter:{iteration:<6} | Pop:{cell_count:<3} | Res:{avg_r:0.2f} | Age:{avg_age:0.1f} | Births:{births} | Deaths:{deaths}")

    # Pulse bar
    pw = int(max(0, min(1, avg_r)) * PULSE_BAR_W)
    bar = COLORS["high"] + "█"*pw + RESET + "░"*(PULSE_BAR_W-pw)
    print(f"Pulse: {bar}")

    sp = sparkline(hist)
    if sp:
        print(f"Hist:  {COLORS['medium']}{sp}{RESET}")

    # Инъекции (показываем по 2)
    if injected:
        user_inj = [i for i in injected if i[3]=="user"][:2]
        repo_inj = [i for i in injected if i[3]=="repo"][:2]
        if user_inj:
            print(f"{COLORS['user']}★ You:{RESET}")
            for w, act, ft, _ in user_inj:
                sym = "★" if act=="BORN" else "↑"
                print(f"  {sym} {w} ({ft:.2f})")
        if repo_inj:
            print(f"{COLORS['repo']}◆ Repo:{RESET}")
            for w, act, ft, _ in repo_inj:
                sym = "◆" if act=="BORN" else "↑"
                print(f"  {sym} {w} ({ft:.2f})")

    # GRID — строго по центру
    grid = place_cells_on_grid(cells, GRID_W, GRID_H, time.time()*0.6)
    left = max(0, (BANNER_W - GRID_W)//2)
    title = f"{DIM}- grid -{RESET}".center(GRID_W)
    print("\n" + " "*left + title)
    for row in grid:
        print(" "*left + "".join(row))

    # Список ячеек (верхние несколько)
    hr()
    if not cells:
        print(f"{COLORS['dead']}Field is empty. Type to seed it.{RESET}")
    else:
        for (cid, age, res, fit) in cells[:CELL_LIST_LIM]:
            col, sym = color_and_symbol(cid, fit)
            word = cid
            if cid.startswith("user_") or cid.startswith("repo_"):
                parts = cid.split("_")
                if len(parts) > 1: word = parts[1]
            word = (word[:16] + "…") if len(word) > 16 else word
            src = "U" if is_user_cell(cid) else ("R" if is_repo_cell(cid) else "O")
            print(f"{col}{sym}{RESET} {src} {word:<18} f:{fit:0.2f}  r:{res:0.2f}  a:{age}")

    # Легенда и время
    hr()
    print(f"{COLORS['user']}★ Your words  {COLORS['repo']}◆ Repo changes  {COLORS['high']}█ Organic{RESET}")
    print(datetime.now().strftime("%H:%M:%S"))

    # Промпт в начале строки (никакого центрирования)
    print("> ", end="", flush=True)

# ========= MAIN =========
def fetch_repo_changes(monitor) -> List[str]:
    if not monitor: return []
    try:
        changes = monitor.fetch_repo_context(limit=5)
        words = []
        for ch in changes:
            content = ch.get('content', '')
            words.extend(extract_words(content)[:3])
        uniq, seen = [], set()
        for w in words:
            if w not in seen:
                seen.add(w); uniq.append(w)
            if len(uniq) >= 10: break
        return uniq
    except Exception:
        return []

def main():
    global _running, _input_buffer, _breath_phase

    # верхняя техническая шапка
    print(f"{BOLD}{COLORS['banner']}" + "="*BANNER_W + RESET)
    print(f"{BOLD}{COLORS['banner']}" + " FIELD VISUALISER v7.4 ".center(BANNER_W) + RESET)
    print(f"{BOLD}{COLORS['banner']}" + "="*BANNER_W + RESET)
    print(f"Terminal: {CFG['term_w']}x{CFG['term_h']} | Banner:{BANNER_W} | Grid:{GRID_W}x{GRID_H}")
    print(f"DB: {ACTIVE_DB}")
    repo_monitor = init_repo_monitor()
    print(f"Repo monitor: {'ON' if repo_monitor else 'OFF'}")
    print("\nType to inject words. Starting in 3s...\n")
    time.sleep(3)

    threading.Thread(target=input_thread, daemon=True).start()
    conn = sqlite3.connect(ACTIVE_DB)

    last_refresh = 0.0
    try:
        while _running:
            now = time.time()
            _breath_phase = (_breath_phase + FRAME_DT) % 1.0

            if now - last_refresh >= UI_REFRESH:
                injected = []

                if _input_buffer:
                    txt = _input_buffer.pop(0)
                    ws = extract_words(txt)
                    if ws:
                        injected += inject_words_into_field(conn, ws, source="user")

                if repo_monitor:
                    ws = fetch_repo_changes(repo_monitor)
                    if ws:
                        injected += inject_words_into_field(conn, ws, source="repo")

                it, cc, ar, aa, b, d = fetch_state(conn)
                cells = fetch_cells(conn, limit=GRID_W*GRID_H)
                hist  = fetch_history(conn, limit=20)

                draw_frame(conn, cells, it, (cc, ar, aa, b, d), injected if injected else None, hist)
                last_refresh = now

            time.sleep(FRAME_DT)
    except KeyboardInterrupt:
        _running = False
        print(f"\n{COLORS['banner']}Stopped. 🧬⚡{RESET}\n")
    finally:
        conn.close()

if __name__ == "__main__":
    main()