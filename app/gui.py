###
# VEP MIDI AutoMate 1.0.0 gui.py
# https://github.com/robertrussell22/VEP-MIDI-AutoMate
###

import json, os, threading, keyboard, queue, webbrowser, csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from functools import partial

import core

APP_NAME = 'VEP MIDI AutoMate'
VERSION = '1.0.0'
REQUIRED_HEADERS = ['device', 'channel', 'cc', 'layer 1', 'layer 2', 'layer 3', 'layer 4', 'repeat']
ABORT_HOTKEY = 'ctrl+f12'
ABORT_HOTKEY_STRING = 'Ctrl + F12'

if os.name == 'nt':
    _base = Path(os.getenv('APPDATA', Path.home()))
else:
    _base = Path(os.getenv('XDG_CONFIG_HOME', Path.home() / '.config'))
CONFIG_DIR = _base / APP_NAME
CONFIG_FILE = CONFIG_DIR / 'settings.json'

PALETTES = {
    'light': {
        'background': '#FFFFFF',
        'foreground': '#111111',
        'muted': '#666666',
        'entry_background': '#FFFFFF',
        'entry_foreground': '#111111',
        'button_background': '#F2F2F2',
        'button_foreground': '#111111',
        'accent': '#3A7AFE',
        'log_background': '#F8F8F8',
        'log_foreground': '#111111',
        'link': '#0B6CFB',
        'warning': '#B00020',
        'okay': '#0C7A0C'
    },
    'dark' : {
        'background': '#1E1E1E',
        'foreground': '#EAEAEA',
        'muted': '#A0A0A0',
        'entry_background': '#2A2A2A',
        'entry_foreground': '#EAEAEA',
        'button_background': '#2E2E2E',
        'button_foreground': '#EAEAEA',
        'accent': '#6CA0FF',
        'log_background': '#0C0C0C',
        'log_foreground': '#DCDCDC',
        'link': '#79A7FF',
        'warning': '#FF6B6B',
        'okay': '#63D17A'
    }
}

def load_settings():
    try:
        json_data = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
        return {'csv_path': json_data.get('csv_path', ''), 'slow_mode': bool(json_data.get('slow_mode', False)), 'theme': json_data.get('theme', 'light')}
    except Exception:
        return {'csv_path': '', 'slow_mode': False, 'theme': detect_system_theme()}

def save_settings(csv_path, slow_mode, theme):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        settings = {'csv_path': str(csv_path or ''), 'slow_mode': bool(slow_mode), 'theme': str(theme)}
        CONFIG_FILE.write_text(json.dumps(settings, indent=2), encoding='utf-8')
    except Exception:
        pass

def UI(function, *args, **kw):
    root.after(0, partial(function, *args, **kw))

def detect_system_theme():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize') as k:
            value, _ = winreg.QueryValueEx(k, 'AppsUseLightTheme')
            return 'light' if value == 1 else 'dark'
    except Exception:
        return 'light'

def apply_theme(theme_string):
    palette = PALETTES[theme_string]

    root.configure(bg=palette['background'])

    container.configure(bg=palette['background'])

    canvas.configure(bg=palette['background'])

    scroll_frame.configure(bg=palette['background'])

    wrapper.configure(bg=palette['background'])

    instructions.configure(bg=palette['background'], fg=palette['foreground'])

    github_link.configure(bg=palette['background'], fg=palette['link'])

    csv_row.configure(bg=palette['background'])
    csv_path_label.configure(bg=palette['background'], fg=palette['foreground'])
    entry_box.configure(bg=palette['entry_background'], fg=palette['entry_foreground'], insertbackground=palette['foreground'], selectbackground=palette['accent'], selectforeground='#ffffff', highlightbackground=palette['background'], highlightcolor=palette['accent'])
    button_browse.configure(bg=palette['button_background'], fg=palette['button_foreground'], activebackground=palette['button_background'])
    button_start.configure(bg=palette['accent'], fg=palette['button_background'], activebackground=palette['accent'])

    csv_status.configure(bg=palette['background'])

    modes_row.configure(bg=palette['background'])
    for button in [slow_mode_button, radio_button_light_mode, radio_button_dark_mode]:
        button.configure(bg=palette['background'], fg=palette['foreground'], selectcolor=palette['background'])

    logging_frame.configure(bg=palette['background'])
    logging_box.configure(bg=palette['log_background'], fg=palette['log_foreground'], insertbackground=palette['log_foreground'], selectbackground=palette['accent'], selectforeground='#ffffff')
    scrollbar_horizontal.configure(bg=palette['background'])
    scrollbar_vertical.configure(bg=palette['background'])

    _hover_off(None)

