#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键构建 Windows 可执行文件。

用法:
    python build.py

产物: dist/图片水印工具.exe（单文件，免安装）
构建中间文件全部落在系统临时目录，不污染源码目录。
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

APP_NAME = "图片水印工具"
APP_NAME_EN = "WatermarkTool"
AUTHOR = "七角松子"
VERSION = "1.1.0.0"
VERSION_STR = "1.1.0"
DESCRIPTION = "图片水印工具 - 批量文字/图片平铺水印，实时预览，保持原图尺寸"
ROOT = Path(__file__).resolve().parent


def ensure_icon() -> Path:
    """用 Pillow 生成应用图标 assets/icon.ico（无需外部素材）。"""
    icon_path = ROOT / "assets" / "icon.ico"
    if icon_path.exists():
        return icon_path

    from PIL import Image, ImageDraw, ImageFont

    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([8, 8, size - 8, size - 8], radius=48, fill="#4f8cff")
    # 斜向"印"字，呼应平铺水印主题
    font_path = Path(r"C:\Windows\Fonts\msyh.ttc")
    font = ImageFont.truetype(str(font_path), 110) if font_path.exists() \
        else ImageFont.load_default()
    txt = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(txt).text((size / 2, size / 2), "印", font=font,
                             fill=(255, 255, 255, 200), anchor="mm")
    img.alpha_composite(txt.rotate(-25, resample=Image.BICUBIC, center=(size / 2, size / 2)))

    icon_path.parent.mkdir(exist_ok=True)
    img.save(icon_path, format="ICO",
             sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    print(f"[build] 图标已生成: {icon_path}")
    return icon_path


def write_version_file(path: Path) -> None:
    """生成 exe 版本信息（右键属性可见）。"""
    path.write_text(
        f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(filevers=({VERSION.replace('.', ', ')}), prodvers=({VERSION.replace('.', ', ')}),
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('080404B0', [
      StringStruct('CompanyName', '{AUTHOR}'),
      StringStruct('FileDescription', '{DESCRIPTION}'),
      StringStruct('FileVersion', '{VERSION_STR}'),
      StringStruct('InternalName', '{APP_NAME_EN}'),
      StringStruct('LegalCopyright', 'Copyright (c) 2026 {AUTHOR}'),
      StringStruct('OriginalFilename', '{APP_NAME}.exe'),
      StringStruct('ProductName', '{APP_NAME}'),
      StringStruct('ProductVersion', '{VERSION_STR}')])]),
    VarFileInfo([VarStruct('Translation', [2052, 1200])])
  ]
)
""",
        encoding="utf-8",
    )


def main() -> int:
    icon = ensure_icon()
    # PyInstaller 要求 specpath 与脚本在同一盘符，故临时目录放在项目内，结束后清理
    tmp = Path(tempfile.mkdtemp(prefix=".build_", dir=ROOT))
    try:
        return _build(icon, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _build(icon: Path, tmp: Path) -> int:
    version_file = tmp / "version.txt"
    write_version_file(version_file)

    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile", "--windowed",
        "--name", APP_NAME,
        "--icon", str(icon),
        "--version-file", str(version_file),
        "--add-data", f"{ROOT / 'index.html'};.",
        "--workpath", str(tmp / "work"),
        "--specpath", str(tmp),
        "--distpath", str(ROOT / "dist"),
        "app.py",
    ]
    print("[build] 运行:", " ".join(args))
    proc = subprocess.run(args, cwd=ROOT)
    if proc.returncode != 0:
        return proc.returncode

    exe = ROOT / "dist" / f"{APP_NAME}.exe"
    print(f"\n[build] 完成: {exe} ({exe.stat().st_size / 1024 / 1024:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
