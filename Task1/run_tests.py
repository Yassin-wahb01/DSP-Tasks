"""Checks the operations against the expected files provided with the task."""
import os
from dsp_core import (read_signal, add_signals, subtract_signals,
                      multiply_by_constant, shift_signal, fold_signal)

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _compare(label, result, expected_file):
    exp = read_signal(os.path.join(DATA, expected_file))
    if len(result) != len(exp):
        return f"{label}: FAILED (different length)"
    if list(result.indices) != list(exp.indices):
        return f"{label}: FAILED (different indices)"
    if any(abs(a - b) >= 0.01 for a, b in zip(result.samples, exp.samples)):
        return f"{label}: FAILED (different values)"
    return f"{label}: passed"


def run_all():
    s1 = read_signal(os.path.join(DATA, "Signal1.txt"))
    s2 = read_signal(os.path.join(DATA, "Signal2.txt"))
    return [
        _compare("Addition", add_signals([s1, s2]), "add.txt"),
        _compare("Subtraction", subtract_signals(s1, [s2]), "subtract.txt"),
        _compare("Multiply by 5", multiply_by_constant(s1, 5), "mul5.txt"),
        _compare("Advance by 3", shift_signal(s1, 3), "advance3.txt"),
        _compare("Delay by 3", shift_signal(s1, -3), "delay3.txt"),
        _compare("Folding", fold_signal(s1), "folding.txt"),
    ]


if __name__ == "__main__":
    print("\n".join(run_all()))