def pick_csv():
    path = filedialog.askopenfilename(title='Choose your CSV', filetypes=[('CSV files', '*.csv'), ('All files', '*.*')])
    if path:
        csv_path_string.set(path)

def find_csv_problems():
    path = csv_path_string.get().strip()
    problems = []
    try:
        f = Path(path).open('r', encoding='utf-8-sig', newline='')    
    except Exception as e:
        problems.append(f'Could not read CSV: {e}')
        return problems
    
    valid_integers_string = {
        'device': '{1, 2, 3, …}',
        'channel': '{1, 2, 3, …, 16}',
        'cc': '{0, 1, 2, …, 127}'
    }

    with f:
        reader = csv.DictReader(f, skipinitialspace=True)
        if reader.fieldnames is None:
            problems.append(f'No header row found. The first row must contain {", ".join(REQUIRED_HEADERS)}.')
            return problems
        missing_headers = [header for header in REQUIRED_HEADERS if header not in reader.fieldnames]
        if missing_headers:
            problems.append(f'Missing some headings: {", ".join(missing_headers)}.')
        for row_number, row in enumerate(reader, start=2):
            row = {key : (value.strip() if isinstance(value, str) else value) for key, value in row.items()}
            for header in ['device', 'channel', 'cc', 'layer 1', 'layer 2']:
                if not row.get(header, ''):
                    problems.append(f'Missing an entry in row {row_number}: \'{header}\'.')
            if row.get('layer 3') and not row.get('layer 2'):
                problems.append(f'Row {row_number} (device={row.get("device")},channel={row.get("channel")},cc={row.get("cc")}): Cannot have \'layer 3\' without \'layer 2\'.')
            if row.get('layer 4') and not row.get('layer 3'):
                problems.append(f'Row {row_number} (device={row.get("device")},channel={row.get("channel")},cc={row.get("cc")}): Cannot have \'layer 4\' without \'layer 3\'.')
            if row.get('repeat') and not (row.get('layer 3') or row.get('layer 4')):
                problems.append(f'Row {row_number} (device={row.get("device")},channel={row.get("channel")},cc={row.get("cc")}): Must have \'layer 3\' or \'layer 4\' to have \'repeat\'.')
            for header in ['device', 'channel', 'cc']:
                value_string = (row.get(header, '') or '').strip()
                if not value_string.isdecimal():
                    problems.append(f'Row {row_number} (device={row.get("device")},channel={row.get("channel")},cc={row.get("cc")}): Must have an integer for \'{header}\'.')
                    continue
                value = int(value_string)
                if header == 'device' and value < 1 or header == 'channel' and value not in range(1, 17) or header == 'cc' and value not in range(0, 128):
                    problems.append(f'Row {row_number} (device={row.get("device")},channel={row.get("channel")},cc={row.get("cc")}): Must have an integer from {valid_integers_string[header]} for \'{header}\'.')
            value_string = (row.get('repeat', '') or '').strip()
            if value_string:
                if not value_string.isdecimal() or int(value_string) < 1:
                    problems.append(f'Row {row_number} (device={row.get("device")},channel={row.get("channel")},cc={row.get("cc")}): Must be blank or have an integer (1, 2, 3, …) for \'repeat\'.')

    return problems

