"""Main analysis orchestrator coordinating ingestion and metrics."""

from src.models import AlphaSignal
from src.output import SignalConsole

from .ingestion import DataIngestionService
from .metrics import VolumeMetrics, WhaleMetrics


class AlphaAnalyzer:
    """
    Main analysis orchestrator for detecting alpha signals.
    
    Coordinates data ingestion and metric calculation, then
    outputs detected signals via the console logger.
    """

    def __init__(self, console: SignalConsole | None = None) -> None:
        """
        Initialize the analyzer.
        
        Args:
            console: Signal console for output. Creates default if None.
        """
        self.console = console or SignalConsole()
        self.ingestion = DataIngestionService()

    async def run_analysis_cycle(self) -> list[AlphaSignal]:
        """
        Run a single analysis cycle.
        
        Fetches recent data and runs all metrics against each active token.
        
        Returns:
            List of all detected alpha signals
        """
        signals: list[AlphaSignal] = []

        # Fetch fresh data
        trades_lf = await self.ingestion.fetch_recent_pumpfun_trades()

        # Get unique mints to analyze
        mints = await self.ingestion.get_unique_mints()

        if not mints:
            self.console.log_info("No active tokens in lookback window")
            return signals

        self.console.log_info(f"Analyzing {len(mints)} active tokens...")

        for mint in mints:
            # Volume spike detection
            volume_signal = VolumeMetrics.detect_volume_spike(trades_lf, mint)
            if volume_signal:
                signals.append(volume_signal)
                self.console.log_signal(volume_signal)

            # Whale detection
            whale_signals = WhaleMetrics.detect_whale_accumulation(trades_lf, mint)
            for whale_signal in whale_signals:
                signals.append(whale_signal)
                self.console.log_signal(whale_signal)

        if signals:
            self.console.log_summary(len(signals))
        else:
            self.console.log_info("No alpha signals detected in this cycle")

        return signals

    async def health_check(self) -> bool:
        """
        Check system health by testing database connection.
        
        Returns:
            True if all systems operational
        """
        from src.db.engine import check_connection

        db_ok = await check_connection()
        if not db_ok:
            self.console.log_error("Database connection failed")
            return False

        self.console.log_info("System health check passed")
        return True
