#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图片水印工具 - 桌面应用入口。

使用 pywebview 以系统 WebView2 承载 index.html 界面，
并通过 JS API 桥提供原生文件保存对话框。
"""

import base64
import os
import sys

import webview

APP_TITLE = "图片水印工具"

# WebView2 运行时的固定客户端 ID（微软官方约定）
_WEBVIEW2_GUID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
_WEBVIEW2_DOWNLOAD_URL = "https://developer.microsoft.com/zh-cn/microsoft-edge/webview2/"


def webview2_installed() -> bool:
    """检测系统是否安装 Edge WebView2 运行时（查注册表）。

    Windows 11 及已更新的 Windows 10 通常已预装；
    精简版 / LTSC / 长期未更新的系统可能缺失。
    """
    import winreg

    locations = [
        (winreg.HKEY_LOCAL_MACHINE,
         rf"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{_WEBVIEW2_GUID}"),
        (winreg.HKEY_LOCAL_MACHINE,
         rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{_WEBVIEW2_GUID}"),
        (winreg.HKEY_CURRENT_USER,
         rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{_WEBVIEW2_GUID}"),
    ]
    for root, path in locations:
        try:
            with winreg.OpenKey(root, path) as key:
                pv, _ = winreg.QueryValueEx(key, "pv")
                if pv and pv != "0.0.0.0":
                    return True
        except OSError:
            continue
    return False


def prompt_install_webview2() -> None:
    """提示用户下载 WebView2 运行时后退出。"""
    import ctypes
    import webbrowser

    MB_YESNO = 0x4
    MB_ICONWARNING = 0x30
    IDYES = 6
    answer = ctypes.windll.user32.MessageBoxW(
        0,
        "本程序依赖 Microsoft Edge WebView2 运行时，当前系统未安装。\n\n"
        "WebView2 是微软官方组件，Windows 11 和已更新的 Windows 10 自带；"
        "部分精简版 / 企业版系统需要手动安装（约几 MB，一次安装永久有效）。\n\n"
        "是否现在打开微软官方下载页面？",
        APP_TITLE + " - 缺少运行组件",
        MB_YESNO | MB_ICONWARNING,
    )
    if answer == IDYES:
        webbrowser.open(_WEBVIEW2_DOWNLOAD_URL)


def resource_path(rel: str) -> str:
    """兼容 PyInstaller 打包后的资源路径。"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def _unique_path(path: str) -> str:
    """目标文件已存在时自动追加 (1)、(2)… 后缀，避免覆盖。"""
    if not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f"{stem} ({i}){ext}"):
        i += 1
    return f"{stem} ({i}){ext}"


class Api:
    """暴露给前端的原生能力。"""

    def save_files(self, files):
        """保存文件。单个文件弹"另存为"，多个文件弹"选择文件夹"。

        files: [{"name": "xxx.png", "data": "<base64>"}, ...]
        return: {"saved": int, "canceled": bool}
        """
        if not files:
            return {"saved": 0, "canceled": False}

        window = webview.windows[0]

        if len(files) == 1:
            result = window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=files[0]["name"],
                file_types=("图片文件 (*.png;*.jpg;*.webp)", "所有文件 (*.*)"),
            )
            if not result:
                return {"saved": 0, "canceled": True}
            path = result if isinstance(result, str) else result[0]
            self._write(path, files[0]["data"])
            return {"saved": 1, "canceled": False}

        result = window.create_file_dialog(webview.FOLDER_DIALOG)
        if not result:
            return {"saved": 0, "canceled": True}
        folder = result if isinstance(result, str) else result[0]
        saved = 0
        for f in files:
            self._write(_unique_path(os.path.join(folder, f["name"])), f["data"])
            saved += 1
        return {"saved": saved, "canceled": False}

    @staticmethod
    def _write(path: str, b64: str) -> None:
        with open(path, "wb") as fh:
            fh.write(base64.b64decode(b64))


def main() -> None:
    if not webview2_installed():
        prompt_install_webview2()
        sys.exit(1)

    webview.create_window(
        APP_TITLE,
        resource_path("index.html"),
        width=1280,
        height=840,
        min_size=(960, 640),
        js_api=Api(),
    )
    webview.start()


if __name__ == "__main__":
    main()
