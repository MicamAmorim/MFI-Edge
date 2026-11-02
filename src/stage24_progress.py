from __future__ import annotations

"""Small dependency-free terminal progress display for long Stage-24 runs.

The progress bar is deliberately presentation-only: it never participates in
scientific selection, caching, seeds, thresholds, or checkpoints.
"""

from dataclasses import dataclass
import os
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


def _interactive_stdout() -> bool:
    """Best-effort interactive-console detection, including Windows Terminal.

    Some Windows/Python launch combinations report ``isatty() == False`` even
    while stdout is attached to an interactive console.  Prefer the standard
    check, then use the Win32 console handle as a fallback.  Environment hints
    are only a last resort and are intentionally limited to known terminals.
    """
    try:
        if sys.stdout.isatty():
            return True
    except Exception:
        pass

    if os.name == "nt":
        try:
            import ctypes
            import msvcrt

            handle = msvcrt.get_osfhandle(sys.stdout.fileno())
            mode = ctypes.c_ulong()
            if ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                return True
        except Exception:
            pass

        if os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM") in {
            "Windows_Terminal",
            "vscode",
        }:
            return True
    return False


def _truncate(text: str, width: int) -> str:
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    return text[: width - 1] + "…"


@dataclass(frozen=True)
class PhaseRange:
    start: float
    end: float
    label: str


class TerminalProgress:
    """Render one continuously updated global progress line.

    ``phases`` maps a phase name to a [0, 1] range in the global campaign.
    Interactive terminals rewrite the same physical line with ``\r``.  The
    rendered line is always constrained to the current terminal width so it
    cannot wrap and leave stale progress rows behind.  Redirected stdout keeps
    compact newline updates at phase changes or ~5 percentage-point steps.
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
        self.is_tty = _interactive_stdout()
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

    def _format_line(
        self,
        stage: str,
        current: int | float,
        total: int | float,
        detail: str,
        fraction: float,
        elapsed: float,
        eta: float | None,
    ) -> str:
        cols = max(48, shutil.get_terminal_size((120, 24)).columns)
        # Leave one spare column: writing exactly to the final terminal column
        # can trigger an automatic wrap on Windows consoles.
        target = max(47, cols - 1)
        phase = self.phases[stage]
        unit = f"{int(current)}/{int(total)}" if total > 0 else "-"

        # Keep timing compact so the scientific detail remains visible even in
        # narrower PowerShell/Windows Terminal windows.
        timing = f" | E {_clock(elapsed)} | ETA {_clock(eta)}"
        status = f"{phase.label} {unit}"

        # Choose the bar only after reserving room for status + timing.  This
        # prevents wrapping, which otherwise defeats carriage-return updates.
        fixed_without_bar = len("[] 100.0% | ") + len(status) + len(timing)
        bar_width = max(8, min(28, target - fixed_without_bar - 16))
        filled = min(bar_width, int(round(bar_width * fraction)))
        bar = "█" * filled + "░" * (bar_width - filled)
        prefix = f"[{bar}] {fraction * 100:5.1f}% | {status}"

        available_detail = target - len(prefix) - len(timing) - 3
        if detail and available_detail >= 4:
            middle = " | " + _truncate(detail, available_detail)
        else:
            middle = ""
        line = prefix + middle + timing
        return line[:target]

    def _render(self, stage: str, current: int | float, total: int | float, detail: str) -> None:
        if self._closed:
            return
        fraction = self._global_fraction(stage, current, total)
        elapsed = max(0.0, time.monotonic() - self.started)
        eta = None if fraction <= 1e-9 else elapsed * (1.0 - fraction) / fraction
        line = self._format_line(stage, current, total, detail, fraction, elapsed, eta)

        if self.is_tty:
            # A line constrained to terminal width plus carriage return is the
            # most compatible way to update in place in PowerShell, Windows
            # Terminal, cmd.exe, and ANSI-capable POSIX terminals.
            clear_to = max(self._last_len, len(line))
            padded = line.ljust(clear_to)
            sys.stdout.write("\r" + padded)
            sys.stdout.flush()
            self._last_len = len(line)
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