def update_csv_status():
    path = csv_path_string.get().strip()
    palette = PALETTES[theme.get()]
    if not path:
        csv_status.config(text='(waiting for CSV)', fg=palette['muted'], cursor='')
        csv_status.unbind('<Button-1>')
        return
    if not Path(path).exists():
        csv_status.config(text='CSV not found', fg=palette['warning'], cursor='')
        csv_status.unbind('<Button-1>')
        return
    
    problems = find_csv_problems()
    if problems:
        csv_status.config(text=f'CSV has problems ({len(problems)}). Click for details…', fg=palette['warning'], cursor='hand2')
        def show_problems(e = None):
            messagebox.showerror(APP_NAME, 'CSV problems. Reported row number includes heading row.\n\n' + '\n'.join(problems))
        csv_status.unbind('<Button-1>')
        csv_status.bind('<Button-1>', show_problems)
    else:
        csv_status.config(text='CSV looks good ✓', fg=palette['okay'], cursor='')
        csv_status.unbind('<Button-1>')

updates = queue.Queue()

def append_log(message):
    logging_box.configure(state='normal')
    logging_box.insert('end', message + '\n')
    logging_box.see('end')
    logging_box.configure(state='disabled')

def pump_updates():
    try:
        while True:
            update = updates.get_nowait()
            append_log(update)
    except queue.Empty:
        pass
    root.after(80, pump_updates)

def run_worker(path, abort_event, slow_mode, update_callback, headers, hotkey_handle, BULLET):
    try:
        UI(append_log, f'Starting{" in slow mode" if slow_mode else ""}. Press \'{ABORT_HOTKEY_STRING}\' to abort at any time.')
        root.update()
        root.update_idletasks()
        core.go(path, abort_event, slow_mode, update_callback, headers, BULLET)
    except core.VEP_MIDI_AutoMate_Abort as e:
        UI(append_log, str(e))
    except Exception as e:
        UI(append_log, f'Error: {e}')
        UI(messagebox.showerror, APP_NAME, str(e))
    finally:
        if hotkey_handle is not None:
            try:
                keyboard.remove_hotkey(hotkey_handle)
            except Exception:
                pass
        UI(button_start.config, state='normal')
        UI(button_browse.config, state='normal')

def start():
    hotkey_handle = None
    abort_event.clear()
    path = Path(csv_path_string.get().strip())
    if not path.exists():
        messagebox.showerror(APP_NAME, 'Please choose a valid CSV file.')
        return
    
    problems = find_csv_problems()
    if problems:
        messagebox.showerror(APP_NAME, 'Please fix the CSV before continuing.\n\n' + '\n'.join(problems))
        return

    def abort():
        if not abort_event.is_set():
            abort_event.set()
    try:
        hotkey_handle = keyboard.add_hotkey(ABORT_HOTKEY, abort)
    except Exception:
        UI(append_log, 'Manually aborting failed. Close the window to stop.')
        hotkey_handle = None

    if not path.exists():
        messagebox.showerror(APP_NAME, 'Please choose a valid CSV file.')
        return
    save_settings(path, slow_mode.get(), theme.get())
    button_start.config(state='disabled')
    button_browse.config(state='disabled')

    def update_callback(update: str):
        updates.put(update)

    threading.Thread(target=run_worker, args=(path, abort_event, slow_mode.get(), update_callback, REQUIRED_HEADERS, hotkey_handle, BULLET), daemon=True).start()

def on_close():
    abort_event.set()
    path = Path(csv_path_string.get().strip())
    try:
        save_settings(path, slow_mode.get(), theme.get())
        keyboard.unhook_all_hotkeys()
    except Exception:
        pass
    root.destroy()

root = tk.Tk()
root.geometry('1100x800')
root.minsize(410, 230)
root.title(f'{APP_NAME} {VERSION}')

APP_DIR = Path(__file__).parent
icon_png_path = APP_DIR / 'icon.png'
try:
    if icon_png_path.exists():
        icon_image = tk.PhotoImage(file=str(icon_png_path))
        root.iconphoto(True, icon_image)
except Exception:
    pass
import tkinter.font as tkfont

default_font = tkfont.nametofont('TkDefaultFont')
default_font.configure(family='Segoe UI', size=10)
root.option_add('*Font', default_font)
output_font = tkfont.nametofont('TkFixedFont')
output_font.configure(size=10)

container = tk.Frame(root)
container.pack(fill='both', expand=True)

