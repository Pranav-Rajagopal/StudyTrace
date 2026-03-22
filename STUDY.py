"""
StudyTrace  —  12th Boards Ultimate Study Tracker
Fixed for Python 3.13 on Linux
No Canvas-based buttons (they crash on some Linux/Tk builds)
Rounded cards via Canvas background only · Live timer · Pomodoro
Circular rings · Streak · Exam countdown
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import json, os, math, time
from datetime import datetime, timedelta, date

# ══════════════════════════════════════════════
#  PALETTE
# ══════════════════════════════════════════════
BG    = "#09090f"
CARD  = "#111119"
CARD2 = "#181822"
CARD3 = "#20202e"
BDR   = "#28283a"
W     = "#f0f0fa"
G1    = "#8888aa"
G2    = "#44445a"
G3    = "#1e1e2a"

ACC   = "#5b9cf6"
GRN   = "#34d399"
RED   = "#f87171"
AMB   = "#fbbf24"
PUR   = "#a78bfa"

SUBJ_CLR = {
    "Maths":            "#5b9cf6",
    "Physics":          "#a78bfa",
    "Chemistry":        "#34d399",
    "English":          "#fbbf24",
    "Computer Science": "#f87171",
}
SUBJECTS = list(SUBJ_CLR.keys())

FNT = {
    "giant": ("Helvetica", 48, "bold"),
    "h1":    ("Helvetica", 26, "bold"),
    "h2":    ("Helvetica", 19, "bold"),
    "h3":    ("Helvetica", 14, "bold"),
    "body":  ("Helvetica", 13),
    "bodyb": ("Helvetica", 13, "bold"),
    "sm":    ("Helvetica", 11),
    "smb":   ("Helvetica", 11, "bold"),
    "xs":    ("Helvetica", 10),
    "timer": ("Helvetica", 54, "bold"),
    "pomo":  ("Helvetica", 36, "bold"),
}

DATA_FILE  = "study_data.json"
GOALS_FILE = "study_goals.json"
EXAM_FILE  = "study_exams.json"

# ══════════════════════════════════════════════
#  DATA HELPERS
# ══════════════════════════════════════════════
def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default

def save_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)

def today_str():
    return date.today().isoformat()

def fmt(minutes):
    minutes = int(minutes)
    h, m = divmod(minutes, 60)
    if h and m: return f"{h}h {m}m"
    if h:       return f"{h}h"
    return f"{m}m"

def fmt_hms(seconds):
    h, r = divmod(int(seconds), 3600)
    m, s = divmod(r, 60)
    if h: return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def get_stats(data):
    today       = date.today()
    week_start  = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    year_start  = today.replace(month=1, day=1)
    td = wk = mo = yr = days_count = 0
    for ds, sessions in data.items():
        try: d = date.fromisoformat(ds)
        except: continue
        m = sum(sessions.values())
        if m > 0: days_count += 1
        if d == today:       td += m
        if d >= week_start:  wk += m
        if d >= month_start: mo += m
        if d >= year_start:  yr += m
    avg = yr // days_count if days_count else 0
    return td, wk, mo, yr, avg

def get_streak(data):
    today = date.today()
    streak = 0
    d = today
    while True:
        sessions = data.get(d.isoformat(), {})
        if sum(sessions.values()) > 0:
            streak += 1
            d -= timedelta(days=1)
        else:
            break
    return streak

def get_week_days(data):
    today = date.today()
    result = []
    for i in range(7):
        d = today - timedelta(days=6 - i)
        s = data.get(d.isoformat(), {})
        result.append((d, sum(s.values())))
    return result

def get_subject_week(data, subject):
    today      = date.today()
    week_start = today - timedelta(days=today.weekday())
    total = 0
    for ds, sessions in data.items():
        try: d = date.fromisoformat(ds)
        except: continue
        if d >= week_start:
            total += sessions.get(subject, 0)
    return total

# ══════════════════════════════════════════════
#  ROUNDED CARD  (Canvas bg only — safe)
# ══════════════════════════════════════════════
def rounded_rect(canvas, x1, y1, x2, y2, r=14, **kw):
    pts = [
        x1+r, y1,   x2-r, y1,
        x2,   y1,   x2,   y1+r,
        x2,   y2-r, x2,   y2,
        x2-r, y2,   x1+r, y2,
        x1,   y2,   x1,   y2-r,
        x1,   y1+r, x1,   y1,
        x1+r, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


class RCard(tk.Frame):
    """
    Rounded card using a Canvas as the background layer
    and a normal tk.Frame on top for widgets.
    Avoids the Canvas.delete() crash on Python 3.13/Linux
    by using a single persistent background canvas.
    """
    def __init__(self, parent, radius=14, bg_color=CARD,
                 border_color=BDR, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._r  = radius
        self._bg = bg_color
        self._bc = border_color

        self._bg_canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self._bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._inner = tk.Frame(self, bg=bg_color)
        self._inner.place(relx=0, rely=0, relwidth=1, relheight=1,
                          x=1, y=1, width=-2, height=-2)

        self.bind("<Configure>", self._redraw)

    def _redraw(self, e=None):
        c = self._bg_canvas
        c.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 4 or h < 4:
            return
        rounded_rect(c, 0, 0, w, h, self._r,
                     fill=self._bc, outline="")
        rounded_rect(c, 1, 1, w-1, h-1, self._r-1,
                     fill=self._bg, outline="")

    def inner(self):
        return self._inner


# ══════════════════════════════════════════════
#  SMOOTH PROGRESS BAR  (Frame-based, no Canvas)
# ══════════════════════════════════════════════
class SmoothBar(tk.Frame):
    def __init__(self, parent, color=ACC, height=8, **kw):
        super().__init__(parent, bg=G3, height=height, **kw)
        self.pack_propagate(False)
        self._color = color
        self._pct   = 0.0
        self._tgt   = 0.0
        self._fill  = tk.Frame(self, bg=color, height=height)
        self._fill.place(x=0, y=0, relheight=1.0, relwidth=0.0)

    def set_value(self, pct):
        self._tgt = max(0.0, min(1.0, pct))
        self._anim()

    def _anim(self):
        diff = self._tgt - self._pct
        if abs(diff) < 0.006:
            self._pct = self._tgt
            self._fill.place(relwidth=self._pct)
            return
        self._pct += diff * 0.16
        self._fill.place(relwidth=self._pct)
        try:
            self.after(16, self._anim)
        except Exception:
            pass

    def set_color(self, c):
        self._color = c
        self._fill.config(bg=c)


# ══════════════════════════════════════════════
#  CIRCULAR RING  (Canvas arc — drawing only, no delete loop)
# ══════════════════════════════════════════════
class Ring(tk.Canvas):
    def __init__(self, parent, size=100, thick=10,
                 track=G3, color=ACC, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=BG, highlightthickness=0, **kw)
        self._size  = size
        self._thick = thick
        self._track = track
        self._color = color
        self._pct   = 0.0
        self._tgt   = 0.0
        self._r     = (size - thick) // 2
        self._cx    = size // 2
        self._cy    = size // 2
        self._arc_id   = None
        self._track_id = None
        self._redraw()

    def _redraw(self):
        self.delete("all")
        cx, cy, r, t = self._cx, self._cy, self._r, self._thick
        self.create_oval(cx-r-t//2, cy-r-t//2,
                         cx+r+t//2, cy+r+t//2,
                         outline=self._track, width=t, fill="")
        if self._pct > 0.005:
            extent = -self._pct * 359.9
            self.create_arc(cx-r-t//2, cy-r-t//2,
                            cx+r+t//2, cy+r+t//2,
                            start=90, extent=extent,
                            outline=self._color, width=t, style="arc")

    def set_value(self, pct, animate=True):
        self._tgt = max(0.0, min(1.0, pct))
        if animate:
            self._anim()
        else:
            self._pct = self._tgt
            self._redraw()

    def _anim(self):
        diff = self._tgt - self._pct
        if abs(diff) < 0.008:
            self._pct = self._tgt
            self._redraw()
            return
        self._pct += diff * 0.14
        self._redraw()
        try:
            self.after(16, self._anim)
        except Exception:
            pass

    def set_color(self, c):
        self._color = c
        self._redraw()


# ══════════════════════════════════════════════
#  TOAST
# ══════════════════════════════════════════════
def toast(root, msg, color=GRN, ms=2400):
    try:
        t = tk.Toplevel(root)
        t.overrideredirect(True)
        t.attributes("-topmost", True)
        t.configure(bg=CARD2)

        inner = tk.Frame(t, bg=CARD2)
        inner.pack(padx=2, pady=2)
        tk.Frame(inner, bg=color, height=3).pack(fill="x")
        tk.Label(inner, text=f"  {msg}  ",
                 font=FNT["bodyb"], bg=CARD2, fg=color,
                 padx=16, pady=12).pack()

        root.update_idletasks()
        rx = root.winfo_x() + root.winfo_width() // 2
        ry = root.winfo_y() + 72
        t.update_idletasks()
        w = t.winfo_reqwidth()
        t.geometry(f"+{rx - w//2}+{ry}")
        t.after(ms, t.destroy)
    except Exception:
        pass


# ══════════════════════════════════════════════
#  PILL LABEL BUTTON  (tk.Label based — no Canvas)
# ══════════════════════════════════════════════
def pill_btn(parent, text, command, bg=ACC, fg=BG,
             font=None, padx=20, pady=10):
    """Simple rounded-looking button using tk.Label."""
    font = font or FNT["bodyb"]
    b = tk.Label(parent, text=text, font=font,
                 bg=bg, fg=fg,
                 padx=padx, pady=pady,
                 cursor="hand2")
    b.bind("<Button-1>",      lambda e: command())
    b.bind("<Enter>",         lambda e: _btn_hover(b, bg, True))
    b.bind("<Leave>",         lambda e: _btn_hover(b, bg, False))
    b.bind("<ButtonPress-1>", lambda e: b.config(relief="sunken"))
    b.bind("<ButtonRelease-1>", lambda e: b.config(relief="flat"))
    b.config(relief="flat")
    return b

def _btn_hover(btn, base_color, entering):
    try:
        h = base_color.lstrip("#")
        r, g, b_ = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        amt = 30 if entering else 0
        r = min(255, r+amt); g = min(255, g+amt); b_ = min(255, b_+amt)
        btn.config(bg=f"#{r:02x}{g:02x}{b_:02x}")
    except Exception:
        pass


# ══════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════
class StudyTrace(tk.Tk):
    def __init__(self):
        super().__init__()
        self.data  = load_json(DATA_FILE,  {})
        self.goals = load_json(GOALS_FILE, {s: 2.0 for s in SUBJECTS})
        self.exams = load_json(EXAM_FILE,  [])

        self._timer_running = False
        self._timer_start   = 0
        self._timer_elapsed = 0
        self._timer_subject = SUBJECTS[0]

        self._pomo_running  = False
        self._pomo_start    = 0
        self._pomo_duration = 25 * 60
        self._pomo_is_break = False
        self._pomo_count    = 0

        self._cur_page = None

        self.title("StudyTrace  ·  12th Boards")
        self.geometry("1150x800")
        self.minsize(1000, 700)
        self.configure(bg=BG)
        self.resizable(True, True)

        self._build()
        self._show("dashboard")

    # ══════════════════════════════════════════
    #  SHELL
    # ══════════════════════════════════════════
    def _build(self):
        self._build_topbar()
        self._content = tk.Frame(self, bg=BG)
        self._content.pack(fill="both", expand=True, padx=22, pady=(10, 18))
        self._pages = {}
        for key, fn in [
            ("dashboard", self._build_dashboard),
            ("timer",     self._build_timer),
            ("history",   self._build_history),
            ("goals",     self._build_goals),
            ("exams",     self._build_exams),
        ]:
            f = tk.Frame(self._content, bg=BG)
            self._pages[key] = f
            fn(f)

    # ── Top bar ───────────────────────────────
    def _build_topbar(self):
        bar = tk.Frame(self, bg=CARD, height=62)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Logo
        lf = tk.Frame(bar, bg=CARD)
        lf.pack(side="left", padx=22, pady=12)
        tk.Label(lf, text="StudyTrace", font=FNT["h2"],
                 bg=CARD, fg=W).pack(side="left")
        tk.Label(lf, text="  12th Boards", font=FNT["body"],
                 bg=CARD, fg=G2).pack(side="left")

        # Nav
        nav = tk.Frame(bar, bg=CARD2, padx=4, pady=4)
        nav.pack(side="left", padx=22, pady=14)

        self._nav_btns = {}
        for key, label in [
            ("dashboard","Dashboard"), ("timer","Timer"),
            ("history","History"),     ("goals","Goals"),
            ("exams","Exams"),
        ]:
            b = tk.Label(nav, text=label, font=FNT["bodyb"],
                         bg=CARD2, fg=G1,
                         padx=16, pady=7, cursor="hand2")
            b.pack(side="left", padx=2)
            b.bind("<Button-1>", lambda e, k=key: self._show(k))
            b.bind("<Enter>",    lambda e, btn=b, k=key:
                   btn.config(fg=W) if self._cur_page != k else None)
            b.bind("<Leave>",    lambda e, btn=b, k=key:
                   btn.config(fg=G1) if self._cur_page != k else None)
            self._nav_btns[key] = b

        # Right: streak + clock
        right = tk.Frame(bar, bg=CARD)
        right.pack(side="right", padx=22)
        self._streak_lbl = tk.Label(right, text="Streak: 0 days",
                                     font=FNT["bodyb"], bg=CARD, fg=AMB)
        self._streak_lbl.pack(side="right", padx=(14, 0))
        self._clock_var = tk.StringVar()
        tk.Label(right, textvariable=self._clock_var,
                 font=FNT["body"], bg=CARD, fg=G1).pack(side="right")
        self._tick_clock()

    def _show(self, key):
        if self._cur_page:
            self._pages[self._cur_page].pack_forget()
        self._pages[key].pack(fill="both", expand=True)
        self._cur_page = key
        for k, b in self._nav_btns.items():
            b.config(bg=BDR if k == key else CARD2,
                     fg=W  if k == key else G1)
        if key == "dashboard": self._refresh_dashboard()
        if key == "history":   self._refresh_history()
        if key == "goals":     self._refresh_goals()
        if key == "exams":     self._refresh_exams()

    # ══════════════════════════════════════════
    #  DASHBOARD
    # ══════════════════════════════════════════
    def _build_dashboard(self, p):
        # Stat cards row
        r1 = tk.Frame(p, bg=BG)
        r1.pack(fill="x", pady=(0, 14))

        self._stat_lbls  = {}
        self._stat_prev  = {}
        cards = [
            ("today",  "Today",       ACC, "0m"),
            ("week",   "This Week",   W,   "0m"),
            ("month",  "This Month",  W,   "0m"),
            ("year",   "This Year",   GRN, "0m"),
            ("avg",    "Daily Avg",   AMB, "0m"),
            ("streak", "Streak",      RED, "0 days"),
        ]
        for i, (key, title, color, default) in enumerate(cards):
            card = RCard(r1, radius=14, bg_color=CARD, border_color=BDR)
            card.pack(side="left", fill="both", expand=True,
                      padx=(0, 10) if i < 5 else 0)
            ci = card.inner()
            tk.Label(ci, text=title, font=FNT["sm"],
                     bg=CARD, fg=G1).pack(anchor="w", padx=16, pady=(14, 3))
            lbl = tk.Label(ci, text=default, font=FNT["h1"],
                           bg=CARD, fg=color)
            lbl.pack(anchor="w", padx=16, pady=(0, 14))
            self._stat_lbls[key] = lbl
            self._stat_prev[key] = 0

        # Bottom row
        r2 = tk.Frame(p, bg=BG)
        r2.pack(fill="both", expand=True)

        # Week chart
        wc = RCard(r2, radius=14, bg_color=CARD, border_color=BDR)
        wc.pack(side="left", fill="both", expand=True, padx=(0, 14))
        wi = wc.inner()
        tk.Label(wi, text="This Week", font=FNT["h3"],
                 bg=CARD, fg=W).pack(anchor="w", padx=18, pady=(16, 10))
        self._chart_frame = tk.Frame(wi, bg=CARD)
        self._chart_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # Subject bars
        sc = RCard(r2, radius=14, bg_color=CARD, border_color=BDR)
        sc.pack(side="left", fill="both", expand=True)
        si = sc.inner()
        tk.Label(si, text="Subjects · This Week", font=FNT["h3"],
                 bg=CARD, fg=W).pack(anchor="w", padx=18, pady=(16, 10))

        self._dash_subj_lbls = {}
        self._dash_subj_bars = {}
        for s in SUBJECTS:
            col = SUBJ_CLR[s]
            row = tk.Frame(si, bg=CARD)
            row.pack(fill="x", padx=14, pady=5)
            top = tk.Frame(row, bg=CARD)
            top.pack(fill="x")
            tk.Label(top, text=s, font=FNT["bodyb"],
                     bg=CARD, fg=W).pack(side="left")
            vl = tk.Label(top, text="--", font=FNT["bodyb"],
                          bg=CARD, fg=col)
            vl.pack(side="right")
            self._dash_subj_lbls[s] = vl
            bar = SmoothBar(row, color=col, height=9)
            bar.pack(fill="x", pady=(5, 0))
            self._dash_subj_bars[s] = bar
        tk.Frame(si, bg=CARD, height=10).pack()

    def _refresh_dashboard(self):
        td, wk, mo, yr, avg = get_stats(self.data)
        streak = get_streak(self.data)
        vals = {"today": td, "week": wk, "month": mo,
                "year": yr, "avg": avg, "streak": streak}
        self._streak_lbl.config(text=f"Streak: {streak} day{'s' if streak != 1 else ''}")

        for key, lbl in self._stat_lbls.items():
            v = vals[key]
            if key == "streak":
                lbl.config(text=f"{v}d")
            else:
                prev = self._stat_prev.get(key, 0)
                self._count_up(lbl, prev, v)
            self._stat_prev[key] = v

        self._draw_week_chart()

        for s in SUBJECTS:
            wt = get_subject_week(self.data, s)
            goal_min = self.goals.get(s, 2.0) * 60 * 7
            pct = wt / goal_min if goal_min > 0 else 0
            self._dash_subj_lbls[s].config(text=fmt(wt) if wt else "--")
            self._dash_subj_bars[s].set_value(pct)

    def _count_up(self, lbl, start, end, steps=24, step=0):
        if step > steps:
            lbl.config(text=fmt(end) if end else "0m")
            return
        v = int(start + (end - start) * step / steps)
        lbl.config(text=fmt(v) if v else "0m")
        try:
            self.after(16, lambda: self._count_up(lbl, start, end, steps, step+1))
        except Exception:
            pass

    def _draw_week_chart(self):
        for w in self._chart_frame.winfo_children():
            w.destroy()

        days    = get_week_days(self.data)
        totals  = [t for _, t in days]
        max_val = max(totals) if any(totals) else 60
        max_val = max(max_val, 30)
        today   = date.today()
        CHART_H = 160

        holder = tk.Frame(self._chart_frame, bg=CARD, height=CHART_H)
        holder.pack(fill="x")
        holder.pack_propagate(False)

        cols = tk.Frame(holder, bg=CARD)
        cols.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)

        for i, (d, total) in enumerate(days):
            is_today  = (d == today)
            bar_color = ACC if is_today else CARD3
            lbl_color = W   if is_today else G1

            cf = tk.Frame(cols, bg=CARD)
            cf.pack(side="left", fill="both", expand=True, padx=4)

            bar_h = int((total / max_val) * (CHART_H - 52)) if total else 2
            space = max((CHART_H - 52) - bar_h, 0)

            tk.Frame(cf, bg=CARD, height=space).pack()

            if total > 0:
                tk.Label(cf, text=fmt(total), font=FNT["xs"],
                         bg=CARD, fg=ACC if is_today else G2).pack()
            else:
                tk.Label(cf, text=" ", font=FNT["xs"],
                         bg=CARD, fg=CARD).pack()

            tk.Frame(cf, bg=bar_color, height=max(bar_h, 4)).pack(fill="x")

            tk.Label(cf, text=d.strftime("%a"),
                     font=FNT["smb"] if is_today else FNT["sm"],
                     bg=CARD, fg=lbl_color).pack(pady=(4, 0))

    # ══════════════════════════════════════════
    #  TIMER PAGE
    # ══════════════════════════════════════════
    def _build_timer(self, p):
        left  = tk.Frame(p, bg=BG)
        right = tk.Frame(p, bg=BG)
        left.pack(side="left",  fill="both", expand=True, padx=(0, 12))
        right.pack(side="left", fill="both", expand=True)

        # ── Study Timer card ──────────────────
        tc = RCard(left, radius=16, bg_color=CARD, border_color=BDR)
        tc.pack(fill="x", pady=(0, 12))
        ti = tc.inner()

        tk.Label(ti, text="Study Timer", font=FNT["h2"],
                 bg=CARD, fg=W).pack(anchor="w", padx=22, pady=(18, 10))

        # Subject pills
        tk.Label(ti, text="Select Subject:", font=FNT["bodyb"],
                 bg=CARD, fg=G1).pack(anchor="w", padx=22)
        pill_row = tk.Frame(ti, bg=CARD)
        pill_row.pack(fill="x", padx=20, pady=(6, 16))

        self._timer_subj_btns = {}
        for s in SUBJECTS:
            col = SUBJ_CLR[s]
            b = tk.Label(pill_row, text=s, font=FNT["smb"],
                         bg=CARD3, fg=G1,
                         padx=12, pady=6,
                         cursor="hand2")
            b.pack(side="left", padx=(0, 6), pady=2)
            b.bind("<Button-1>", lambda e, x=s: self._pick_timer_subj(x))
            self._timer_subj_btns[s] = b

        self._timer_subj_var = tk.StringVar(value=SUBJECTS[0])
        self._pick_timer_subj(SUBJECTS[0])

        # Timer display
        self._timer_lbl = tk.Label(ti, text="00:00",
                                    font=FNT["timer"],
                                    bg=CARD, fg=W)
        self._timer_lbl.pack(pady=(6, 16))

        # Buttons row
        btn_row = tk.Frame(ti, bg=CARD)
        btn_row.pack(pady=(0, 8))

        self._start_btn_lbl = pill_btn(btn_row, "  Start  ",
                                        command=self._toggle_timer,
                                        bg=GRN, fg=BG,
                                        font=FNT["h3"],
                                        padx=28, pady=13)
        self._start_btn_lbl.pack(side="left", padx=6)

        pill_btn(btn_row, "  Log & Reset  ",
                 command=self._log_timer,
                 bg=CARD3, fg=G1,
                 font=FNT["bodyb"],
                 padx=20, pady=13).pack(side="left", padx=6)

        tk.Frame(ti, bg=CARD, height=8).pack()

        # ── Manual entry card ─────────────────
        mc = RCard(left, radius=16, bg_color=CARD, border_color=BDR)
        mc.pack(fill="x")
        mi = mc.inner()

        tk.Label(mi, text="Manual Entry", font=FNT["h2"],
                 bg=CARD, fg=W).pack(anchor="w", padx=22, pady=(18, 10))

        dur_row = tk.Frame(mi, bg=CARD)
        dur_row.pack(padx=22, anchor="w", pady=(0, 12))

        self._man_h = tk.StringVar(value="0")
        self._man_m = tk.StringVar(value="30")
        for var, lbl_txt, lo, hi in [
            (self._man_h, "Hours", 0, 23),
            (self._man_m, "Minutes", 0, 59),
        ]:
            cf = tk.Frame(dur_row, bg=CARD)
            cf.pack(side="left", padx=(0, 24))
            tk.Label(cf, text=lbl_txt, font=FNT["sm"],
                     bg=CARD, fg=G1).pack(anchor="w")
            tk.Spinbox(cf, from_=lo, to=hi,
                       textvariable=var, width=4,
                       font=("Helvetica", 24, "bold"),
                       bg=CARD2, fg=W,
                       buttonbackground=BDR,
                       insertbackground=W,
                       relief="flat", bd=0,
                       highlightthickness=1,
                       highlightcolor=ACC,
                       highlightbackground=BDR).pack()

        self._man_preview = tk.Label(mi, text="0h 30m  ·  Maths",
                                      font=FNT["h2"], bg=CARD, fg=ACC)
        self._man_preview.pack(padx=22, pady=(0, 12))

        self._man_h.trace_add("write", lambda *_: self._update_preview())
        self._man_m.trace_add("write", lambda *_: self._update_preview())
        self._timer_subj_var.trace_add("write", lambda *_: self._update_preview())

        btn_row2 = tk.Frame(mi, bg=CARD)
        btn_row2.pack(padx=20, pady=(0, 18), anchor="w")
        pill_btn(btn_row2, "  Log Session  ",
                 command=self._log_manual,
                 bg=ACC, fg=BG,
                 font=FNT["h3"], padx=24, pady=12).pack(side="left", padx=(0, 10))
        pill_btn(btn_row2, "Undo Last",
                 command=self._undo,
                 bg=CARD3, fg=G1,
                 font=FNT["body"], padx=16, pady=12).pack(side="left")

        # ── Pomodoro card (right) ─────────────
        pc = RCard(right, radius=16, bg_color=CARD, border_color=BDR)
        pc.pack(fill="x", pady=(0, 12))
        poi = pc.inner()

        tk.Label(poi, text="Pomodoro Timer", font=FNT["h2"],
                 bg=CARD, fg=W).pack(anchor="w", padx=22, pady=(18, 8))

        # Ring
        ring_holder = tk.Frame(poi, bg=CARD)
        ring_holder.pack(pady=(0, 4))
        self._pomo_ring = Ring(ring_holder, size=160, thick=12,
                               track=G3, color=GRN)
        self._pomo_ring.pack()
        # Can't draw text on Ring canvas reliably — use a label below

        self._pomo_lbl = tk.Label(poi, text="25:00",
                                   font=FNT["pomo"], bg=CARD, fg=W)
        self._pomo_lbl.pack()

        self._pomo_mode_lbl = tk.Label(poi, text="Focus Session",
                                        font=FNT["body"], bg=CARD, fg=G1)
        self._pomo_mode_lbl.pack(pady=(2, 6))

        self._pomo_count_lbl = tk.Label(poi,
                                         text="Sessions completed: 0",
                                         font=FNT["smb"], bg=CARD, fg=AMB)
        self._pomo_count_lbl.pack(pady=(0, 10))

        pomo_btns = tk.Frame(poi, bg=CARD)
        pomo_btns.pack(pady=(0, 8))

        self._pomo_start_lbl = pill_btn(pomo_btns, "  Start  ",
                                         command=self._toggle_pomo,
                                         bg=GRN, fg=BG,
                                         font=FNT["h3"], padx=26, pady=12)
        self._pomo_start_lbl.pack(side="left", padx=6)
        pill_btn(pomo_btns, "Reset",
                 command=self._reset_pomo,
                 bg=CARD3, fg=G1,
                 font=FNT["bodyb"], padx=18, pady=12).pack(side="left", padx=6)

        # Duration selector
        dur_sel = tk.Frame(poi, bg=CARD)
        dur_sel.pack(pady=(0, 16))
        tk.Label(dur_sel, text="Focus duration:",
                 font=FNT["sm"], bg=CARD, fg=G1).pack(side="left", padx=(0, 8))
        self._pomo_dur_btns = {}
        for mins in [15, 25, 45]:
            b = tk.Label(dur_sel, text=f"{mins}m",
                         font=FNT["smb"],
                         bg=BDR if mins == 25 else CARD3,
                         fg=W if mins == 25 else G1,
                         padx=10, pady=5, cursor="hand2")
            b.pack(side="left", padx=3)
            b.bind("<Button-1>",
                   lambda e, m=mins: self._set_pomo_dur(m))
            self._pomo_dur_btns[mins] = b

        # ── Today summary (right bottom) ──────
        tc2 = RCard(right, radius=16, bg_color=CARD, border_color=BDR)
        tc2.pack(fill="both", expand=True)
        tci = tc2.inner()
        tk.Label(tci, text="Today", font=FNT["h2"],
                 bg=CARD, fg=W).pack(anchor="w", padx=22, pady=(18, 12))

        self._today_lbls = {}
        for s in SUBJECTS:
            col = SUBJ_CLR[s]
            row = tk.Frame(tci, bg=CARD)
            row.pack(fill="x", padx=16, pady=4)
            tk.Frame(row, bg=col, width=4).pack(side="left", fill="y")
            tk.Label(row, text=f"  {s}", font=FNT["body"],
                     bg=CARD, fg=G1).pack(side="left")
            lbl = tk.Label(row, text="--", font=FNT["bodyb"],
                           bg=CARD, fg=col)
            lbl.pack(side="right", padx=14, pady=8)
            self._today_lbls[s] = lbl

        tk.Frame(tci, bg=CARD, height=10).pack()
        self._refresh_today_lbls()

    # ── Timer logic ───────────────────────────
    def _pick_timer_subj(self, sub):
        self._timer_subj_var.set(sub)
        self._timer_subject = sub
        for s, b in self._timer_subj_btns.items():
            col = SUBJ_CLR[s]
            b.config(bg=col if s == sub else CARD3,
                     fg=BG  if s == sub else G1)
        self._update_preview()

    def _toggle_timer(self):
        if not self._timer_running:
            self._timer_running = True
            self._timer_start   = time.time() - self._timer_elapsed
            self._start_btn_lbl.config(text="  Stop  ", bg=RED)
            self._tick_timer()
        else:
            self._timer_running = False
            self._timer_elapsed = time.time() - self._timer_start
            self._start_btn_lbl.config(text="  Start  ", bg=GRN)

    def _tick_timer(self):
        if not self._timer_running:
            return
        self._timer_elapsed = time.time() - self._timer_start
        try:
            self._timer_lbl.config(text=fmt_hms(self._timer_elapsed))
            self.after(500, self._tick_timer)
        except Exception:
            pass

    def _log_timer(self):
        mins = int(self._timer_elapsed // 60)
        if mins < 1:
            toast(self, "Timer under 1 minute — keep studying!", AMB)
            return
        subj = self._timer_subject
        self.data.setdefault(today_str(), {})
        self.data[today_str()][subj] = \
            self.data[today_str()].get(subj, 0) + mins
        save_json(DATA_FILE, self.data)
        self._timer_elapsed = 0
        self._timer_running = False
        self._timer_start   = 0
        self._timer_lbl.config(text="00:00")
        self._start_btn_lbl.config(text="  Start  ", bg=GRN)
        self._refresh_today_lbls()
        toast(self, f"Logged {fmt(mins)} for {subj}", SUBJ_CLR.get(subj, GRN))

    def _update_preview(self):
        try:
            h = int(self._man_h.get())
            m = int(self._man_m.get())
        except Exception:
            return
        subj = getattr(self, "_timer_subject", SUBJECTS[0])
        col  = SUBJ_CLR.get(subj, ACC)
        self._man_preview.config(
            text=f"{fmt(h*60+m)}  ·  {subj}", fg=col)

    def _log_manual(self):
        subj = getattr(self, "_timer_subject", SUBJECTS[0])
        try:
            h = int(self._man_h.get())
            m = int(self._man_m.get())
        except Exception:
            messagebox.showerror("Error", "Invalid duration.")
            return
        total = h * 60 + m
        if total < 1:
            messagebox.showwarning("Oops", "Enter at least 1 minute.")
            return
        self.data.setdefault(today_str(), {})
        self.data[today_str()][subj] = \
            self.data[today_str()].get(subj, 0) + total
        save_json(DATA_FILE, self.data)
        self._refresh_today_lbls()
        toast(self, f"Logged {fmt(total)} for {subj}",
              SUBJ_CLR.get(subj, GRN))

    def _undo(self):
        if not self.data:
            messagebox.showinfo("Undo", "Nothing to undo.")
            return
        latest   = max(self.data)
        sessions = self.data.get(latest, {})
        if not sessions:
            messagebox.showinfo("Undo", "Nothing to undo.")
            return
        last_sub = max(sessions, key=lambda s: sessions[s])
        removed  = sessions.pop(last_sub)
        if not sessions:
            del self.data[latest]
        save_json(DATA_FILE, self.data)
        self._refresh_today_lbls()
        toast(self, f"Removed {fmt(removed)} from {last_sub}", RED)

    def _refresh_today_lbls(self):
        td_sessions = self.data.get(today_str(), {})
        for s in SUBJECTS:
            m = td_sessions.get(s, 0)
            self._today_lbls[s].config(text=fmt(m) if m else "--")
        self._streak_lbl.config(
            text=f"Streak: {get_streak(self.data)} days")

    # ── Pomodoro logic ────────────────────────
    def _set_pomo_dur(self, mins):
        self._pomo_duration = mins * 60
        self._reset_pomo()
        for m, b in self._pomo_dur_btns.items():
            b.config(bg=BDR if m == mins else CARD3,
                     fg=W   if m == mins else G1)

    def _toggle_pomo(self):
        if not self._pomo_running:
            self._pomo_running = True
            self._pomo_start   = time.time()
            self._pomo_start_lbl.config(text="  Stop  ", bg=RED)
            self._tick_pomo()
        else:
            self._pomo_running = False
            self._pomo_start_lbl.config(text="  Start  ", bg=GRN)

    def _reset_pomo(self):
        self._pomo_running  = False
        self._pomo_is_break = False
        self._pomo_start    = 0
        self._pomo_start_lbl.config(text="  Start  ", bg=GRN)
        dur_min = self._pomo_duration // 60
        try:
            self._pomo_lbl.config(text=f"{dur_min:02d}:00", fg=W)
            self._pomo_mode_lbl.config(text="Focus Session")
            self._pomo_ring.set_value(0, animate=False)
            self._pomo_ring.set_color(GRN)
        except Exception:
            pass

    def _tick_pomo(self):
        if not self._pomo_running:
            return
        elapsed = time.time() - self._pomo_start
        dur     = self._pomo_duration if not self._pomo_is_break else 5 * 60
        remain  = max(0, dur - elapsed)
        pct     = elapsed / dur
        color   = GRN if not self._pomo_is_break else ACC

        try:
            self._pomo_ring.set_value(min(pct, 1.0), animate=False)
            self._pomo_ring.set_color(color)
            m, s = divmod(int(remain), 60)
            self._pomo_lbl.config(text=f"{m:02d}:{s:02d}", fg=color)
        except Exception:
            return

        if remain <= 0:
            if not self._pomo_is_break:
                mins = self._pomo_duration // 60
                subj = getattr(self, "_timer_subject", SUBJECTS[0])
                self.data.setdefault(today_str(), {})
                self.data[today_str()][subj] = \
                    self.data[today_str()].get(subj, 0) + mins
                save_json(DATA_FILE, self.data)
                self._refresh_today_lbls()
                self._pomo_count += 1
                self._pomo_count_lbl.config(
                    text=f"Sessions completed: {self._pomo_count}")
                self._pomo_is_break = True
                self._pomo_start    = time.time()
                self._pomo_mode_lbl.config(text="Break — 5 minutes")
                self._pomo_ring.set_value(0, animate=False)
                toast(self,
                      f"Focus done! {fmt(mins)} logged. Take a break!",
                      GRN, ms=3500)
            else:
                self._pomo_is_break = False
                self._pomo_start    = time.time()
                self._pomo_mode_lbl.config(text="Focus Session")
                self._pomo_ring.set_value(0, animate=False)
                toast(self, "Break over — let's focus!", AMB, ms=3000)

        try:
            self.after(500, self._tick_pomo)
        except Exception:
            pass

    # ══════════════════════════════════════════
    #  HISTORY
    # ══════════════════════════════════════════
    def _build_history(self, p):
        tk.Label(p, text="Session History  ·  Last 60 Days",
                 font=FNT["h1"], bg=BG, fg=W).pack(anchor="w", pady=(0, 14))

        outer = RCard(p, radius=16, bg_color=CARD, border_color=BDR)
        outer.pack(fill="both", expand=True)
        oi = outer.inner()

        self._hist_canvas = tk.Canvas(oi, bg=CARD, highlightthickness=0)
        sb = tk.Scrollbar(oi, orient="vertical",
                          command=self._hist_canvas.yview)
        self._hist_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._hist_canvas.pack(side="left", fill="both", expand=True)

        self._hist_inner = tk.Frame(self._hist_canvas, bg=CARD)
        self._hist_win   = self._hist_canvas.create_window(
            (0, 0), window=self._hist_inner, anchor="nw")

        self._hist_inner.bind("<Configure>", lambda e:
            self._hist_canvas.configure(
                scrollregion=self._hist_canvas.bbox("all")))
        self._hist_canvas.bind("<Configure>", lambda e:
            self._hist_canvas.itemconfig(
                self._hist_win, width=e.width))
        self._hist_canvas.bind("<Button-4>",
            lambda e: self._hist_canvas.yview_scroll(-1, "units"))
        self._hist_canvas.bind("<Button-5>",
            lambda e: self._hist_canvas.yview_scroll(1,  "units"))

    def _refresh_history(self):
        for w in self._hist_inner.winfo_children():
            w.destroy()
        today  = date.today()
        cutoff = today - timedelta(days=60)
        dates  = sorted(
            [ds for ds in self.data
             if date.fromisoformat(ds) >= cutoff],
            reverse=True)

        if not dates:
            tk.Label(self._hist_inner,
                     text="No sessions in the last 60 days.",
                     font=FNT["body"], bg=CARD, fg=G2).pack(pady=40)
            return

        for ds in dates:
            sessions = self.data.get(ds, {})
            if not sessions:
                continue
            d        = date.fromisoformat(ds)
            is_today = (d == today)
            heading  = "Today" if is_today else d.strftime("%A, %d %B %Y")
            total    = sum(sessions.values())

            grp = tk.Frame(self._hist_inner, bg=CARD)
            grp.pack(fill="x", padx=16, pady=6)

            hdr = tk.Frame(grp, bg=CARD2)
            hdr.pack(fill="x")
            tk.Label(hdr, text=f"  {heading}",
                     font=FNT["bodyb"], bg=CARD2, fg=W,
                     pady=10).pack(side="left")
            tk.Label(hdr, text=f"{fmt(total)}  ",
                     font=FNT["bodyb"], bg=CARD2,
                     fg=ACC).pack(side="right")

            for subj, mins in sessions.items():
                col  = SUBJ_CLR.get(subj, G1)
                srow = tk.Frame(grp, bg=CARD)
                srow.pack(fill="x")
                tk.Frame(srow, bg=col, width=4).pack(side="left", fill="y")
                tk.Label(srow, text=f"   {subj}",
                         font=FNT["body"], bg=CARD, fg=G1,
                         pady=9).pack(side="left", fill="x", expand=True)
                tk.Label(srow, text=fmt(mins),
                         font=FNT["bodyb"], bg=CARD,
                         fg=col, padx=20).pack(side="right")

    # ══════════════════════════════════════════
    #  GOALS
    # ══════════════════════════════════════════
    def _build_goals(self, p):
        tk.Label(p, text="Daily Goals & Progress",
                 font=FNT["h1"], bg=BG, fg=W).pack(anchor="w", pady=(0, 14))

        # Goal setters
        setter = tk.Frame(p, bg=BG)
        setter.pack(fill="x", pady=(0, 14))
        self._goal_vars = {}
        for i, s in enumerate(SUBJECTS):
            col  = SUBJ_CLR[s]
            card = RCard(setter, radius=14, bg_color=CARD, border_color=BDR)
            card.pack(side="left", fill="both", expand=True,
                      padx=(0, 10) if i < 4 else 0)
            ci = card.inner()
            tk.Frame(ci, bg=col, height=3).pack(fill="x")
            tk.Label(ci, text=s, font=FNT["smb"],
                     bg=CARD, fg=W).pack(anchor="w", padx=14, pady=(10, 3))
            v = tk.DoubleVar(value=self.goals.get(s, 2.0))
            self._goal_vars[s] = v
            tk.Spinbox(ci, from_=0.5, to=12, increment=0.5,
                       textvariable=v, width=4,
                       font=("Helvetica", 18, "bold"),
                       bg=CARD2, fg=col,
                       buttonbackground=BDR,
                       relief="flat", bd=0,
                       insertbackground=col,
                       highlightthickness=1,
                       highlightcolor=col,
                       highlightbackground=BDR).pack(padx=14)
            tk.Label(ci, text="hrs / day", font=FNT["xs"],
                     bg=CARD, fg=G2).pack(anchor="w", padx=14, pady=(2, 12))

        pill_btn(p, "  Save Goals  ",
                 command=self._save_goals,
                 bg=ACC, fg=BG,
                 font=FNT["bodyb"], padx=22, pady=10).pack(anchor="e", pady=(0, 14))

        # Today's rings
        tk.Label(p, text="Today's Progress",
                 font=FNT["h3"], bg=BG, fg=W).pack(anchor="w", pady=(0, 10))

        rings_row = tk.Frame(p, bg=BG)
        rings_row.pack(fill="x", pady=(0, 14))

        self._goal_rings      = {}
        self._goal_ring_lbls  = {}
        self._goal_sub_lbls   = {}

        for i, s in enumerate(SUBJECTS):
            col  = SUBJ_CLR[s]
            card = RCard(rings_row, radius=14, bg_color=CARD, border_color=BDR)
            card.pack(side="left", fill="both", expand=True,
                      padx=(0, 10) if i < 4 else 0)
            ci = card.inner()

            ring = Ring(ci, size=100, thick=10, track=G3, color=col)
            ring.pack(pady=(16, 4))
            self._goal_rings[s] = ring

            tk.Label(ci, text=s, font=FNT["smb"],
                     bg=CARD, fg=W).pack()
            pct_lbl = tk.Label(ci, text="0%", font=FNT["bodyb"],
                               bg=CARD, fg=col)
            pct_lbl.pack(pady=(2, 0))
            self._goal_ring_lbls[s] = pct_lbl

            sub_lbl = tk.Label(ci, text="-- / --",
                               font=FNT["xs"], bg=CARD, fg=G1)
            sub_lbl.pack(pady=(0, 14))
            self._goal_sub_lbls[s] = sub_lbl

        # Weekly bars
        tk.Label(p, text="Weekly Progress",
                 font=FNT["h3"], bg=BG, fg=W).pack(anchor="w", pady=(0, 10))

        wk_card = RCard(p, radius=14, bg_color=CARD, border_color=BDR)
        wk_card.pack(fill="x")
        wi = wk_card.inner()

        self._wk_bars = {}
        self._wk_lbls = {}
        for s in SUBJECTS:
            col = SUBJ_CLR[s]
            row = tk.Frame(wi, bg=CARD)
            row.pack(fill="x", padx=18, pady=6)
            top = tk.Frame(row, bg=CARD)
            top.pack(fill="x")
            tk.Label(top, text=s, font=FNT["bodyb"],
                     bg=CARD, fg=W).pack(side="left")
            lbl = tk.Label(top, text="-- / --", font=FNT["bodyb"],
                           bg=CARD, fg=col)
            lbl.pack(side="right")
            self._wk_lbls[s] = lbl
            bar = SmoothBar(row, color=col, height=10)
            bar.pack(fill="x", pady=(5, 0))
            self._wk_bars[s] = bar

        tk.Frame(wi, bg=CARD, height=12).pack()

    def _save_goals(self):
        self.goals = {s: float(self._goal_vars[s].get()) for s in SUBJECTS}
        save_json(GOALS_FILE, self.goals)
        self._refresh_goals()
        toast(self, "Goals saved!", GRN)

    def _refresh_goals(self):
        td_sessions = self.data.get(today_str(), {})
        for s in SUBJECTS:
            col      = SUBJ_CLR[s]
            goal_day = self.goals.get(s, 2.0) * 60
            today_m  = td_sessions.get(s, 0)
            pct_day  = min(1.0, today_m / goal_day) if goal_day else 0
            done     = pct_day >= 1.0

            self._goal_rings[s].set_value(pct_day)
            self._goal_rings[s].set_color(GRN if done else col)
            self._goal_ring_lbls[s].config(
                text=f"{int(pct_day*100)}%",
                fg=GRN if done else col)
            self._goal_sub_lbls[s].config(
                text=f"{fmt(today_m)} / {fmt(int(goal_day))}")

            wk_m      = get_subject_week(self.data, s)
            goal_week = goal_day * 7
            pct_week  = min(1.0, wk_m / goal_week) if goal_week else 0
            self._wk_lbls[s].config(
                text=f"{fmt(wk_m)} / {fmt(int(goal_week))}",
                fg=GRN if pct_week >= 1.0 else col)
            self._wk_bars[s].set_value(pct_week)

    # ══════════════════════════════════════════
    #  EXAMS
    # ══════════════════════════════════════════
    def _build_exams(self, p):
        hdr = tk.Frame(p, bg=BG)
        hdr.pack(fill="x", pady=(0, 14))
        tk.Label(hdr, text="Exam Countdown",
                 font=FNT["h1"], bg=BG, fg=W).pack(side="left")
        pill_btn(hdr, "  + Add Exam  ",
                 command=self._add_exam,
                 bg=GRN, fg=BG,
                 font=FNT["bodyb"], padx=20, pady=10).pack(side="right")

        self._exam_scroll_canvas = tk.Canvas(p, bg=BG,
                                              highlightthickness=0)
        exam_sb = tk.Scrollbar(p, orient="vertical",
                                command=self._exam_scroll_canvas.yview)
        self._exam_scroll_canvas.configure(yscrollcommand=exam_sb.set)
        exam_sb.pack(side="right", fill="y")
        self._exam_scroll_canvas.pack(side="left", fill="both", expand=True)

        self._exam_frame = tk.Frame(self._exam_scroll_canvas, bg=BG)
        self._exam_win = self._exam_scroll_canvas.create_window(
            (0, 0), window=self._exam_frame, anchor="nw")
        self._exam_frame.bind("<Configure>", lambda e:
            self._exam_scroll_canvas.configure(
                scrollregion=self._exam_scroll_canvas.bbox("all")))
        self._exam_scroll_canvas.bind("<Configure>", lambda e:
            self._exam_scroll_canvas.itemconfig(
                self._exam_win, width=e.width))
        self._exam_scroll_canvas.bind("<Button-4>",
            lambda e: self._exam_scroll_canvas.yview_scroll(-1, "units"))
        self._exam_scroll_canvas.bind("<Button-5>",
            lambda e: self._exam_scroll_canvas.yview_scroll(1, "units"))

    def _add_exam(self):
        name = simpledialog.askstring("Add Exam", "Exam name:", parent=self)
        if not name:
            return
        date_str = simpledialog.askstring(
            "Add Exam", "Exam date (YYYY-MM-DD):", parent=self)
        if not date_str:
            return
        try:
            date.fromisoformat(date_str)
        except ValueError:
            messagebox.showerror("Error", "Use format YYYY-MM-DD  e.g. 2025-03-15")
            return
        self.exams.append({"name": name, "date": date_str})
        save_json(EXAM_FILE, self.exams)
        self._refresh_exams()

    def _refresh_exams(self):
        for w in self._exam_frame.winfo_children():
            w.destroy()

        today = date.today()
        upcoming = []
        for ex in self.exams:
            try:
                d = date.fromisoformat(ex["date"])
                upcoming.append(((d - today).days, ex["name"], ex["date"]))
            except Exception:
                continue
        upcoming.sort()

        if not upcoming:
            card = RCard(self._exam_frame, radius=16,
                         bg_color=CARD, border_color=BDR)
            card.pack(fill="x", pady=4)
            ci = card.inner()
            tk.Label(ci, text="No exams added yet.",
                     font=FNT["body"], bg=CARD, fg=G2).pack(pady=30)
            tk.Label(ci,
                     text='Click "+ Add Exam" above to add your board exam dates.',
                     font=FNT["sm"], bg=CARD, fg=G2).pack(pady=(0, 30))
            return

        # Grid layout: 3 per row
        row_frame = None
        for idx, (days_left, name, date_str) in enumerate(upcoming):
            if idx % 3 == 0:
                row_frame = tk.Frame(self._exam_frame, bg=BG)
                row_frame.pack(fill="x", pady=(0, 12))

            if days_left < 0:
                color = G2;  badge = "Past"
            elif days_left == 0:
                color = RED; badge = "TODAY"
            elif days_left <= 7:
                color = RED; badge = f"{days_left} days"
            elif days_left <= 30:
                color = AMB; badge = f"{days_left} days"
            else:
                color = GRN; badge = f"{days_left} days"

            card = RCard(row_frame, radius=16, bg_color=CARD, border_color=BDR)
            card.pack(side="left", fill="both", expand=True,
                      padx=(0, 12) if (idx % 3) < 2 else 0)
            ci = card.inner()

            tk.Frame(ci, bg=color, height=4).pack(fill="x")
            tk.Label(ci, text=name, font=FNT["h2"],
                     bg=CARD, fg=W).pack(anchor="w", padx=20, pady=(14, 4))
            tk.Label(ci, text=date_str, font=FNT["body"],
                     bg=CARD, fg=G1).pack(anchor="w", padx=20)

            # Ring
            try:
                d = date.fromisoformat(date_str)
                year_days = 365
                pct = 1.0 - max(0, days_left) / year_days
                ring = Ring(ci, size=120, thick=12,
                            track=G3, color=color)
                ring.pack(pady=14)
                ring.set_value(min(pct, 1.0))
            except Exception:
                pass

            tk.Label(ci, text=badge, font=FNT["h1"],
                     bg=CARD, fg=color).pack()
            tk.Label(ci,
                     text="days left" if days_left >= 0 else "days ago",
                     font=FNT["body"], bg=CARD, fg=G1).pack(pady=(0, 6))

            def make_del(n=name, ds=date_str):
                return lambda: self._del_exam(n, ds)

            pill_btn(ci, "Remove",
                     command=make_del(),
                     bg=CARD3, fg=RED,
                     font=FNT["sm"], padx=14, pady=6).pack(pady=(6, 16))

    def _del_exam(self, name, date_str):
        self.exams = [e for e in self.exams
                      if not (e["name"] == name and e["date"] == date_str)]
        save_json(EXAM_FILE, self.exams)
        self._refresh_exams()
        toast(self, f"Removed exam: {name}", RED)

    # ══════════════════════════════════════════
    #  CLOCK
    # ══════════════════════════════════════════
    def _tick_clock(self):
        try:
            self._clock_var.set(datetime.now().strftime("%a %d %b  %H:%M"))
            self.after(30000, self._tick_clock)
        except Exception:
            pass


# ══════════════════════════════════════════════
if __name__ == "__main__":
    app = StudyTrace()
    app.mainloop()