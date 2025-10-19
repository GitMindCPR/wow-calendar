import tkinter as tk
from tkinter import messagebox, Text, Frame, Label, Button, StringVar, Toplevel, Entry, colorchooser
import calendar
import datetime
import json
import os
import sys
import webbrowser
import traceback  # [핵심 수정] 빠뜨렸던 traceback 모듈을 추가했습니다.

# --- [핵심 수정 1] 파일 경로 문제 해결 ---
# .exe로 실행되든 .py로 실행되든, 파일의 실제 위치를 기준으로 경로를 설정합니다.
if getattr(sys, 'frozen', False):
    # .exe 파일로 실행될 경우
    application_path = os.path.dirname(sys.executable)
else:
    # .py 파일로 직접 실행될 경우
    application_path = os.path.dirname(os.path.abspath(__file__))

# 모든 파일 경로를 이 application_path를 기준으로 설정합니다.
LOCAL_CACHE_FILE = os.path.join(application_path, "wowstarism_local_cache.json")
AUTH_TOKEN_FILE = os.path.join(application_path, "wowstarism_auth.json")
COLOR_SETTINGS_FILE = os.path.join(application_path, "wowstarism_color_settings.json")

# --- 설정 및 전역 변수 ---
PASSWORD_RESET_URL = "https://app.wowstarism.com/reset-password"
memos = {}
day_cells = {}
USER_TOKEN = None
color_settings = {
    "today_border": "#6a0dad", "memo_bg": "#fff5e6", "default_bg": "#ffffff",
    "weekday_header_bg": "#f0f0f0", "other_month_fg": "grey", "other_month_bg": "lightgrey"
}
# --- 전역 변수 추가 ---
current_year = 0
current_month = 0
frame_calendar_grid = None
title_var = None

# --- 모든 함수 정의 ---

