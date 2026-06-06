"""BurstRender GUI — guided detect → preview → render workflow (Tkinter).

A thin shell over imageautomation.pipeline: builds the same runtime state
the CLI builds from argparse, then drives the shared core on a worker
thread. One core, two faces.
"""

import os
import pathlib
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from loguru import logger

from imageautomation import pipeline
from imageautomation import runtime as config
from imageautomation.binaries import doctor

GRAVITY_CHOICES = [
    "(default)", "NorthWest", "North", "NorthEast", "West",
    "Center", "East", "SouthWest", "South", "SouthEast",
]


class BurstRenderGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BurstRender")
        self.geometry("900x680")
        self.minsize(760, 560)

        self.log_queue = queue.Queue()
        self.worker = None
        self.burst_info = []
        self.burst_files = []
        self.preview_index = 0
        self._preview_photo = None  # keep a reference or Tk drops the image

        # BUNDLE-CRITICAL, not cosmetic: quiet=True is what keeps tqdm and
        # PrintLog's print() calls away from the None stdout/stderr of a
        # console=False frozen exe. Flipping this crashes the Windows GUI.
        config.quiet = True
        logger.remove()
        logger.add(self._log_sink, level="INFO", format="{level}: {message}")

        # File log so a bundled (console-less) GUI still leaves a trail
        if sys.platform == "win32":
            log_base = pathlib.Path(os.environ.get("LOCALAPPDATA", pathlib.Path.home()))
            log_dir = log_base / "burstrender" / "logs"
        else:
            log_dir = pathlib.Path.home() / ".burstrender" / "logs"
        logger.add(
            str(log_dir / "burstrender-gui.log"),
            level="DEBUG",
            rotation="10 MB",
            retention=10,
        )
        self.log_file = log_dir / "burstrender-gui.log"

        self._build_widgets()
        self.after(100, self._drain_log_queue)

    # ---------- layout ----------

    def _build_widgets(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        self.notebook = nb

        nb.add(self._build_detect_tab(nb), text="1. Detect")
        nb.add(self._build_preview_tab(nb), text="2. Preview")
        nb.add(self._build_render_tab(nb), text="3. Render")

        # Log pane below the notebook
        log_frame = ttk.LabelFrame(self, text="Log")
        log_frame.pack(fill="both", padx=8, pady=(0, 8))
        self.log_text = tk.Text(log_frame, height=8, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True)

    def _build_detect_tab(self, parent):
        f = ttk.Frame(parent, padding=10)

        self.source_var = tk.StringVar()
        self.dest_var = tk.StringVar()
        self.filetype_var = tk.StringVar(value=".cr3")
        self.gap_var = tk.IntVar(value=2)
        self.minlen_var = tk.IntVar(value=10)

        row = 0
        ttk.Label(f, text="Photo folder:").grid(row=row, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.source_var, width=60).grid(row=row, column=1, sticky="we")
        ttk.Button(f, text="Browse…", command=lambda: self._pick_dir(self.source_var)).grid(row=row, column=2)

        row += 1
        ttk.Label(f, text="Output folder:").grid(row=row, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.dest_var, width=60).grid(row=row, column=1, sticky="we")
        ttk.Button(f, text="Browse…", command=lambda: self._pick_dir(self.dest_var)).grid(row=row, column=2)

        row += 1
        opts = ttk.Frame(f)
        opts.grid(row=row, column=0, columnspan=3, sticky="w", pady=8)
        ttk.Label(opts, text="File type:").pack(side="left")
        ttk.Radiobutton(opts, text="CR3 (RAW)", variable=self.filetype_var, value=".cr3").pack(side="left")
        ttk.Radiobutton(opts, text="JPG", variable=self.filetype_var, value=".jpg").pack(side="left", padx=(0, 16))
        ttk.Label(opts, text="Gap between bursts (s):").pack(side="left")
        ttk.Spinbox(opts, from_=1, to=60, textvariable=self.gap_var, width=4).pack(side="left", padx=(0, 16))
        ttk.Label(opts, text="Min photos per burst:").pack(side="left")
        ttk.Spinbox(opts, from_=1, to=200, textvariable=self.minlen_var, width=4).pack(side="left")

        row += 1
        self.detect_button = ttk.Button(f, text="Detect Bursts", command=self.on_detect)
        self.detect_button.grid(row=row, column=0, pady=8, sticky="w")
        self.detect_status = ttk.Label(f, text="")
        self.detect_status.grid(row=row, column=1, sticky="w")

        row += 1
        cols = ("burst", "start", "end", "frames", "orientation")
        self.burst_table = ttk.Treeview(f, columns=cols, show="headings", height=10)
        for col, w in zip(cols, (60, 200, 200, 80, 100)):
            self.burst_table.heading(col, text=col.title())
            self.burst_table.column(col, width=w, anchor="w")
        self.burst_table.grid(row=row, column=0, columnspan=3, sticky="nsew", pady=8)
        f.rowconfigure(row, weight=1)
        f.columnconfigure(1, weight=1)
        return f

    def _build_preview_tab(self, parent):
        f = ttk.Frame(parent, padding=10)

        self.crop_var = tk.StringVar()
        self.gravity_var = tk.StringVar(value="(default)")
        self.normalize_var = tk.BooleanVar(value=True)
        self.custom_vf_var = tk.StringVar()

        knobs = ttk.Frame(f)
        knobs.pack(fill="x")
        ttk.Label(knobs, text="Crop:").pack(side="left")
        ttk.Entry(knobs, textvariable=self.crop_var, width=18).pack(side="left", padx=(0, 12))
        ttk.Label(knobs, text="Gravity:").pack(side="left")
        ttk.Combobox(knobs, textvariable=self.gravity_var, values=GRAVITY_CHOICES,
                     state="readonly", width=12).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(knobs, text="Normalize", variable=self.normalize_var).pack(side="left", padx=(0, 12))
        ttk.Label(knobs, text="Custom -vf:").pack(side="left")
        ttk.Entry(knobs, textvariable=self.custom_vf_var, width=24).pack(side="left")

        actions = ttk.Frame(f)
        actions.pack(fill="x", pady=8)
        self.preview_button = ttk.Button(actions, text="Render Previews", command=self.on_preview)
        self.preview_button.pack(side="left")
        ttk.Button(actions, text="◀ Prev", command=lambda: self._show_preview(-1)).pack(side="left", padx=(16, 0))
        ttk.Button(actions, text="Next ▶", command=lambda: self._show_preview(1)).pack(side="left")
        self.preview_label_text = ttk.Label(actions, text="")
        self.preview_label_text.pack(side="left", padx=12)

        self.preview_canvas = ttk.Label(f, anchor="center")
        self.preview_canvas.pack(fill="both", expand=True)
        return f

    def _build_render_tab(self, parent):
        f = ttk.Frame(parent, padding=10)

        self.mp4_var = tk.BooleanVar(value=True)
        self.stab_var = tk.BooleanVar(value=True)
        self.gif_var = tk.BooleanVar(value=True)

        checks = ttk.Frame(f)
        checks.pack(fill="x")
        ttk.Checkbutton(checks, text="MP4", variable=self.mp4_var).pack(side="left")
        ttk.Checkbutton(checks, text="Stabilized MP4", variable=self.stab_var).pack(side="left", padx=12)
        ttk.Checkbutton(checks, text="GIF", variable=self.gif_var).pack(side="left")

        actions = ttk.Frame(f)
        actions.pack(fill="x", pady=8)
        self.render_button = ttk.Button(actions, text="Render All Bursts", command=self.on_render)
        self.render_button.pack(side="left")
        ttk.Button(actions, text="Open Output Folder", command=self.on_open_output).pack(side="left", padx=12)

        self.progress = ttk.Progressbar(f, mode="determinate")
        self.progress.pack(fill="x", pady=8)
        self.render_status = ttk.Label(f, text="")
        self.render_status.pack(anchor="w")
        return f

    # ---------- helpers ----------

    def _pick_dir(self, var):
        chosen = filedialog.askdirectory()
        if chosen:
            var.set(chosen)
            if var is self.source_var and not self.dest_var.get():
                self.dest_var.set(chosen)

    def _log_sink(self, message):
        self.log_queue.put(str(message).rstrip())

    def _drain_log_queue(self):
        try:
            while True:
                line = self.log_queue.get_nowait()
                self.log_text.configure(state="normal")
                self.log_text.insert("end", line + "\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(100, self._drain_log_queue)

    def _apply_runtime(self):
        """Push GUI state into the shared runtime config (same as CLI arg parsing)."""
        config.source_path = os.path.abspath(self.source_var.get() or ".")
        config.destination_path = os.path.abspath(self.dest_var.get() or os.getcwd())
        config.file_extension = self.filetype_var.get()
        config.seconds_between_bursts = int(self.gap_var.get())
        config.min_burst_length = int(self.minlen_var.get())
        config.crop_string = self.crop_var.get() or None
        gravity = self.gravity_var.get()
        config.gravity_string = None if gravity == "(default)" else gravity
        config.normalize_string = (
            ",normalize=blackpt=black:whitept=white:smoothing=50"
            if self.normalize_var.get()
            else ""
        )
        custom = self.custom_vf_var.get().strip()
        config.custom_vf_string = f",{custom}" if custom else ""

        if sys.platform == "win32":
            base = pathlib.Path(os.environ.get("LOCALAPPDATA", pathlib.Path.home()))
            config.working_directory = str(base / "burstrender" / "working")
        else:
            config.working_directory = str(pathlib.Path.home() / ".burstrender" / "working")
        pathlib.Path(config.working_directory).mkdir(parents=True, exist_ok=True)

    def _run_in_worker(self, fn, done_msg):
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("BurstRender", "A task is already running.")
            return

        self._set_buttons_enabled(False)

        def wrapped():
            try:
                fn()
                self.log_queue.put(done_msg)
            except Exception as exc:  # surface, never die silently
                self.log_queue.put(f"ERROR: {exc}")
            finally:
                # Cross-thread after() is safe: it only enqueues onto Tcl's
                # mutex-protected event queue; the callback runs on the main
                # thread. Requires the mainloop to be running (it is — workers
                # only start from button callbacks).
                self.after(0, lambda: self._set_buttons_enabled(True))

        self.worker = threading.Thread(target=wrapped, daemon=True)
        self.worker.start()

    def _set_buttons_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for btn in (self.detect_button, self.preview_button, self.render_button):
            btn.configure(state=state)

    # ---------- actions ----------

    def on_detect(self):
        if not self.source_var.get():
            messagebox.showwarning("BurstRender", "Pick a photo folder first.")
            return
        self._apply_runtime()
        self.detect_status.configure(text="Scanning…")

        def work():
            info, files = pipeline.detect(
                config.source_path,
                config.file_extension,
                config.seconds_between_bursts,
                config.min_burst_length,
            )
            self.burst_info, self.burst_files = info, files
            self.after(0, self._fill_burst_table)

        self._run_in_worker(work, "Detection complete.")

    def _fill_burst_table(self):
        self.burst_table.delete(*self.burst_table.get_children())
        for i, b in enumerate(self.burst_info):
            self.burst_table.insert("", "end", values=(
                i + 1, str(b["start"]), str(b["end"]), b["frames"],
                "landscape" if b["long_side"] == "width" else "portrait",
            ))
        n = len(self.burst_info)
        self.detect_status.configure(
            text=f"{n} burst(s) detected." if n else "No bursts found — try adjusting the knobs."
        )

    def on_preview(self):
        if not self.burst_files:
            messagebox.showwarning("BurstRender", "Run Detect first.")
            return
        self._apply_runtime()

        def work():
            for i in range(len(self.burst_files)):
                if not pipeline.render_sample(self.burst_files, i):
                    self.log_queue.put(f"Sample for burst {i + 1} failed.")
            self.after(0, lambda: self._show_preview(0, reset=True))

        self._run_in_worker(work, "Previews rendered.")

    def _show_preview(self, delta, reset=False):
        if not self.burst_files:
            return
        if reset:
            self.preview_index = 0
        else:
            self.preview_index = (self.preview_index + delta) % len(self.burst_files)
        png = (
            pathlib.Path(config.destination_path)
            / f"burst_{self.preview_index + 1}-testimage.png"
        )
        if not png.exists():
            self.preview_label_text.configure(text=f"burst {self.preview_index + 1}: no preview")
            return
        img = tk.PhotoImage(file=str(png))
        factor = max(1, img.width() // 760, img.height() // 480)
        if factor > 1:
            img = img.subsample(factor, factor)
        self._preview_photo = img
        self.preview_canvas.configure(image=img)
        self.preview_label_text.configure(
            text=f"burst {self.preview_index + 1} of {len(self.burst_files)}"
        )

    def on_render(self):
        if not self.burst_files:
            messagebox.showwarning("BurstRender", "Run Detect first.")
            return
        if not (self.mp4_var.get() or self.gif_var.get() or self.stab_var.get()):
            messagebox.showwarning("BurstRender", "Pick at least one output type.")
            return
        self._apply_runtime()
        total = len(self.burst_files)
        self.progress.configure(maximum=total, value=0)

        def work():
            done = 0
            for i in range(total):
                self.after(0, lambda i=i: self.render_status.configure(
                    text=f"Rendering burst {i + 1} of {total}…"))
                pipeline.process_burst(
                    self.burst_files[i],
                    i,
                    output_mp4=self.mp4_var.get(),
                    output_stabilized=self.stab_var.get(),
                    output_gif=self.gif_var.get(),
                    progress=lambda label: self.log_queue.put(f"  {label}"),
                )
                done += 1
                self.after(0, lambda d=done: self.progress.configure(value=d))
            self.after(0, lambda: self.render_status.configure(text="Done."))

        self._run_in_worker(work, "Render complete.")

    def on_open_output(self):
        dest = self.dest_var.get() or os.getcwd()
        if sys.platform == "win32":
            os.startfile(dest)  # noqa: S606 — intended behavior
        elif sys.platform == "darwin":
            subprocess.Popen(["open", dest])
        else:
            subprocess.Popen(["xdg-open", dest])


def main():
    import contextlib
    import io

    app = BurstRenderGUI()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        tools_ok = doctor()
    for line in buf.getvalue().splitlines():
        logger.info(line)
    if not tools_ok:
        messagebox.showwarning(
            "BurstRender",
            "Some required tools were not found — rendering will fail until "
            "this is resolved. Details are in the Log pane below and in:\n"
            f"{app.log_file}",
        )
    app.mainloop()


if __name__ == "__main__":
    main()
