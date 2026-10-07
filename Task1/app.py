"""DSP Toolkit - Tkinter GUI (Task 1). Run:  python app.py"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import dsp_core as dsp
import run_tests


class DSPApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DSP Toolkit")
        self.geometry("1100x650")
        self.signals = []            # list[dsp.Signal]
        self.counter = 0             # for naming results

        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        left = ttk.Frame(self, padding=8)
        left.pack(side="left", fill="y")
        right = ttk.Frame(self, padding=8)
        right.pack(side="right", fill="both", expand=True)

        # signal list
        ttk.Label(left, text="Signals (Ctrl/Shift+click to multi-select)").pack(anchor="w")
        self.listbox = tk.Listbox(left, selectmode="extended", width=32, height=12,
                                  exportselection=False)
        self.listbox.pack(fill="x", pady=4)

        row = ttk.Frame(left)
        row.pack(fill="x")
        ttk.Button(row, text="Load...", command=self.load_signal).pack(side="left", expand=True, fill="x")
        ttk.Button(row, text="Save selected", command=self.save_signal).pack(side="left", expand=True, fill="x")
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

        # operations
        ops = ttk.LabelFrame(left, text="Operations", padding=6)
        ops.pack(fill="x")
        ttk.Button(ops, text="Add selected (any number)", command=self.do_add).pack(fill="x", pady=1)
        ttk.Button(ops, text="Subtract (top selected - others)", command=self.do_subtract).pack(fill="x", pady=1)

        r = ttk.Frame(ops); r.pack(fill="x", pady=1)
        ttk.Label(r, text="Constant:").pack(side="left")
        self.const_var = tk.StringVar(value="5")
        ttk.Entry(r, textvariable=self.const_var, width=8).pack(side="left", padx=4)
        ttk.Button(r, text="Multiply", command=self.do_multiply).pack(side="left", expand=True, fill="x")

        r = ttk.Frame(ops); r.pack(fill="x", pady=1)
        ttk.Label(r, text="k steps:").pack(side="left")
        self.k_var = tk.StringVar(value="3")
        ttk.Entry(r, textvariable=self.k_var, width=8).pack(side="left", padx=4)
        ttk.Button(r, text="Advance x(n+k)", command=lambda: self.do_shift(+1)).pack(side="left", expand=True, fill="x")
        ttk.Button(ops, text="Delay x(n-k)", command=lambda: self.do_shift(-1)).pack(fill="x", pady=1)
        ttk.Button(ops, text="Fold x(-n)", command=self.do_fold).pack(fill="x", pady=1)

        ttk.Button(left, text="Run provided test cases", command=self.show_tests).pack(fill="x", pady=(10, 0))

        # plot area
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        NavigationToolbar2Tk(self.canvas, right).update()

    # ------------------------------------------------------------- helpers
    def _selected(self):
        return [self.signals[i] for i in self.listbox.curselection()]

    def _refresh_list(self, select_last=False):
        self.listbox.delete(0, "end")
        for s in self.signals:
            self.listbox.insert("end", f"{s.name}  (N={len(s)})")
        if select_last and self.signals:
            self.listbox.selection_set("end")

    def _add_result(self, sig):
        self.counter += 1
        sig.name = f"{sig.name} [{self.counter}]"
        self.signals.append(sig)
        self._refresh_list()
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set("end")
        self.plot_selected()

    def _need(self, n, exact=False):
        sel = self._selected()
        if len(sel) < n or (exact and len(sel) != n):
            messagebox.showwarning("Selection", f"Select {'exactly ' if exact else 'at least '}{n} signal(s).")
            return None
        return sel

    def _get_float(self, var, what):
        try:
            return float(var.get())
        except ValueError:
            messagebox.showerror("Invalid input", f"{what} must be a number.")
            return None

    # --------------------------------------------------------------- file
    def load_signal(self):
        paths = filedialog.askopenfilenames(title="Open signal file(s)",
                                            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        for p in paths:
            try:
                self.signals.append(dsp.read_signal(p))
            except Exception as e:
                messagebox.showerror("Could not read file", f"{p}\n\n{e}")
        self._refresh_list()

    def save_signal(self):
        sel = self._need(1, exact=True)
        if not sel:
            return
        p = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if p:
            dsp.write_signal(sel[0], p)

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
            if self.plot_style.get() == "stem":
                ax.stem(s.indices, s.samples, linefmt=c + "-", markerfmt=c + "o",
                        basefmt="k-", label=s.name)
            else:
                ax.plot(s.indices, s.samples, color=c, marker="o", label=s.name)
            ax.axhline(0, color="k", lw=0.5)
            ax.grid(True, alpha=0.3)
            ax.set_xlabel("n")
            ax.set_ylabel("x(n)")
            ax.set_title(s.name if not self.overlay.get() else "Signals")
            if self.overlay.get():
                ax.legend()
        self.fig.tight_layout()
        self.canvas.draw()

    # ----------------------------------------------------------- operations
    def do_add(self):
        sel = self._need(2)
        if sel:
            self._add_result(dsp.add_signals(sel, "sum"))

    def do_subtract(self):
        sel = self._need(2)
        if sel:
            self._add_result(dsp.subtract_signals(sel[0], sel[1:], "difference"))

    def do_multiply(self):
        sel = self._need(1, exact=True)
        c = self._get_float(self.const_var, "Constant")
        if sel and c is not None:
            self._add_result(dsp.multiply_by_constant(sel[0], c))

    def do_shift(self, direction):
        sel = self._need(1, exact=True)
        k = self._get_float(self.k_var, "k")
        if sel and k is not None:
            if not k.is_integer():
                messagebox.showerror("Invalid input", "k must be an integer.")
                return
            self._add_result(dsp.shift_signal(sel[0], direction * abs(int(k))))

    def do_fold(self):
        sel = self._need(1, exact=True)
        if sel:
            self._add_result(dsp.fold_signal(sel[0]))

    def show_tests(self):
        messagebox.showinfo("Test cases", "\n".join(run_tests.run_all()))


if __name__ == "__main__":
    DSPApp().mainloop()