canvas = tk.Canvas(container, highlightthickness=0, bd=0)
vertical_scroll_global = tk.Scrollbar(container, orient='vertical', command=canvas.yview)
canvas.configure(yscrollcommand=vertical_scroll_global.set)

canvas.pack(side='left', fill='both', expand=True)
vertical_scroll_global.pack(side='right', fill='y')

scroll_frame = tk.Frame(canvas)
scroll_frame.grid_rowconfigure(0, weight=1)
scroll_frame.grid_columnconfigure(0, weight=1)
frame_id = canvas.create_window((0,0), window=scroll_frame, anchor='nw')

def _update_scroll_region(_event=None):
    canvas.configure(scrollregion=canvas.bbox('all'))
def _on_canvas_config(event):
    canvas.itemconfig(frame_id, width=event.width)
    required_height = scroll_frame.winfo_reqheight()
    if event.height > required_height:
        canvas.itemconfig(frame_id, height=event.height)
    else:
        canvas.itemconfig(frame_id, height=0)
    canvas.configure(scrollregion=canvas.bbox('all'))
scroll_frame.bind('<Configure>', _update_scroll_region)
canvas.bind('<Configure>', _on_canvas_config)

wrapper = tk.Frame(scroll_frame, padx=12, pady=12)
wrapper.rowconfigure(7, weight=1)
wrapper.columnconfigure(0, weight=1)
wrapper.grid(row=0, column=0, sticky='nsew')

settings = load_settings()

theme = tk.StringVar(value=settings['theme'])

BULLET = '▸'
instructions_text = (
    'VEP MIDI AutoMate will read a CSV file and automatically create MIDI Automation rows in Vienna Ensemble Pro 7 (VEP).\n\n'
    'What you need to do:\n'
    f' {BULLET} Open VEP with your target instance active on a screen with scaling set to 100%.\n'
    f' {BULLET} Choose your CSV file below.\n'
    f' {BULLET} Click "Let\'s AutoMate ▶" and do not touch your mouse or keyboard, except to press \'{ABORT_HOTKEY_STRING}\' to abort at any time.\n\n'
    'What ' + APP_NAME + ' will do:\n'
    + APP_NAME + ' will take control of your mouse and keyboard and use screen-grabs to link up the MIDI automation stored in your CSV file using the following algorithm.\n'
    f' {BULLET} import CSV file\n'
    f' {BULLET} find VEP window, maximise, bring to front, check for active instance, reset layout, maximise \'MIDI Controllers\' section \n'
    f' {BULLET} delete all current MIDI automation rows\n'
    f' {BULLET} investigate general layout and menu positions\n'
    f' {BULLET} for each item in your CSV file\n'
    f'    {BULLET} create new row in the \'MIDI Controllers\' section, scrolling down if needed\n'
    f'    {BULLET} select device, channel, cc\n'
    f'    {BULLET} input destination items\n\n'
    'Advice:\n'
    f' {BULLET} You can watch a video walkthrough on GitHub.\n'
    f' {BULLET} Sudden popups on your computer can confuse. Open VEP on a screen that is unlikely to see these.\n'
    f' {BULLET} This is designed to work as quickly as possible, so use \'slow mode\' if you want to watch more carefully.\n'
    f' {BULLET} Use the provided data.csv as a template for your CSV file; it has the necessary column headings.\n'
    f' {BULLET} If {APP_NAME} fails, it is most likely that something in your CSV file is not spelt correctly.\n'
    f' {BULLET} Avoid mixer channel names that are the same as plugin names or settings, this might lead to confusion during the destination input stage.\n'
    f' {BULLET} Use GitHub to report any problems and/or send your appreciation.'
    )

instructions = tk.Label(wrapper, text=instructions_text, justify='left', anchor='w', wraplength=1)
instructions.grid(row=0, column=0, columnspan=3, sticky='we', pady=(0,8))
def _sync_wrap(event):
    instructions.configure(wraplength=event.width)
instructions.bind('<Configure>', _sync_wrap)

github_link = tk.Label(wrapper, text='Open GitHub for documentation, tips, and updates.', font=('TkDefaultFont', 9, 'underline'), fg=PALETTES[theme.get()]['link'], cursor='hand2')
github_link.grid(row=1, column=0, sticky='e')
def _hover_on(event):
    palette = PALETTES[theme.get()]
    github_link.config(fg=palette['accent'], cursor='hand2')
