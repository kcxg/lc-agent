from __future__ import annotations

import multiprocessing
import socket
import time
from pathlib import Path
import sys


def wait_for_port(host: str, port: int, timeout: float = 30.0):
    deadline = time.monotonic() + timeout
    connect_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((connect_host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def get_work_area() -> tuple[int, int, int, int]:
    try:
        import ctypes
        from ctypes import wintypes

        rect = wintypes.RECT()
        if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
    except Exception:
        pass
    return 0, 0, 1400, 900


def get_webview_storage_path() -> str:
    path = Path.cwd() / ".tmp" / "webview2-data"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def _apply_dark_titlebar(title: str):
    """Set dark/themed title bar on Windows 10/11 via DWM API."""
    import os
    import time

    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        dwm = ctypes.windll.dwmapi

        dwm.DwmSetWindowAttribute.argtypes = [
            wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
        ]
        dwm.DwmSetWindowAttribute.restype = ctypes.HRESULT

        # Find the webview window by enumerating windows in this process
        pid = os.getpid()
        candidates: list[int] = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def _enum_cb(h, _lp):
            wpid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(h, ctypes.byref(wpid))
            if wpid.value == pid and user32.IsWindowVisible(h):
                candidates.append(h)
            return True

        for _ in range(20):
            candidates.clear()
            user32.EnumWindows(_enum_cb, 0)
            if candidates:
                break
            time.sleep(0.5)

        if not candidates:
            print(f"[Desktop] No visible window found in PID {pid}")
            return

        for hwnd in candidates:
            dark = ctypes.c_int(1)
            # Try attribute 20 (Win10 20H1+), fallback to 19 (pre-20H1)
            hr = dwm.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark), 4)
            if hr != 0:
                dwm.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(dark), 4)

            # DWMWA_CAPTION_COLOR = 35 (Windows 11+)
            # #141414 matches Element Plus dark --el-bg-color
            color = ctypes.c_uint(0x00141414)
            hr35 = dwm.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(color), 4)

            # Force non-client area redraw
            user32.SetWindowPos(
                hwnd, 0, 0, 0, 0, 0,
                0x0020 | 0x0001 | 0x0002 | 0x0004,  # FRAMECHANGED|NOSIZE|NOMOVE|NOZORDER
            )
            print(f"[Desktop] Dark titlebar applied (hwnd={hwnd}, caption_hr={hr35:#x})")

    except Exception as e:
        print(f"[Desktop] Failed to set dark titlebar: {e}")


def _apply_window_icon(title: str):
    """Set the window/taskbar icon to favicon.ico via Win32 API."""
    import os

    try:
        import ctypes
        from ctypes import wintypes

        ico_path = str(Path(__file__).parent / "web" / "dist" / "favicon.ico")
        if not Path(ico_path).exists():
            return

        user32 = ctypes.windll.user32
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x0010
        LR_DEFAULTSIZE = 0x0040
        WM_SETICON = 0x0080
        ICON_BIG = 1
        ICON_SMALL = 0

        pid = os.getpid()
        candidates: list[int] = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def _enum_cb(h, _lp):
            wpid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(h, ctypes.byref(wpid))
            if wpid.value == pid and user32.IsWindowVisible(h):
                candidates.append(h)
            return True

        user32.EnumWindows(_enum_cb, 0)

        for hwnd in candidates:
            big = user32.LoadImageW(0, ico_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
            small = user32.LoadImageW(0, ico_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
            if big:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, big)
            if small:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, small)
            print(f"[Desktop] Window icon set (hwnd={hwnd})")
    except Exception as e:
        print(f"[Desktop] Failed to set window icon: {e}")


def _webview_process(url: str, title: str):
    """Entry point for the webview subprocess."""
    try:
        import webview
    except ImportError:
        print("[Desktop] pywebview not installed, skipping desktop window.")
        return

    x, y, width, height = get_work_area()
    webview.create_window(
        title=title,
        url=url,
        x=x,
        y=y,
        width=width,
        height=height,
        min_size=(800, 600),
        text_select=True,
    )

    def on_started():
        _apply_dark_titlebar(title)
        _apply_window_icon(title)

    webview.start(private_mode=False, storage_path=get_webview_storage_path(), func=on_started)


def launch_desktop(host: str, port: int, title: str = "lc-agent") -> multiprocessing.Process | None:
    """Launch a webview window in a subprocess pointing at the server.

    Returns the Process object (or None if the server is not reachable).
    The caller (uvicorn main process) keeps running regardless of whether
    the webview is open or closed.
    """
    url_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"http://{url_host}:{port}/"
    if not wait_for_port(host, port, timeout=5.0):
        print(f"服务器 {host}:{port} 未响应")
        sys.exit(1)
    _webview_process(url, title)

    # proc = multiprocessing.Process(
    #     target=_webview_process,
    #     args=(url, title),
    #     daemon=True,
    # )
    # proc.start()
    # return proc


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Open lc-agent desktop window")
    parser.add_argument("--url", default=None, help="Server URL to open")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--title", default="lc-agent", help="Window title")
    args = parser.parse_args()

    url = args.url or f"http://{args.host}:{args.port}/"
    print(f"[Desktop] Opening {url}")

    if not wait_for_port(args.host, args.port, timeout=5.0):
        print(f"[Desktop] Warning: server at {args.host}:{args.port} not reachable, opening anyway.")

    _webview_process(url, args.title)
