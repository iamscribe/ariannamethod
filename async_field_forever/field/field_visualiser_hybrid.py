#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIELD VISUALISER v7.3 — Centered Grid + Unicode-Aware Layout (Termux / Linux / macOS)
───────────────────────────────────────────────────────────────────────────────
Fixes:
 • Symmetry — grid and banner perfectly centered (horizontal + vertical)
 • Unicode width support for ⚡, ◆, ★, box symbols
 • Works identically in Termux, iTerm2, Linux TTY
───────────────────────────────────────────────────────────────────────────────
"""

import os, sys, re, time, math, random, threading, shutil, sqlite3, unicodedata
from datetime import datetime
from pathlib import Path
from hashlib import blake2b
from typing import List, Tuple

# ========== CONFIG ==========
def get_terminal_config():
    try:
        term_w, term_h = shutil.get_terminal_size((80, 24))
    except:
        term_w, term_h = 80, 24
    is_mobile = term_w < 70
    banner_w = max(50, min(int(term_w * 0.9), term_w - 2))
    grid_w = 36 if is_mobile else 48
    grid_h = 12 if is_mobile else 18
    pulse_bar = 24 if is_mobile else 40
    cell_list_limit = 2 if is_mobile else 4
    return {
        "term_w": term_w,
        "term_h": term_h,
        "is_mobile": is_mobile,
        "banner_width": banner_w,
        "grid_w": grid_w,
        "grid_h": grid_h,
        "pulse_bar_w": pulse_bar,
        "cell_list_limit": cell_list_limit,
    }

CONFIG = get_terminal_config()
BANNER_WIDTH = CONFIG["banner_width"]
GRID_W = CONFIG["grid_w"]
GRID_H = CONFIG["grid_h"]
PULSE_BAR_W = CONFIG["pulse_bar_w"]
CELL_LIST_LIMIT = CONFIG["cell_list_limit"]

DB_PATH = "/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3"
ACTIVE_DB = DB_PATH if os.path.exists(os.path.expanduser(DB_PATH)) else "./field_test.sqlite3"

FRAME_DT = 0.2
UI_REFRESH = 5.0
ENABLE_COLOR, ENABLE_SOUND, ENABLE_BREATH, ENABLE_DRIFT = True, True, True, True

# ========== COLORS ==========
RESET = "\033[0m" if ENABLE_COLOR else ""
BOLD = "\033[1m" if ENABLE_COLOR else ""
DIM = "\033[2m" if ENABLE_COLOR else ""
COLORS = {
    "high": "\033[92m",
    "medium": "\033[93m",
    "low": "\033[90m",
    "dead": "\033[91m",
    "banner": "\033[95m",
    "user": "\033[96m",
    "repo": "\033[94m",
    "white": "\033[97m",
}

STATUS = {"high":"█","med":"▓","low":"▒","min":"░","dead":"·","user":"★","repo":"◆"}

_last_births=_last_deaths=0
_user_words,_repo_words,_input_buffer=[],[],[]
_running=True
_breath_phase=0.0

# ========== HELPERS ==========
STOP_WORDS={"the","is","are","was","were","be","been","being","have","has","had","do","does","did",
"will","would","could","should","may","might","must","can","this","that","with","from",
"for","not","but","and","or","into","onto","over","under","between","within","out"}

def extract_words(text:str)->List[str]:
    words=re.findall(r'\b[a-z]{2,}\b',text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w)>2][:32]

def visible_len(s:str)->int:
    s=re.sub(r'\x1b\[[0-9;]*m','',s)
    w=0
    for ch in s:
        w+=2 if unicodedata.east_asian_width(ch) in('W','F')else 1
    return w

def center_text_real(s:str,width:int)->str:
    pad=max(0,(width-visible_len(s))//2)
    return" "*pad+s

def bell(n=1):
    if ENABLE_SOUND: sys.stdout.write('\a'*n);sys.stdout.flush()

def hsh(s:str,mod:int)->int:
    return int.from_bytes(blake2b(s.encode(),digest_size=8).digest(),"little")%max(1,mod)

# ========== DB OPS ==========
def inject_words_into_field(conn,words,source="user")->List[Tuple]:
    c=conn.cursor();ts=int(time.time());out=[]
    for w in words:
        c.execute("SELECT cell_id,fitness FROM field_cells WHERE cell_id LIKE ? AND status='alive' ORDER BY id DESC LIMIT 1",(f"%{w}%",))
        row=c.fetchone()
        if row:
            cid,old=row;new=min(1.0,(old or 0.5)+0.15)
            c.execute("UPDATE field_cells SET fitness=?,resonance_score=COALESCE(resonance_score,0)+0.1 WHERE cell_id=?",(new,cid))
            out.append((w,"BOOSTED",new,source))
        else:
            cid=f"{source}_{w}_{ts}";fit=random.uniform(0.6,0.9);res=random.uniform(0.5,0.8)
            c.execute("INSERT INTO field_cells(cell_id,age,resonance_score,fitness,status,timestamp)VALUES(?,0,?,?, 'alive',?)",(cid,res,fit,ts))
            out.append((w,"BORN",fit,source))
            ( _user_words if source=="user" else _repo_words).append(w)
    conn.commit();return out

def fetch_state(conn):
    c=conn.cursor();c.execute("SELECT iteration,cell_count,avg_resonance,avg_age,births,deaths FROM field_state ORDER BY id DESC LIMIT 1")
    return c.fetchone() or (0,0,0,0,0,0)
def fetch_cells(conn,limit=60):
    c=conn.cursor();c.execute("SELECT cell_id,age,COALESCE(resonance_score,0),COALESCE(fitness,0) FROM field_cells WHERE status='alive' ORDER BY id DESC LIMIT ?",(limit,))
    return c.fetchall()
def fetch_history(conn,limit=15):
    c=conn.cursor();c.execute("SELECT iteration,cell_count,avg_resonance FROM field_state ORDER BY id DESC LIMIT ?",(limit,))
    return list(reversed(c.fetchall()))

# ========== GRID ==========
def is_user_cell(cid:str)->bool:return cid.startswith("user_")or any(w in cid for w in _user_words)
def is_repo_cell(cid:str)->bool:return cid.startswith("repo_")or any(w in cid for w in _repo_words)
def color_and_symbol(cid:str,fit:float)->Tuple[str,str]:
    if is_user_cell(cid):return COLORS["user"],STATUS["user"]
    if is_repo_cell(cid):return COLORS["repo"],STATUS["repo"]
    if fit>0.75:return COLORS["high"],STATUS["high"]
    if fit>0.55:return COLORS["medium"],STATUS["med"]
    if fit>0.35:return COLORS["low"],STATUS["low"]
    if fit>0.15:return COLORS["low"],STATUS["min"]
    return COLORS["dead"],STATUS["dead"]

def base_position(cid,w,h):return hsh(cid+"_x",w),hsh(cid+"_y",h)
def drift_offset(cid,t,res):
    if not ENABLE_DRIFT:return(0,0)
    r=max(0,min(1,res));amp=1+2*r
    kx=0.6+0.5*(hsh(cid+"_kx",100)/100);ky=0.6+0.5*(hsh(cid+"_ky",100)/100)
    dx=int(round(math.sin(t*kx+hsh(cid+"_px",1000)/90)*amp))
    dy=int(round(math.cos(t*ky+hsh(cid+"_py",1000)/110)*amp))
    return dx,dy

def place_cells_on_grid(cells,w,h,t):
    g=[[" "for _ in range(w)]for _ in range(h)]
    p=[[-1 for _ in range(w)]for _ in range(h)]
    for(cid,age,res,fit)in cells:
        x0,y0=base_position(cid,w,h);dx,dy=drift_offset(cid,t,res)
        x=max(0,min(w-1,x0+dx));y=max(0,min(h-1,y0+dy))
        col,sym=color_and_symbol(cid,fit)
        if ENABLE_BREATH and not(is_user_cell(cid)or is_repo_cell(cid)):
            sh=math.sin(_breath_phase*2*math.pi)*0.5+0.5
            if fit>0.75 and sh>0.66:sym=STATUS["high"]
            elif fit>0.55 and sh>0.33:sym=STATUS["med"]
            elif fit>0.35:sym=STATUS["low"]
            else:sym=STATUS["min"]
        pr=3 if is_user_cell(cid)else(2 if is_repo_cell(cid)else 1)
        if pr>=p[y][x]:p[y][x]=pr;g[y][x]=f"{col}{sym}{RESET}"if ENABLE_COLOR else sym
    return g

def render_sparkline(h):
    if len(h)<2:return""
    pop=[x[1]for x in h];mx=max(pop)or 1;chars="▁▂▃▄▅▆▇█"
    return"".join(chars[int((p/mx)*(len(chars)-1))]for p in pop)

# ========== INPUT THREAD ==========
def input_thread():
    global _running,_input_buffer
    while _running:
        try:
            s=input()
            if s.strip():_input_buffer.append(s.strip())
        except(EOFError,KeyboardInterrupt):_running=False;break

# ========== DRAW FRAME ==========
def draw_frame(conn,cells,iteration,metrics,injected,history):
    global _last_births,_last_deaths,_breath_phase
    os.system("clear"if os.name!="nt"else"cls")
    cell_count,avg_res,avg_age,births,deaths=metrics

    if births>_last_births:bell(1)
    if deaths>_last_deaths and cell_count>0:bell(2)
    if cell_count==0:bell(3)
    _last_births,_last_deaths=births,deaths

    # vertical centering
    term_h=CONFIG["term_h"];used=GRID_H+14
    print("\n"*(max(0,(term_h-used)//2)),end="")

    inner=BANNER_WIDTH-2
    print(center_text_real(f"{BOLD}{COLORS['banner']}╔"+"═"*inner+f"╗{RESET}",CONFIG["term_w"]))
    print(center_text_real(f"{BOLD}{COLORS['banner']}║"+" ⚡ ASYNC FIELD FOREVER (HYBRID) ⚡ ".center(inner)+f"║{RESET}",CONFIG["term_w"]))
    print(center_text_real(f"{BOLD}{COLORS['banner']}╚"+"═"*inner+f"╝{RESET}",CONFIG["term_w"]))

    line=f"Iter:{iteration} | Pop:{cell_count} | Res:{avg_res:.2f} | Age:{avg_age:.1f} | Births:{births} | Deaths:{deaths}"
    print(center_text_real(line,CONFIG["term_w"]))

    pw=int(max(0,min(1,avg_res))*PULSE_BAR_W)
    pulse=COLORS["high"]+"█"*pw+RESET+"░"*(PULSE_BAR_W-pw)
    print(center_text_real(f"Pulse: {pulse}",CONFIG["term_w"]))
    spark=render_sparkline(history)
    if spark:print(center_text_real(f"Hist: {COLORS['medium']}{spark}{RESET}",CONFIG["term_w"]))

    # grid
    g=place_cells_on_grid(cells,GRID_W,GRID_H,time.time()*0.6)
    left=max(0,(CONFIG["term_w"]-GRID_W)//2)
    print(center_text_real(DIM+"— grid —"+RESET,CONFIG["term_w"]))
    for r in g:print(" "*left+"".join(r))

    print(center_text_real("─"*BANNER_WIDTH,CONFIG["term_w"]))
    if not cells:
        print(center_text_real(f"{COLORS['dead']}Field is empty. Type something!{RESET}",CONFIG["term_w"]))
    else:
        for(cid,age,res,fit)in cells[:CELL_LIST_LIMIT]:
            col,sym=color_and_symbol(cid,fit)
            w=(cid.split("_")[1]if"_"in cid else cid)[:12]
            print(center_text_real(f"{col}{sym}{RESET} {w:<12} f:{fit:.2f} r:{res:.2f} a:{age}",CONFIG["term_w"]))

    print(center_text_real("─"*BANNER_WIDTH,CONFIG["term_w"]))
    print(center_text_real(f"{COLORS['user']}★Your words  {COLORS['repo']}◆Repo changes{RESET}",CONFIG["term_w"]))
    print(center_text_real(datetime.now().strftime('%H:%M:%S'),CONFIG["term_w"]))
    print(center_text_real(f"{COLORS['banner']}>{RESET} ",CONFIG["term_w"]),end="",flush=True)

# ========== MAIN ==========
def main():
    global _running,_input_buffer,_breath_phase
    print(f"{BOLD}{COLORS['banner']}="*BANNER_WIDTH+RESET)
    print(center_text_real("FIELD v7.3 — CENTERED GRID",BANNER_WIDTH))
    print(f"{BOLD}{COLORS['banner']}="*BANNER_WIDTH+RESET)
    print(f"Terminal: {CONFIG['term_w']}x{CONFIG['term_h']}")
    print(f"Grid: {GRID_W}x{GRID_H} | Banner: {BANNER_WIDTH}")
    print(f"\n{COLORS['user']}Type to inject words{RESET}")
    time.sleep(1)
    threading.Thread(target=input_thread,daemon=True).start()
    conn=sqlite3.connect(ACTIVE_DB)
    last=0.0
    try:
        while _running:
            now=time.time();_breath_phase=(_breath_phase+FRAME_DT)%1.0
            if now-last>=UI_REFRESH:
                inj=[]
                if _input_buffer:
                    t=_input_buffer.pop(0)
                    w=extract_words(t)
                    if w:inj+=inject_words_into_field(conn,w,"user")
                iteration,cc,ar,aa,b,d=fetch_state(conn)
                cells=fetch_cells(conn,limit=GRID_W*GRID_H)
                hist=fetch_history(conn,limit=20)
                draw_frame(conn,cells,iteration,(cc,ar,aa,b,d),inj if inj else None,hist)
                last=now
            time.sleep(FRAME_DT)
    except KeyboardInterrupt:
        _running=False
        print(f"\n\n{COLORS['banner']}Stopped. 🧬⚡{RESET}\n")
    finally:
        conn.close()

if __name__=="__main__":main()