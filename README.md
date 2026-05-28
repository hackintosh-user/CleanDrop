# ✦ CleanDrop

**A sleek Downloads folder cleaner with a modern GUI — built with CustomTkinter.**

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2+-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## Features

- 📁 **Smart Sorting** — Automatically categorizes files into Images, Videos, Audio, Documents, Archives, Apps, Code, and Other
- 👀 **File Preview** — See exactly what will be moved before anything happens
- ↩️ **Undo Last Clean** — Restore all files from the last session in one click
- 🌙 **Dark / Light Mode** — Toggle between themes on the fly
- 📊 **Stats Bar** — See total file count, size, and category breakdown at a glance
- 🔍 **Category Filter** — Filter the file list by category before cleaning
- ✅ **Selective Clean** — Check/uncheck individual files, or select/deselect all

---

## Installation

### Prerequisites
- Python 3.10 or later

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/cleandrop.git
cd cleandrop

# 2. Install dependencies
pip install -r requirements.txt
# or on macOS/Linux:
pip3 install -r requirements.txt

# 3. Run
python main.py
# or on macOS/Linux:
python3 main.py
```

---

## Usage

1. Launch the app
2. The default folder is your **Downloads** folder — or click **Browse** to pick another
3. Click **⟳ Scan** to scan the folder
4. Review the file list — check/uncheck files as needed
5. Click **🧹 Clean Selected** and confirm
6. Files are moved into subfolders: `Images/`, `Videos/`, `Documents/`, etc.
7. Made a mistake? Hit **↩ Undo** to restore everything

---

## Folder Structure After Clean

```
Downloads/
├── Images/
├── Videos/
├── Audio/
├── Documents/
├── Archives/
├── Apps/
├── Code/
└── Other/
```

---

## File Categories

| Category   | Extensions |
|------------|-----------|
| 🖼 Images  | jpg, jpeg, png, gif, bmp, svg, webp, ico, tiff, heic, raw |
| 🎬 Videos  | mp4, mov, avi, mkv, wmv, flv, webm, m4v, mpeg |
| 🎵 Audio   | mp3, wav, aac, flac, ogg, m4a, wma, aiff |
| 📄 Documents | pdf, doc, docx, xls, xlsx, ppt, pptx, txt, rtf, odt, csv |
| 📦 Archives | zip, rar, 7z, tar, gz, bz2, xz, dmg, iso |
| 💻 Apps    | exe, msi, pkg, app, deb, rpm, apk |
| 💾 Code    | py, js, ts, html, css, json, xml, sh, bat, java, cpp, c, go, rs |
| 🗂 Other   | Everything else |

---

## License

MIT — do whatever you want with it.

---

*Built with Python & CustomTkinter*
