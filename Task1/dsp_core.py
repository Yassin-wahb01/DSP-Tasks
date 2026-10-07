"""Core DSP logic (no GUI code here) - reused by all future tasks."""
from __future__ import annotations
import os
from dataclasses import dataclass, field


@dataclass
class Signal:
    name: str
    indices: list = field(default_factory=list)
    samples: list = field(default_factory=list)
    is_periodic: int = 0

    def __len__(self):
        return len(self.indices)

    def as_dict(self):
        return dict(zip(self.indices, self.samples))


# ---------------------------------------------------------------- file I/O
def read_signal(path: str) -> Signal:
    """Read a signal from a txt file.

    Supported layouts:
      * course layout : line1 = signal type (0 time / 1 freq), line2 = is periodic,
                        line3 = N, then N lines of "index value"
      * simple layout : line1 = N, then N lines of "index value"
    """
    with open(path, "r") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    if not lines:
        raise ValueError("File is empty")

    def is_single_int(s):
        parts = s.split()
        if len(parts) != 1:
            return False
        try:
            int(parts[0])
            return True
        except ValueError:
            return False

    # decide how many header lines there are
    if len(lines) >= 3 and all(is_single_int(l) for l in lines[:3]):
        is_periodic = int(lines[1])
        n = int(lines[2])
        data = lines[3:]
    elif is_single_int(lines[0]):
        is_periodic = 0
        n = int(lines[0])
        data = lines[1:]
    else:
        raise ValueError("First row must contain N (number of samples)")

    idx, val = [], []
    for ln in data[:n]:
        parts = ln.replace(",", " ").split()
        if len(parts) != 2:
            raise ValueError(f"Bad line: '{ln}'")
        idx.append(int(float(parts[0])))
        val.append(float(parts[1]))
    if len(idx) != n:
        raise ValueError(f"Header says N={n} but found {len(idx)} samples")

    order = sorted(range(n), key=lambda i: idx[i])
    return Signal(os.path.basename(path), [idx[i] for i in order],
                  [val[i] for i in order], is_periodic)


def write_signal(sig: Signal, path: str):
    with open(path, "w") as f:
        f.write(f"0\n{sig.is_periodic}\n{len(sig)}\n")
        for i, v in zip(sig.indices, sig.samples):
            f.write(f"{i} {_fmt(v)}\n")


def _fmt(v):
    return str(int(v)) if float(v).is_integer() else repr(float(v))


# -------------------------------------------------------------- operations
def add_signals(signals, name="sum") -> Signal:
    """Add any number of signals. Missing samples count as 0."""
    if not signals:
        raise ValueError("Select at least one signal")
    lo = min(s.indices[0] for s in signals)
    hi = max(s.indices[-1] for s in signals)
    dicts = [s.as_dict() for s in signals]
    idx = list(range(lo, hi + 1))
    val = [sum(d.get(i, 0.0) for d in dicts) for i in idx]
    return Signal(name, idx, val)


def multiply_by_constant(sig: Signal, c: float, name=None) -> Signal:
    return Signal(name or f"{_fmt(c)}*{sig.name}", list(sig.indices),
                  [c * v for v in sig.samples], sig.is_periodic)


def subtract_signals(first: Signal, others, name="difference") -> Signal:
    """first - others[0] - others[1] ... (addition after multiplying by -1)."""
    negated = [multiply_by_constant(o, -1) for o in others]
    return add_signals([first] + negated, name)


def shift_signal(sig: Signal, k: int, name=None) -> Signal:
    """x(n+k): k>0 advances (moves left), k<0 delays (moves right)."""
    label = f"{sig.name}(n{'+' if k >= 0 else '-'}{abs(k)})"
    return Signal(name or label, [i - k for i in sig.indices],
                  list(sig.samples), sig.is_periodic)


def fold_signal(sig: Signal, name=None) -> Signal:
    """x(-n)"""
    pairs = sorted(((-i, v) for i, v in zip(sig.indices, sig.samples)))
    return Signal(name or f"{sig.name}(-n)", [p[0] for p in pairs],
                  [p[1] for p in pairs], sig.is_periodic)
