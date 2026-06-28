from __future__ import annotations

import socket
import sys
import threading
import time
from typing import Any

import uvicorn


class DesktopApi:
    def __init__(self):
        self.window = None
        self._is_fullscreen = False
        self._stop_server = None

    def minimize(self):
        if self.window is not None:
            self.window.minimize()

    def toggle_maximize(self):
        if self.window is None:
            return
        if self._is_fullscreen:
            self.window.restore()
        else:
            import ctypes
            from ctypes import wintypes
            rect = wintypes.RECT()
            # SPI_GETWORKAREA = 0x0030, gets desktop area excluding taskbar
            ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
            self.window.move(rect.left, rect.top)
            self.window.resize(rect.right - rect.left, rect.bottom - rect.top)
        self._is_fullscreen = not self._is_fullscreen

    def close(self):
        if self._stop_server is not None:
            self._stop_server()
        if self.window is not None:
            self.window.destroy()


def wait_for_port(host: str, port: int, timeout: float = 30.0):
    deadline = time.monotonic() + timeout
    connect_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((connect_host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"lc_agent desktop server did not listen on {connect_host}:{port} within {timeout:.0f}s")


def run_desktop(app: Any, host: str, port: int, title: str = "lc-agent"):
    try:
        import webview
    except ImportError as exc:
        raise RuntimeError("Desktop mode requires pywebview. Install it with: pip install pywebview") from exc

    sys.setrecursionlimit(10000)

    api = DesktopApi()
    config = uvicorn.Config(app.fastapi_app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    api._stop_server = lambda: setattr(server, "should_exit", True)

    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    wait_for_port(host, port)

    url_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    window = webview.create_window(
        title=title,
        url=f"http://{url_host}:{port}/?desktop=1",
        width=1400,
        height=900,
        min_size=(960, 640),
        frameless=True,
        easy_drag=False,
        on_top=True,
        js_api=api,
    )
    api.window = window

    def _on_shown():
        time.sleep(1)
        if window:
            window.on_top = False

    window.events.shown += _on_shown

    try:
        webview.start(private_mode=False)
    finally:
        server.should_exit = True
        server_thread.join(timeout=5)
