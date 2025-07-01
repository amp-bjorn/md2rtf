
# Markdown to RTF Converter (with Obsidian Integration)

This tool converts Obsidian-style Markdown notes to rich text (RTF) documents. It provides a simple graphical interface built with Gooey and supports:

- Embedded image handling via Obsidian's `![[image.png]]` syntax  
- Automatic image and table resizing in the output RTF  
- Intelligent detection of attachment folders based on Obsidian's `.obsidian/app.json`

> ✨ Designed for users who want quick and consistent exports from their Obsidian vaults.

---

## 📸 Screenshot

![[screenshot/gui1.png]]

---

## 🚀 Features

- ✅ Converts Markdown to RTF  
- ✅ Resolves Obsidian-style image links  
- ✅ Scales images and tables automatically  
- ✅ Provides simple, user-friendly GUI  
- ✅ Auto-launches output in WordPad  

---

## 🛠 Requirements

- Python 3.8+  
- Pandoc (system-wide install)  
- Virtual environment with the following packages:

Gooey==1.0.8.1  
pypandoc==1.14

---

## 🐍 Setup

1. **Clone or download this repository.**
2. **Create and activate a virtual environment:**

   ```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

3. **Install Python requirements:**
```bash
pip install -r requirements.txt
```

4. **Install Pandoc (required by pypandoc):**
```bash 
winget install pandoc
```

5. You can verify installation with:
```bash 
`pandoc --version`
```

---
## 🖥 Building the EXE (optional)

If you want to create a standalone executable using **PyInstaller**:
```bash
pyinstaller --noconfirm --onefile --add-data "pandoc/pandoc.exe;pandoc" --windowed src/md2rtf_gui.py
```

> This bundles `pandoc.exe` directly with the application. The script dynamically uses the internal copy if running from a PyInstaller bundle.

---
## 📂 How It Works

1. User selects a `.md` file from an Obsidian vault.
2. The script:
    - Locates `.obsidian/app.json`
    - Detects the image store path
    - Adjusts image links in Markdown
    - Converts the result to `.rtf`
    - Resizes images/tables
    - Opens the RTF in WordPad