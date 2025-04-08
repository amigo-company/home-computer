# Terminal
# Author: Daniel Ervilha
# Type: lib

# References:
# - https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797 (ANSI codes)
# - https://learn.microsoft.com/en-us/windows/console/input-record-str (Windows API INPUT_RECORD)
ABOUT = """
"""
import os

def size():
    ts = os.get_terminal_size()
    return ts.columns, ts.lines

# ANSI codes
def reset():
    return "\033[0m"

def bold():
    return "\033[1m"
def underline():
    return "\033[4m"
def inverse():
    return "\033[7m"

def erase_line():
    return "\033[2K"
def erase_screen():
    return "\033[2J"
def erase_saved_lines():
    return "\033[2J"

def move(x: int, y: int):
    return f"\033[{y +1};{x +1}H"

def bgd(r: int, g: int, b: int):
    return f"\033[48;2;{r};{g};{b}m"
def fgd(r: int, g: int, b: int):
    return f"\033[38;2;{r};{g};{b}m"

EVENT_KEYBOARD = 1
EVENT_MOUSE = 2

# Windows specific implementations
if os.name == 'nt':
    import ctypes
    import ctypes.wintypes as wintypes

    # Constants from Windows API
    _STD_INPUT_HANDLE = -10
    _STD_OUTPUT_HANDLE = -11
    _ENABLE_MOUSE_INPUT = 0x0010
    _ENABLE_EXTENDED_FLAGS = 0x0080
    _ENABLE_WINDOW_INPUT = 0x0008
    _FROM_LEFT_1ST_BUTTON_PRESSED = 0x0001
    _RIGHTMOST_BUTTON_PRESSED = 0x0002
    _MOUSE_MOVED = 0x0001
    _MOUSE_WHEELED = 0x0004

    # Structs from Windows API
    class COORD(ctypes.Structure):
        _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]

    class KEY_EVENT_RECORD(ctypes.Structure):
        _fields_ = [
            ("bKeyDown", wintypes.BOOL),
            ("wRepeatCount", wintypes.WORD),
            ("wVirtualKeyCode", wintypes.WORD),
            ("wVirtualScanCode", wintypes.WORD),
            ("uChar", wintypes.WCHAR),
            ("dwControlKeyState", wintypes.DWORD),
        ]

    class MOUSE_EVENT_RECORD(ctypes.Structure):
        _fields_ = [
            ("dwMousePosition", COORD),
            ("dwButtonState", wintypes.DWORD),
            ("dwControlKeyState", wintypes.DWORD),
            ("dwEventFlags", wintypes.DWORD),
        ]

    class EVENT_UNION(ctypes.Union):
        _fields_ = [
            ("KeyEvent", KEY_EVENT_RECORD),
            ("MouseEvent", MOUSE_EVENT_RECORD),
        ]

    class INPUT_RECORD(ctypes.Structure):
        _fields_ = [
            ("EventType", wintypes.WORD),
            ("Event", EVENT_UNION),
        ]

    # kernel32 config
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(_STD_INPUT_HANDLE)
    kernel32.SetConsoleMode(
        handle,
        _ENABLE_EXTENDED_FLAGS | _ENABLE_MOUSE_INPUT | _ENABLE_WINDOW_INPUT
    )

    # Events
    _forced_event_stack = []
    def force_event(event):
        _forced_event_stack.append(event)

    def read_event():
        if _forced_event_stack:
            return _forced_event_stack.pop()

        record = INPUT_RECORD()
        count = wintypes.DWORD()

        success = kernel32.PeekConsoleInputW(handle, ctypes.byref(record), 1, ctypes.byref(count))
        if not success or count.value == 0:
            return None

        kernel32.ReadConsoleInputW(handle, ctypes.byref(record), 1, ctypes.byref(count))

        if record.EventType == EVENT_KEYBOARD:
            key = record.Event.KeyEvent
            return {
                'type': EVENT_KEYBOARD,
                'key': ord(key.uChar),
                'press': key.bKeyDown,
                'keycode': key.wVirtualKeyCode,
                'scancode': key.wVirtualScanCode
            }

        if record.EventType == EVENT_MOUSE:
            mouse = record.Event.MouseEvent
            return {
                'type': EVENT_MOUSE,
                'event': mouse.dwEventFlags,
                'button': mouse.dwButtonState,
                'x': mouse.dwMousePosition.X,
                'y': mouse.dwMousePosition.Y,
            }

    # Cursor
    def hide_cursor():
        class CONSOLE_CURSOR_INFO(ctypes.Structure):
            _fields_ = [("dwSize", ctypes.c_int),
                        ("bVisible", ctypes.c_bool)]
        cursor_info = CONSOLE_CURSOR_INFO()
            
        stdout_handle = ctypes.windll.kernel32.GetStdHandle(_STD_OUTPUT_HANDLE)
        ctypes.windll.kernel32.GetConsoleCursorInfo(stdout_handle, ctypes.byref(cursor_info))
        cursor_info.bVisible = False
        ctypes.windll.kernel32.SetConsoleCursorInfo(stdout_handle, ctypes.byref(cursor_info))

    # Window title
    def set_title(title: str):
        kernel32.SetConsoleTitleW(title)
        # os.system(f"title {title}") # closed alternative

else:
    raise NotImplementedError("UNIX systems are not yet implemented. Please yell at me.")