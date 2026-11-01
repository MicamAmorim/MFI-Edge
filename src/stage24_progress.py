from __future__ import annotations

"""Small dependency-free terminal progress display for long Stage-24 runs.

The progress bar is deliberately presentation-only: it never participates in
scientific selection, caching, seeds, thresholds, or checkpoints.
"""

from dataclasses import dataclass
import shutil
import sys
import time


def _clock(seconds: float | None) -> str:
    if seconds is None or seconds < 0 or seconds == float("inf"):
        return "--:--:--"
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


@dataclass(frozen=True)
class PhaseRange:
    start: float
    end: float
    label: str


class TerminalProgress:
    """Render one continuously updated global progress line.

    ``phases`` maps a phase name to a [0, 1] range in the global campaign.
    In interactive terminals the same line is rewritten with ``\r``.  When
    stdout is redirected, compact newline updates are emitted only at phase
    changes or ~5 percentage-point increments, so log files stay readable.
    """

    def __init__(self, phases: dict[str, tuple[float, float, str]] | None = None):
        raw = phases or {
            "maps": (0.00, 0.20, "descritores"),
            "cv": (0.20, 0.80, "nested CV"),
            "freeze": (0.80, 0.90, "freeze"),
            "anatomy": (0.90, 0.95, "residuos"),
            "official": (0.95, 1.00, "avaliacao oficial"),
        }
        self.phases = {k: PhaseRange(*v) for k, v in raw.items()}
        self.started = time.monotonic()
        self.is_tty = bool(getattr(sys.stdout, "isatty", lambda: False)())
        self._last_len = 0
        self._last_emit_fraction = -1.0
        self._last_phase: str | None = None
        self._stage: str | None = None
        self._current = 0
        self._total = 1
        self._detail = ""
        self._closed = False

    def _global_fraction(self, stage: str, current: int | float, total: int | float) -> float:
        phase = self.phases[stage]
        local = 0.0 if total <= 0 else min(1.0, max(0.0, float(current) / float(total)))
        return phase.start + (phase.end - phase.start) * local

    def _render(self, stage: str, current: int | float, total: int | float, detail: str) -> None:
        if self._closed:
            return
        fraction = self._global_fraction(stage, current, total)
        elapsed = max(0.0, time.monotonic() - self.started)
        eta = None if fraction <= 1e-9 else elapsed * (1.0 - fraction) / fraction
        cols = shutil.get_terminal_size((130, 24)).columns
        bar_width = max(12, min(34, cols - 92))
        filled = min(bar_width, int(round(bar_width * fraction)))
        bar = "█" * filled + "░" * (bar_width - filled)
        phase = self.phases[stage]
        unit = f"{int(current)}/{int(total)}" if total > 0 else "-"
        suffix = f" | {detail}" if detail else ""
        line = (
            f"[{bar}] {fraction * 100:5.1f}% | {phase.label} {unit}{suffix}"
            f" | elapsed {_clock(elapsed)} | ETA {_clock(eta)}"
        )

        if self.is_tty:
            padded = line.ljust(self._last_len)
            sys.stdout.write("\r" + padded)
            sys.stdout.flush()
            self._last_len = max(self._last_len, len(line))
        else:
            phase_changed = stage != self._last_phase
            advanced = fraction - self._last_emit_fraction >= 0.05
            if phase_changed or advanced or fraction >= 1.0:
                print(line, flush=True)
                self._last_emit_fraction = fraction
        self._last_phase = stage

    def update(self, stage: str, current: int | float, total: int | float, detail: str = "") -> None:
        if stage not in self.phases:
            raise KeyError(f"unknown progress phase: {stage}")
        self._stage, self._current, self._total, self._detail = stage, current, total, detail
        self._render(stage, current, total, detail)

    def detail(self, detail: str) -> None:
        """Refresh the current line without changing its numerical progress."""
        if self._stage is not None:
            self._detail = detail
            self._render(self._stage, self._current, self._total, detail)

    def newline(self) -> None:
        """End the dynamic line before an external command prints normal output."""
        if self.is_tty and self._last_len:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self._last_len = 0

    def finish(self, detail: str = "concluido") -> None:
        if self._closed:
            return
        # Use the final registered phase so the global bar reaches exactly 100%.
        stage = "official" if "official" in self.phases else list(self.phases)[-1]
        self._render(stage, 1, 1, detail)
        self.newline()
        self._closed = True

    def stop(self, detail: str = "interrompido com checkpoint seguro") -> None:
        if self._closed:
            return
        self.detail(detail)
        self.newline()
        self._closed = True
