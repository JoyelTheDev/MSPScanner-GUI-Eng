# -*- coding: UTF-8 -*-
import sys
import os


def hide_console():
    """Hide the console window when -no_console flag is present"""
    if "-no_console" in sys.argv:
        from win32console import GetConsoleWindow
        from win32gui import ShowWindow, SetWindowLong
        from win32con import SW_HIDE, GWL_EXSTYLE, WS_EX_TOOLWINDOW
        try:
            hwnd = GetConsoleWindow()
            if hwnd:
                ShowWindow(hwnd, SW_HIDE)
            SetWindowLong(hwnd, GWL_EXSTYLE, WS_EX_TOOLWINDOW)
        except Exception as e:
            # Suppress error silently
            pass

def main():
    hide_console()
    from time import perf_counter
    total_timer = perf_counter()
    
    from Gui.UserInterface import GUI

    gui_timer = perf_counter()
    root = GUI()
    print(f"GUI initialization time: {perf_counter() - gui_timer:.3f} seconds")
    print(f"Total startup time: {perf_counter() - total_timer:.3f} seconds")
    root.mainloop()
    
    # Redirect stderr to suppress error messages
    from io import BytesIO
    sys.stderr = BytesIO()


if __name__ == '__main__':
    sys.path.append(".")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