def load_color_settings():
    global color_settings
    if os.path.exists(COLOR_SETTINGS_FILE):
        try:
            with open(COLOR_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                color_settings.update(json.load(f))
        except: pass

def save_color_settings():
    try:
        with open(COLOR_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(color_settings, f, ensure_ascii=False, indent=4)
    except: pass

def open_color_settings_window(root):
    settings_window = Toplevel(root)
    settings_window.title("색상 설정")
    settings_window.geometry("350x300")
    settings_window.resizable(False, False)
    settings_window.transient(root)
    
    root.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - 175
    y = root.winfo_y() + (root.winfo_height() // 2) - 150
    settings_window.geometry(f'+{int(x)}+{int(y)}')
    
    settings_frame = Frame(settings_window, padx=10, pady=10)
    settings_frame.pack(fill="both", expand=True)

    def change_color(key, label_to_update):
        color_code = colorchooser.askcolor(title="색상 선택", initialcolor=color_settings[key])
        if color_code[1]:
            color_settings[key] = color_code[1]
            label_to_update.config(bg=color_settings[key])
            save_color_settings()
            draw_calendar()

    options = {
        "today_border": "오늘 날짜 테두리",
        "memo_bg": "메모 있는 날 배경",
        "default_bg": "기본 날짜 배경",
        "weekday_header_bg": "요일 헤더 배경"
    }
    
    for i, (key, text) in enumerate(options.items()):
        Label(settings_frame, text=f"{text}:").grid(row=i, column=0, sticky="w", pady=5)
        color_label = Label(settings_frame, text="    ", bg=color_settings[key], relief="solid", borderwidth=1)
        color_label.grid(row=i, column=1, padx=10)
        btn = Button(settings_frame, text="색상 변경", command=lambda k=key, l=color_label: change_color(k, l))
        btn.grid(row=i, column=2)

    Button(settings_window, text="닫기", command=settings_window.destroy).pack(pady=10)
    settings_window.grab_set()

def save_auth_token(token):
    global USER_TOKEN
    USER_TOKEN = token
    with open(AUTH_TOKEN_FILE, 'w', encoding='utf-8') as f:
        json.dump({'token': token}, f)

def open_password_reset_link(event=None):
    webbrowser.open(PASSWORD_RESET_URL)

def show_login_fail_dialog(parent_window):
    fail_window = Toplevel(parent_window)
    fail_window.title("로그인 실패")
    parent_window.update_idletasks()
    x = parent_window.winfo_x() + (parent_window.winfo_width()//2) - 175
    y = parent_window.winfo_y() + (parent_window.winfo_height()//2) - 75
    fail_window.geometry(f"350x150+{int(x)}+{int(y)}")
    fail_window.resizable(False, False)
    fail_window.transient(parent_window)
    Label(fail_window, text="ID 또는 비밀번호가 일치하지 않습니다.", font=('sans-serif', 11, 'bold'), fg='red').pack(pady=(15, 5))
    reset_label = Label(fail_window, text="비밀번호 재설정 페이지로 이동", fg="blue", cursor="hand2", font=('sans-serif', 10, 'underline'))
    reset_label.pack(pady=5)
    reset_label.bind("<Button-1>", open_password_reset_link)
    Button(fail_window, text="확인", command=fail_window.destroy).pack(pady=10)
    fail_window.grab_set()
    parent_window.wait_window(fail_window)

def attempt_login(username, password):
    if username == "wow" and password == "star":
        save_auth_token("DUMMY_TOKEN_12345")
        return True
    return False

def show_login_dialog(root):
    login_success = False
    
    login_window = Toplevel(root)
    login_window.title("WOWSTARISM 구독자 로그인")
    screen_width = login_window.winfo_screenwidth()
    screen_height = login_window.winfo_screenheight()
    x = (screen_width / 2) - 150
    y = (screen_height / 2) - 125
    login_window.geometry(f'300x250+{int(x)}+{int(y)}')
    login_window.resizable(False, False)
    
    Label(login_window, text="아이디:", font=('sans-serif', 10, 'bold')).pack(pady=(20, 0))
    user_entry = Entry(login_window, width=30)
    user_entry.pack(pady=5, padx=20)
    user_entry.focus()
    Label(login_window, text="비밀번호:", font=('sans-serif', 10, 'bold')).pack(pady=(5, 0))
    pass_entry = Entry(login_window, show="*", width=30)
    pass_entry.pack(pady=5, padx=20)
    
    def on_login_click():
        nonlocal login_success
        if attempt_login(user_entry.get(), pass_entry.get()):
            login_success = True
            login_window.destroy()
        else:
            show_login_fail_dialog(login_window)

    Button(login_window, text="로그인", command=on_login_click).pack(pady=15)
    
    def on_close():
        nonlocal login_success
        login_success = False
        login_window.destroy()

    login_window.protocol("WM_DELETE_WINDOW", on_close)
    login_window.transient(root)
    login_window.grab_set()
    root.wait_window(login_window)
    
    return login_success

def load_memos():
    global memos
    if os.path.exists(LOCAL_CACHE_FILE):
        try:
            with open(LOCAL_CACHE_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                memos = json.loads(content) if content else {}
        except: memos = {}
    else: memos = {}

def save_all_memos():
    global memos
    for date_str, cell_widgets in day_cells.items():
        memo_content = cell_widgets['memo_text'].get("1.0", tk.END).strip()
        if memo_content:
            memos[date_str] = memo_content
        elif date_str in memos:
            del memos[date_str]
    try:
        with open(LOCAL_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(memos, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("저장 완료", "모든 변경사항이 로컬에 저장되었습니다.")
    except Exception as e:
        messagebox.showerror("저장 실패", f"파일 오류: {e}")
    draw_calendar()

def draw_calendar():
    global day_cells, frame_calendar_grid
    for widget in frame_calendar_grid.winfo_children():
        widget.destroy()
    day_cells = {}

    title_var.set(f"{current_year}년 {current_month}월")

    cal = calendar.Calendar(calendar.SUNDAY)
    days = ["일", "월", "화", "수", "목", "금", "토"]
    for i, day in enumerate(days):
        lbl = Label(frame_calendar_grid, text=day, font=('sans-serif', 12, 'bold'), bg=color_settings['weekday_header_bg'])
        lbl.grid(row=0, column=i, sticky="nsew")
        
    today_str = datetime.date.today().strftime('%Y-%m-%d')

    month_dates = cal.monthdatescalendar(current_year, current_month)
    for r, week in enumerate(month_dates, 1):
        for c, date in enumerate(week):
            date_str = date.strftime('%Y-%m-%d')
            is_today = (date_str == today_str)
            border_thickness = 2 if is_today else 1
            border_color = color_settings['today_border'] if is_today else "lightgrey"

            cell_frame = Frame(frame_calendar_grid, highlightbackground=border_color, highlightthickness=border_thickness)
            cell_frame.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
            
            cell_bg = color_settings['memo_bg'] if date_str in memos else color_settings['default_bg']
            
            day_label = Label(cell_frame, text=str(date.day), font=('sans-serif', 10, 'bold'), bg=cell_bg)
            day_label.pack(anchor="nw", padx=3, pady=2)
            
            memo_text = Text(cell_frame, font=('sans-serif', 10), wrap="word", height=5, width=15, bg=cell_bg, borderwidth=0, highlightthickness=0)
            memo_text.pack(fill="both", expand=True, padx=5, pady=(0,5))
            memo_text.insert(tk.END, memos.get(date_str, ""))
            
            day_cells[date_str] = {'frame': cell_frame, 'memo_text': memo_text}
            
            if date.month != current_month:
                cell_frame.config(bg=color_settings['other_month_bg'])
                memo_text.config(state="disabled", bg=color_settings['other_month_bg'])
                day_label.config(fg=color_settings['other_month_fg'], bg=color_settings['other_month_bg'])
    
    # 빈 줄의 높이를 동적으로 조절
    for i in range(7):
        frame_calendar_grid.grid_rowconfigure(i, weight=1 if i <= len(month_dates) else 0)


def change_month(delta):
    global current_year, current_month
    current_month += delta
    if current_month > 12:
        current_month = 1
        current_year += 1
    elif current_month < 1:
        current_month = 12
        current_year -= 1
    draw_calendar()

def change_year(delta):
    global current_year
    current_year += delta
    draw_calendar()

def return_to_today():
    global current_year, current_month
    today = datetime.date.today()
    current_year, current_month = today.year, today.month
    draw_calendar()

def update_datetime(root, date_var, time_var):
    now = datetime.datetime.now()
    date_var.set(now.strftime('%Y년 %m월 %d일'))
    time_var.set(now.strftime('%H시 %M분 %S초'))
    root.after(1000, lambda: update_datetime(root, date_var, time_var))

def main():
    root = tk.Tk()
    root.title("WOWSTARISM CALENDAR - 구독자 전용")
    root.withdraw()

    global current_year, current_month, frame_calendar_grid, title_var
    
    app_width, app_height = 1200, 800
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width / 2) - (app_width / 2)
    y = (screen_height / 2) - (app_height / 2)
    root.geometry(f'{app_width}x{app_height}+{int(x)}+{int(y)}')
    root.minsize(app_width, app_height)
    
    frame_top = Frame(root)
    frame_top.pack(fill="x", pady=(10, 0))
    Label(frame_top, text="✨ WOWSTARISM CALENDAR ✨", font=('Arial', 24, 'bold'), fg='#6a0dad').pack()
    
    frame_datetime = Frame(frame_top)
    frame_datetime.pack(pady=2)
    date_var, time_var = StringVar(), StringVar()
    Label(frame_datetime, textvariable=date_var, font=('sans-serif', 12)).pack(side="left", padx=10)
    Label(frame_datetime, textvariable=time_var, font=('sans-serif', 12)).pack(side="left", padx=10)
    
    title_var = StringVar()
    Label(frame_top, textvariable=title_var, font=('sans-serif', 18, 'bold')).pack(pady=5)

    frame_nav = Frame(frame_top)
    frame_nav.pack(pady=2, fill="x")
    
    left_nav = Frame(frame_nav)
    left_nav.pack(side="left", expand=True, fill="x", anchor='w')
    center_nav = Frame(frame_nav)
    center_nav.pack(side="left")
    right_nav = Frame(frame_nav)
    right_nav.pack(side="right", expand=True, fill="x", anchor='e')
    
    Button(left_nav, text="◀◀ 이전 해", command=lambda: change_year(-1)).pack(side="left", padx=5)
    Button(left_nav, text="◀ 이전 달", command=lambda: change_month(-1)).pack(side="left", padx=5)
    
    Button(center_nav, text="오늘 (HOME)", font=('sans-serif', 10, 'bold'), command=return_to_today).pack(side="left", padx=20)
    
    Button(right_nav, text="다음 해 ▶▶", command=lambda: change_year(1)).pack(side="right", padx=5)
    Button(right_nav, text="다음 달 ▶", command=lambda: change_month(1)).pack(side="right", padx=5)
    Button(right_nav, text="🎨 색상 설정", command=lambda: open_color_settings_window(root)).pack(side="right", padx=20)
    Button(right_nav, text="💾 로컬 저장", font=('sans-serif', 12, 'bold'), bg='#6a0dad', fg='white', command=save_all_memos).pack(side="right", padx=20)
    
    frame_calendar_grid = Frame(root, bg='lightgrey')
    frame_calendar_grid.pack(fill="both", expand=True, padx=10, pady=10)
    for i in range(7):
        frame_calendar_grid.grid_columnconfigure(i, weight=1)
    # Row weights are now set dynamically in draw_calendar

    load_color_settings()
    today = datetime.date.today()
    current_year, current_month = today.year, today.month

    login_needed = True
    if os.path.exists(AUTH_TOKEN_FILE):
        try:
            with open(AUTH_TOKEN_FILE, 'r') as f:
                token = json.load(f).get('token')
                if token:
                    global USER_TOKEN
                    USER_TOKEN = token
                    login_needed = False
        except: login_needed = True

    should_run_app = False
    if login_needed:
        if show_login_dialog(root):
            should_run_app = True
    else:
        should_run_app = True

    if should_run_app:
        load_memos()
        draw_calendar()
        update_datetime(root, date_var, time_var)
        root.deiconify()
        root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # 만약의 최종 오류를 파일에 기록합니다.
        with open(os.path.join(application_path, "critical_error.txt"), "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now()}] CRITICAL ERROR:\n")
            f.write(traceback.format_exc())

