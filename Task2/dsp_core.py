"""Core DSP logic (no GUI code here) - reused by all future tasks."""
from __future__ import annotations
import math
from dataclasses import dataclass, field


@dataclass
class Signal:
    name: str
    indices: list = field(default_factory=list)
    samples: list = field(default_factory=list)
    params: dict = field(default_factory=dict)   # kind, A, theta, F, Fs

    def __len__(self):
        return len(self.indices)


def check_sampling(F: float, Fs: float):
    """Sampling theorem: Fs must be greater than 2F."""
    if F <= 0:
        raise ValueError("Analog frequency must be greater than 0")
    if Fs <= 2 * F:
        raise ValueError(f"Sampling theorem violated: Fs must be > 2F = {2 * F:g} Hz "
                         f"(you entered Fs = {Fs:g} Hz)")


def generate_signal(kind: str, A: float, theta: float, F: float, Fs: float,
                    periods: int = 4) -> Signal:
    """x(n) = A*sin(2*pi*(F/Fs)*n + theta)   or   A*cos(...)   for n = 0..N-1.

    kind is "sine" or "cosine", theta is in radians, `periods` analog periods are generated.
    """
    if kind not in ("sine", "cosine"):
        raise ValueError("kind must be 'sine' or 'cosine'")
    check_sampling(F, Fs)
    fn = math.sin if kind == "sine" else math.cos
    n_samples = int(math.ceil(periods * Fs / F))
    idx = list(range(n_samples))
    val = [A * fn(2 * math.pi * F * n / Fs + theta) for n in idx]
    name = f"{'sin' if kind == 'sine' else 'cos'} A={A:g} F={F:g} Fs={Fs:g}"
    return Signal(name, idx, val, dict(kind=kind, A=A, theta=theta, F=F, Fs=Fs))


def analog_curve(sig: Signal, points_per_period: int = 100):
    """Continuous x(t) of a generated signal over the same time span. Returns (t, x)."""
    p = sig.params
    fn = math.sin if p["kind"] == "sine" else math.cos
    t_end = (sig.indices[-1] + 1) / p["Fs"]
    n_points = max(200, int(t_end * p["F"] * points_per_period))
    t = [t_end * i / (n_points - 1) for i in range(n_points)]
    x = [p["A"] * fn(2 * math.pi * p["F"] * ti + p["theta"]) for ti in t]
    return t, x
