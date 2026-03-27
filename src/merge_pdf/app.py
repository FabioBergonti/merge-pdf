#!/usr/bin/env python3
"""
PDF Merger (GUI)

- Select multiple PDF files (Shift/Ctrl click)
- Reorder them via drag-like Up/Down buttons
- Merge into a single output PDF

Requirements:
- Python 3.x
- pypdf
"""

import sys
import threading
import queue
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from pypdf import PdfWriter, PdfReader


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Merger")
        self.geometry("780x560")
        self.minsize(700, 480)

        self.output_path = tk.StringVar()
        self.log_q: queue.Queue = queue.Queue()
        self.worker_thread = None

        self._build_ui()
        self.after(100, self._poll_log_queue)

    # ── UI ────────────────────────────────────────────────────────────

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=12, pady=12)

        # ── file list + order buttons ─────────────────────────────────
        list_frame = ttk.LabelFrame(frm, text="PDF files to merge (top → bottom = page order)")
        list_frame.pack(fill="both", expand=True, **pad)

        inner = ttk.Frame(list_frame)
        inner.pack(fill="both", expand=True, padx=6, pady=6)

        # Listbox with scrollbar
        lb_frame = ttk.Frame(inner)
        lb_frame.pack(side="left", fill="both", expand=True)

        self.listbox = tk.Listbox(lb_frame, selectmode="extended", activestyle="dotbox")
        scroll = ttk.Scrollbar(lb_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)

        # Side buttons for ordering
        btn_frame = ttk.Frame(inner)
        btn_frame.pack(side="right", fill="y", padx=(6, 0))

        ttk.Button(btn_frame, text="Add files…", command=self._add_files).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="Remove selected", command=self._remove_selected).pack(fill="x", pady=2)
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=6)
        ttk.Button(btn_frame, text="⬆  Move Up", command=self._move_up).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="⬇  Move Down", command=self._move_down).pack(fill="x", pady=2)
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=6)
        ttk.Button(btn_frame, text="Sort A → Z", command=self._sort_az).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="Clear all", command=self._clear_all).pack(fill="x", pady=2)

        # ── output path ──────────────────────────────────────────────
        row_out = ttk.Frame(frm)
        row_out.pack(fill="x", **pad)
        ttk.Label(row_out, text="Output PDF:", width=14).pack(side="left")
        ttk.Entry(row_out, textvariable=self.output_path).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(row_out, text="Choose…", command=self._choose_output).pack(side="left")

        # ── merge button ─────────────────────────────────────────────
        row_btn = ttk.Frame(frm)
        row_btn.pack(fill="x", **pad)
        self.btn_merge = ttk.Button(row_btn, text="Merge PDFs", command=self._start_merge)
        self.btn_merge.pack(side="left")

        # ── progress ─────────────────────────────────────────────────
        row_prog = ttk.Frame(frm)
        row_prog.pack(fill="x", **pad)
        self.progress = ttk.Progressbar(row_prog, mode="determinate")
        self.progress.pack(fill="x", expand=True)

        # ── log area ─────────────────────────────────────────────────
        ttk.Label(frm, text="Log:").pack(anchor="w", padx=10, pady=(8, 0))
        self.txt = tk.Text(frm, height=8, wrap="word")
        self.txt.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt.configure(state="disabled")

    # ── file management ───────────────────────────────────────────────

    def _add_files(self):
        files = filedialog.askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if not files:
            return
        existing = list(self.listbox.get(0, "end"))
        for f in files:
            if f not in existing:
                self.listbox.insert("end", f)
        self._log(f"Added {len(files)} file(s). Total: {self.listbox.size()}")
        # Auto-suggest output path if empty
        if not self.output_path.get().strip() and files:
            folder = Path(files[0]).parent
            self.output_path.set(str(folder / "merged.pdf"))

    def _remove_selected(self):
        sel = list(self.listbox.curselection())
        for i in reversed(sel):
            self.listbox.delete(i)

    def _move_up(self):
        sel = list(self.listbox.curselection())
        if not sel or sel[0] == 0:
            return
        for i in sel:
            text = self.listbox.get(i)
            self.listbox.delete(i)
            self.listbox.insert(i - 1, text)
            self.listbox.selection_set(i - 1)

    def _move_down(self):
        sel = list(self.listbox.curselection())
        if not sel or sel[-1] == self.listbox.size() - 1:
            return
        for i in reversed(sel):
            text = self.listbox.get(i)
            self.listbox.delete(i)
            self.listbox.insert(i + 1, text)
            self.listbox.selection_set(i + 1)

    def _sort_az(self):
        items = list(self.listbox.get(0, "end"))
        items.sort(key=lambda p: Path(p).name.lower())
        self.listbox.delete(0, "end")
        for item in items:
            self.listbox.insert("end", item)

    def _clear_all(self):
        self.listbox.delete(0, "end")

    def _choose_output(self):
        f = filedialog.asksaveasfilename(
            title="Save merged PDF as",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if f:
            self.output_path.set(f)

    # ── merge logic ───────────────────────────────────────────────────

    def _validate(self):
        files = list(self.listbox.get(0, "end"))
        if len(files) < 2:
            messagebox.showerror("Error", "Add at least 2 PDF files to merge.")
            return None

        for f in files:
            p = Path(f)
            if not p.is_file():
                messagebox.showerror("Error", f"File not found:\n{f}")
                return None
            if p.suffix.lower() != ".pdf":
                messagebox.showerror("Error", f"Not a PDF file:\n{f}")
                return None

        out = self.output_path.get().strip()
        if not out:
            messagebox.showerror("Error", "Choose an output file path.")
            return None

        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Warn if output already exists
        if out_path.exists():
            ok = messagebox.askyesno(
                "Overwrite?",
                f"The file already exists:\n{out_path}\n\nOverwrite?",
            )
            if not ok:
                return None

        return files, out_path

    def _start_merge(self):
        if self.worker_thread and self.worker_thread.is_alive():
            return

        validated = self._validate()
        if not validated:
            return

        files, out_path = validated
        self.progress["value"] = 0
        self.progress["maximum"] = len(files)
        self.btn_merge.configure(state="disabled")

        self._log(f"Merging {len(files)} PDFs → {out_path}")

        self.worker_thread = threading.Thread(
            target=self._worker,
            args=(files, out_path),
            daemon=True,
        )
        self.worker_thread.start()

    def _worker(self, files: list[str], out_path: Path):
        writer = PdfWriter()
        total_pages = 0
        try:
            for i, f in enumerate(files, start=1):
                p = Path(f)
                reader = PdfReader(str(p))
                n_pages = len(reader.pages)
                for page in reader.pages:
                    writer.add_page(page)
                total_pages += n_pages
                self._log_q(f"[{i}/{len(files)}] {p.name} ({n_pages} pages)")
                self.log_q.put(("progress", i))

            with open(out_path, "wb") as fp:
                writer.write(fp)

            size_mb = out_path.stat().st_size / 1e6
            self.log_q.put(
                ("done", f"Merge complete! {total_pages} pages → {out_path.name} ({size_mb:.2f} MB)")
            )
        except Exception as e:
            self.log_q.put(("done", f"ERROR: {e}"))

    # ── logging helpers ───────────────────────────────────────────────

    def _log(self, msg: str):
        self.txt.configure(state="normal")
        self.txt.insert("end", msg + "\n")
        self.txt.see("end")
        self.txt.configure(state="disabled")

    def _log_q(self, msg: str):
        self.log_q.put(("log", msg))

    def _poll_log_queue(self):
        try:
            while True:
                kind, payload = self.log_q.get_nowait()
                if kind == "log":
                    self._log(payload)
                elif kind == "progress":
                    self.progress["value"] = payload
                elif kind == "done":
                    self._log(f"\n{payload}")
                    self.btn_merge.configure(state="normal")
        except queue.Empty:
            pass
        self.after(100, self._poll_log_queue)


def main():
    if sys.platform.startswith("win"):
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
