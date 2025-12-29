"""
Yurei Quant Insight - Main Entry Point

High-performance DeFi quantitative analysis layer for detecting alpha signals
from PumpFun trades and Raydium swaps streamed by yurei-geyser-client.

Usage:
    python main.py
    
Configuration:
    Copy .env.example to .env and configure your PostgreSQL connection.
"""

import asyncio
import signal
import sys
from typing import NoReturn

from src import __version__
from src.analysis import AlphaAnalyzer
from src.config import settings
from src.output import SignalConsole


class QuantInsightRunner:
    """Main application runner with graceful shutdown support."""

    def __init__(self) -> None:
        self.console = SignalConsole()
        self.analyzer = AlphaAnalyzer(self.console)
        self._shutdown_event = asyncio.Event()

    def _handle_shutdown(self, signum: int, frame: object) -> None:
        """Signal handler for graceful shutdown."""
        self.console.log_info(f"Received signal {signum}, initiating shutdown...")
        self._shutdown_event.set()

    async def run(self) -> NoReturn:
        """
        Main analysis loop.
        
        Runs analysis cycles at the configured interval until shutdown.
        """
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        # Startup
        self.console.log_startup(__version__, settings.analysis_interval_seconds)

        # Health check
        self.console.log_info("Running system health check...")
        if not await self.analyzer.health_check():
            self.console.log_error("Health check failed, exiting")
            sys.exit(1)

        self.console.log_success("System ready, starting analysis loop")
        self.console.print()

        cycle_count = 0

        try:
            while not self._shutdown_event.is_set():
                cycle_count += 1
                self.console.log_info(f"Starting analysis cycle #{cycle_count}")

                try:
                    await self.analyzer.run_analysis_cycle()
                except Exception as e:
                    self.console.log_error(f"Analysis cycle failed: {e}")

                # Wait for next cycle or shutdown
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=settings.analysis_interval_seconds,
                    )
                except asyncio.TimeoutError:
                    # Normal timeout, continue to next cycle
                    pass

        finally:
            self.console.log_shutdown()


def main() -> None:
    """Application entry point."""
    runner = QuantInsightRunner()

    try:
        asyncio.run(runner.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