def _hover_off(event):
    palette = PALETTES[theme.get()]
    github_link.config(fg=palette['link'], cursor='arrow')
github_link.bind('<Enter>', _hover_on)
github_link.bind('<Leave>', _hover_off)
def open_github(event):
    github_url = 'https://github.com/robertrussell22/VEP-MIDI-AutoMate'
    try:
        webbrowser.open_new(github_url)
    except Exception as e:
        messagebox.showerror(APP_NAME, f'Could not open browser: {e}. Please navigate to {github_url}.')
github_link.bind('<Button-1>', open_github)

def theme_toggle():
    apply_theme(theme.get())
    update_csv_status()
    save_settings(csv_path_string.get(), slow_mode.get(), theme.get())

separator = ttk.Separator(wrapper, orient='horizontal')
separator.grid(row=2, column=0, columnspan=3, sticky='ew', pady=(6,10))

csv_row = tk.Frame(wrapper)
csv_row.grid(row=3, column=0, columnspan=3, sticky='we')
csv_row.columnconfigure(0, weight=1)

csv_path_label = tk.Label(csv_row, text='CSV file')
csv_path_label.pack(side='left')

csv_path_string = tk.StringVar(value=settings['csv_path'])
csv_path_string.trace_add('write', lambda *args: update_csv_status())

entry_box = tk.Entry(csv_row, textvariable=csv_path_string)
entry_box.pack(side='left', fill='x', expand=True, padx=(6,8))
entry_box.bind('<FocusOut>', lambda x: update_csv_status())
entry_box.bind('<Return>', lambda x: update_csv_status())

button_browse = tk.Button(csv_row, text='Browse…', command=pick_csv)
button_browse.pack(side='left')

csv_status = tk.Label(wrapper, text='(waiting for CSV)', anchor='w', fg='#666')
csv_status.grid(row=4, column=0, columnspan=3, sticky='w', pady=(2,8))

modes_row = tk.Frame(wrapper)
modes_row.grid(row=5, column=0, columnspan=3, sticky='w')

slow_mode = tk.BooleanVar(value=settings['slow_mode'])
slow_mode_button = tk.Checkbutton(modes_row, text='Slow mode', variable=slow_mode)
slow_mode_button.pack(side='left')

radio_button_light_mode = tk.Radiobutton(modes_row, text='Light mode', variable=theme, value='light', command=theme_toggle)
radio_button_light_mode.pack(side='left', padx=(12,0))
radio_button_dark_mode = tk.Radiobutton(modes_row, text='Dark mode', variable=theme, value='dark', command=theme_toggle)
radio_button_dark_mode.pack(side='left', padx=(12,0))

button_start = tk.Button(wrapper, text='Let\'s AutoMate ▶', command=start)
button_start.grid(row=6, column=0, sticky='w', pady=(8,8))

logging_frame = tk.Frame(wrapper)
logging_frame.rowconfigure(0, weight=1, minsize=180)
logging_frame.columnconfigure(0, weight=1)
logging_frame.grid(row=7, column=0, columnspan=3, sticky='nsew')
scrollbar_horizontal = tk.Scrollbar(logging_frame, orient='horizontal')
scrollbar_vertical = tk.Scrollbar(logging_frame, orient='vertical')
logging_box = tk.Text(logging_frame, height=12, state='disabled', wrap='none', xscrollcommand=scrollbar_horizontal.set, yscrollcommand=scrollbar_vertical.set)
logging_box.configure(font=output_font)
scrollbar_horizontal.config(command=logging_box.xview)
scrollbar_vertical.config(command=logging_box.yview)
logging_box.grid(row=0, column=0, sticky='nsew')
scrollbar_horizontal.grid(row=1, column=0, sticky='ew')
scrollbar_vertical.grid(row=0, column=1, sticky='ns')

apply_theme(theme.get())

update_csv_status()

pump_updates()
abort_event = threading.Event()

root.protocol('WM_DELETE_WINDOW', on_close)
root.mainloop()
