"""DSP Toolkit - Tkinter GUI (Task 2). Run:  python app.py"""
import math
import tkinter as tk
from tkinter import ttk, messagebox

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import dsp_core as dsp


class GenerateDialog(tk.Toplevel):
    """Asks for A, theta, F and Fs of a sine / cosine wave. Result is stored in self.result."""

    def __init__(self, parent, kind):
        super().__init__(parent)
        self.kind = kind
        self.result = None
        self.title("Sine wave" if kind == "sine" else "Cosine wave")
        self.resizable(False, False)
        self.transient(parent)

        fn = "sin" if kind == "sine" else "cos"
        frm = ttk.Frame(self, padding=12)
        frm.pack()
        ttk.Label(frm, text=f"x(t) = A {fn}(2 pi F t + theta)").grid(row=0, column=0, columnspan=2, pady=(0, 8))

        self.vars = {}
        fields = [("A", "Amplitude A", "1"), ("theta", "Phase shift theta (radians, e.g. 0.5 or pi/4)", "0"),
                  ("F", "Analog frequency F (Hz)", "5"), ("Fs", "Sampling frequency Fs (Hz)", "100")]
        for r, (key, text, default) in enumerate(fields, start=1):
            ttk.Label(frm, text=text).grid(row=r, column=0, sticky="w", pady=2)
            self.vars[key] = tk.StringVar(value=default)
            ttk.Entry(frm, textvariable=self.vars[key], width=10).grid(row=r, column=1, padx=6)
        ttk.Label(frm, text="Fs must be greater than 2F (sampling theorem).").grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(6, 0))

        row = ttk.Frame(frm)
        row.grid(row=6, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(row, text="Generate", command=self.ok).pack(side="left", padx=4)
        ttk.Button(row, text="Cancel", command=self.destroy).pack(side="left")
        self.bind("<Return>", lambda e: self.ok())
        self.grab_set()

    @staticmethod
    def _number(text):
        text = text.strip().lower().replace("pi", str(math.pi))
        allowed = set("0123456789.+-*/() e")
        if not text or not set(text) <= allowed:
            raise ValueError
        return float(eval(text, {"__builtins__": {}}))

    def ok(self):
        try:
            values = {k: self._number(v.get()) for k, v in self.vars.items()}
        except Exception:
            messagebox.showerror("Invalid input", "A, theta, F and Fs must be numbers.", parent=self)
            return
        try:
            self.result = dsp.generate_signal(self.kind, values["A"], values["theta"],
                                              values["F"], values["Fs"])
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e), parent=self)
            return
        self.destroy()


class DSPApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DSP Toolkit")
        self.geometry("1100x650")
        self.signals = []            # list[dsp.Signal]

        self._build_menu()
        self._build_ui()

    # ---------------------------------------------------------------- menu
    def _build_menu(self):
        menubar = tk.Menu(self)
        gen = tk.Menu(menubar, tearoff=0)
        gen.add_command(label="Sine wave", command=lambda: self.generate("sine"))
        gen.add_command(label="Cosine wave", command=lambda: self.generate("cosine"))
        menubar.add_cascade(label="Signal Generation", menu=gen)
        self.config(menu=menubar)

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        left = ttk.Frame(self, padding=8)
        left.pack(side="left", fill="y")
        right = ttk.Frame(self, padding=8)
        right.pack(side="right", fill="both", expand=True)

        # signal list
        ttk.Label(left, text="Signals (Ctrl/Shift+click to select two)").pack(anchor="w")
        self.listbox = tk.Listbox(left, selectmode="extended", width=32, height=12,
                                  exportselection=False)
        self.listbox.pack(fill="x", pady=4)
        ttk.Button(left, text="Remove selected", command=self.remove_signals).pack(fill="x")

        # display
        box = ttk.LabelFrame(left, text="Display", padding=6)
        box.pack(fill="x", pady=8)
        self.plot_style = tk.StringVar(value="stem")
        ttk.Radiobutton(box, text="Discrete (stem)", variable=self.plot_style, value="stem").pack(anchor="w")
        ttk.Radiobutton(box, text="Continuous (line)", variable=self.plot_style, value="line").pack(anchor="w")
        self.overlay = tk.BooleanVar(value=False)
        ttk.Checkbutton(box, text="Overlay on one plot", variable=self.overlay).pack(anchor="w")
        ttk.Button(box, text="Plot selected", command=self.plot_selected).pack(fill="x", pady=(4, 0))

        # plot area
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        NavigationToolbar2Tk(self.canvas, right).update()

    # ------------------------------------------------------------- helpers
    def _selected(self):
        return [self.signals[i] for i in self.listbox.curselection()]

    def _refresh_list(self):
        self.listbox.delete(0, "end")
        for s in self.signals:
            self.listbox.insert("end", f"{s.name}  (N={len(s)})")

    # ---------------------------------------------------------- generation
    def generate(self, kind):
        dlg = GenerateDialog(self, kind)
        self.wait_window(dlg)
        if dlg.result:
            self.signals.append(dlg.result)
            self._refresh_list()
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set("end")
            self.plot_selected()

    def remove_signals(self):
        keep = set(self.listbox.curselection())
        self.signals = [s for i, s in enumerate(self.signals) if i not in keep]
        self._refresh_list()

    # ---------------------------------------------------------------- plot
    def plot_selected(self):
        sel = self._selected()
        if not sel:
            messagebox.showinfo("Plot", "Select a signal to display.")
            return
        self.fig.clear()
        colors = ["C0", "C1", "C2", "C3", "C4", "C5"]
        n = 1 if self.overlay.get() else len(sel)
        axes = [self.fig.add_subplot(n, 1, i + 1) for i in range(n)]
        for k, s in enumerate(sel):
            ax = axes[0] if self.overlay.get() else axes[k]
            c = colors[k % len(colors)]
            if self.plot_style.get() == "stem":          # discrete x(n) drawn at t = n/Fs
                t = [i / s.params["Fs"] for i in s.indices]
                ax.stem(t, s.samples, linefmt=c + "-", markerfmt=c + "o",
                        basefmt="k-", label=s.name)
            else:                                        # continuous x(t)
                t, x = dsp.analog_curve(s)
                ax.plot(t, x, color=c, label=s.name)
            ax.axhline(0, color="k", lw=0.5)
            ax.grid(True, alpha=0.3)
            ax.set_xlabel("t (s)")
            ax.set_ylabel("x(n)" if self.plot_style.get() == "stem" else "x(t)")
            ax.set_title(s.name if not self.overlay.get() else "Signals")
            if self.overlay.get():
                ax.legend()
        self.fig.tight_layout()
        self.canvas.draw()


if __name__ == "__main__":
    DSPApp().mainloop()
