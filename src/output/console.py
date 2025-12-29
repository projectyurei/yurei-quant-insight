"""Rich console logger for structured signal output."""

import json
from datetime import datetime, timezone

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.models import AlphaSignal, SignalSeverity


class SignalConsole:
    """
    Rich-based console logger for alpha signals.
    
    Provides structured JSON output with color-coded severity levels
    and professional formatting for monitoring.
    """

    SEVERITY_STYLES = {
        SignalSeverity.LOW: "dim white",
        SignalSeverity.MEDIUM: "yellow",
        SignalSeverity.HIGH: "bold orange1",
        SignalSeverity.CRITICAL: "bold red blink",
    }

    SEVERITY_ICONS = {
        SignalSeverity.LOW: "◎",
        SignalSeverity.MEDIUM: "◉",
        SignalSeverity.HIGH: "⚠",
        SignalSeverity.CRITICAL: "🚨",
    }

    def __init__(self) -> None:
        """Initialize the console logger."""
        self.console = Console()
        self._signal_count = 0

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def log_signal(self, signal: AlphaSignal) -> None:
        """
        Log an alpha signal with structured JSON output.
        
        Args:
            signal: The alpha signal to log
        """
        self._signal_count += 1

        style = self.SEVERITY_STYLES.get(signal.severity, "white")
        icon = self.SEVERITY_ICONS.get(signal.severity, "•")

        # Create header
        header = Text()
        header.append(f"{icon} ", style=style)
        header.append(f"[{signal.signal_type}] ", style="bold cyan")
        header.append(f"{signal.severity.value}", style=style)

        # Create JSON body
        signal_dict = signal.to_log_dict()
        json_str = json.dumps(signal_dict, indent=2)

        # Create panel
        panel = Panel(
            json_str,
            title=header,
            title_align="left",
            border_style=style,
            subtitle=f"mint: {signal.mint[:16]}...",
            subtitle_align="right",
        )

        self.console.print(panel)

    def log_info(self, message: str) -> None:
        """Log an informational message."""
        timestamp = self._get_timestamp()
        self.console.print(
            f"[dim]{timestamp}[/dim] [blue]ℹ[/blue] {message}"
        )

    def log_error(self, message: str) -> None:
        """Log an error message."""
        timestamp = self._get_timestamp()
        self.console.print(
            f"[dim]{timestamp}[/dim] [red]✗[/red] [bold red]{message}[/bold red]"
        )

    def log_success(self, message: str) -> None:
        """Log a success message."""
        timestamp = self._get_timestamp()
        self.console.print(
            f"[dim]{timestamp}[/dim] [green]✓[/green] {message}"
        )

    def log_summary(self, signal_count: int) -> None:
        """Log analysis cycle summary."""
        self.console.print()
        self.console.rule("[bold cyan]Analysis Cycle Complete[/bold cyan]")
        self.console.print(
            f"[bold]Signals Detected:[/bold] {signal_count}",
            justify="center",
        )
        self.console.print()

    def log_startup(self, version: str, interval: int) -> None:
        """Log startup banner."""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ▓██   ██▓ █    ██  ██▀███  ▓█████  ██▓                      ║
║    ▒██  ██▒ ██  ▓██▒▓██ ▒ ██▒▓█   ▀ ▓██▒                      ║
║     ▒██ ██░▓██  ▒██░▓██ ░▄█ ▒▒███   ▒██▒                      ║
║     ░ ▐██▓░▓▓█  ░██░▒██▀▀█▄  ▒▓█  ▄ ░██░                      ║
║     ░ ██▒▓░▒▒█████▓ ░██▓ ▒██▒░▒████▒░██░                      ║
║      ██▒▒▒ ░▒▓▒ ▒ ▒ ░ ▒▓ ░▒▓░░░ ▒░ ░░▓                        ║
║    ▓██ ░▒░ ░░▒░ ░ ░   ░▒ ░ ▒░ ░ ░  ░ ▒ ░                      ║
║    ▒ ▒ ░░   ░░░ ░ ░   ░░   ░    ░    ▒ ░                      ║
║    ░ ░        ░        ░        ░  ░ ░                        ║
║                                                               ║
║              Q U A N T   I N S I G H T                        ║
║         High-Frequency Alpha Signal Detection                 ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
        self.console.print(banner, style="cyan")
        self.console.print(f"[dim]Version:[/dim] {version}")
        self.console.print(f"[dim]Analysis Interval:[/dim] {interval}s")
        self.console.print()

    def log_shutdown(self) -> None:
        """Log shutdown message."""
        self.console.print()
        self.console.rule("[bold red]Shutting Down[/bold red]")
        self.console.print(
            f"[dim]Total signals detected this session:[/dim] {self._signal_count}"
        )
