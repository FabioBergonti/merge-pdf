# merge-pdf 📄

A simple GUI tool to **select, reorder, and merge multiple PDF files** into a single document using [`pypdf`](https://pypdf.readthedocs.io/).

Designed to be easy to run for non-technical users while remaining fully scriptable and reproducible via `conda`.

Tested on **Windows**, should work on **Linux** and **macOS** as well. 🤞

## ⚡ Quick setup (conda)

1. Install [`miniforge`](https://github.com/robotology/robotology-superbuild/blob/master/doc/install-miniforge.md)
2. Create the environment:
   ```bash
   conda env create -f environment.yml
    ```
3. Activate it:
   ```bash
   conda activate merge-pdf
   ```
4. (Later) Update the environment:
   ```bash
   conda env update -f environment.yml --prune
   ```

The [`environment.yml`](environment.yml) installs:
* Python
* the local package (via `pip`), so the `merge-pdf` console command is registered

## ▶️ Run

After activating the environment launch the GUI:

```bash
merge-pdf
```

### How to use

1. Click **Add files…** and select multiple PDFs (use Shift/Ctrl to multi-select)
2. Reorder files with **⬆ Move Up** / **⬇ Move Down**, or click **Sort A → Z**
3. Choose the output file path
4. Click **Merge PDFs**

## 🚀 Ready-to-use launcher scripts

Launcher scripts allow starting the app without manually activating the environment.

Generate launchers with:
```bash
conda activate merge-pdf
python scripts/make_launcher.py
```

### Windows

* Use `run_merge_pdf.cmd`
* Double-click or run from a terminal

### Linux / macOS

* Use `run_merge_pdf.sh`
* The generator marks it executable
* If needed:

```bash
chmod +x run_merge_pdf.sh
```

## 📦 Build a standalone executable (no conda needed for end users)

You can package the app into a self-contained `.exe` using PyInstaller.

1. Activate the environment and install PyInstaller:
   ```bash
   conda activate merge-pdf
   pip install pyinstaller
   ```
2. Run the build script:
   ```bash
   python scripts/build_exe.py
   ```
   This creates `dist/merge-pdf/` containing `merge-pdf.exe` and all dependencies.

3. Share the **entire** `dist/merge-pdf/` folder with users — they just double-click `merge-pdf.exe`.

### Build options

| Flag | Effect |
|------|--------|
| *(none)* | **Recommended.** Folder bundle (`dist/merge-pdf/`). Fast startup. |
| `--onefile` | Single `.exe`. Slower first launch. |

> **Note:** A `--onedir` (default) bundle must be distributed as a folder; moving only the `.exe` out of it will break the app.
