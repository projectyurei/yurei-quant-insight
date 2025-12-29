"""Quantitative metrics for alpha signal detection."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import polars as pl

from src.config import settings
from src.models import SignalSeverity, VolumeSignal, WhaleSignal


@dataclass
class VolumeMetrics:
    """Volume spike detection metrics."""

    @staticmethod
    def detect_volume_spike(
        trades_lf: pl.LazyFrame,
        mint: str,
        recent_minutes: int = 5,
        baseline_minutes: int = 15,
        threshold_percent: float | None = None,
    ) -> VolumeSignal | None:
        """
        Detect if a token has a volume spike.
        
        A spike is detected when the volume in the recent window exceeds
        the baseline window by more than the threshold percentage.
        
        Args:
            trades_lf: LazyFrame of PumpFun trades
            mint: Token mint address to analyze
            recent_minutes: Recent window in minutes (default: 5)
            baseline_minutes: Baseline window in minutes (default: 15)
            threshold_percent: Spike threshold percentage (default from settings)
            
        Returns:
            VolumeSignal if spike detected, None otherwise
        """
        if threshold_percent is None:
            threshold_percent = settings.volume_spike_threshold

        now = datetime.now(timezone.utc)
        recent_cutoff = now - timedelta(minutes=recent_minutes)
        baseline_cutoff = now - timedelta(minutes=recent_minutes + baseline_minutes)

        # Filter for specific mint
        mint_trades = trades_lf.filter(pl.col("mint") == mint)

        # Recent window trades (last N minutes)
        recent_trades = mint_trades.filter(pl.col("observed_at") >= recent_cutoff)

        # Baseline window trades (previous M minutes, before recent window)
        baseline_trades = mint_trades.filter(
            (pl.col("observed_at") >= baseline_cutoff) & 
            (pl.col("observed_at") < recent_cutoff)
        )

        # Calculate volumes (only buys for buy pressure analysis)
        recent_stats = (
            recent_trades
            .filter(pl.col("is_buy") == True)  # noqa: E712
            .select([
                pl.col("sol_amount").sum().alias("volume_sol"),
                pl.len().alias("trade_count"),
            ])
            .collect()
        )

        baseline_stats = (
            baseline_trades
            .filter(pl.col("is_buy") == True)  # noqa: E712
            .select([
                pl.col("sol_amount").sum().alias("volume_sol"),
                pl.len().alias("trade_count"),
            ])
            .collect()
        )

        recent_volume = recent_stats["volume_sol"][0] or 0.0
        recent_count = recent_stats["trade_count"][0] or 0
        baseline_volume = baseline_stats["volume_sol"][0] or 0.0
        baseline_count = baseline_stats["trade_count"][0] or 0

        # Avoid division by zero
        if baseline_volume == 0:
            if recent_volume > 0:
                # New token or first activity
                spike_percentage = float("inf")
            else:
                return None
        else:
            spike_percentage = ((recent_volume - baseline_volume) / baseline_volume) * 100

        # Check if spike exceeds threshold
        if spike_percentage >= threshold_percent:
            # Determine severity
            if spike_percentage >= 1000:
                severity = SignalSeverity.CRITICAL
            elif spike_percentage >= 500:
                severity = SignalSeverity.HIGH
            elif spike_percentage >= 300:
                severity = SignalSeverity.MEDIUM
            else:
                severity = SignalSeverity.LOW

            return VolumeSignal(
                severity=severity,
                mint=mint,
                description=(
                    f"Volume spike detected: {spike_percentage:.1f}% increase "
                    f"in last {recent_minutes} minutes"
                ),
                recent_volume_sol=Decimal(str(recent_volume)),
                baseline_volume_sol=Decimal(str(baseline_volume)),
                spike_percentage=spike_percentage,
                trade_count_recent=recent_count,
                trade_count_baseline=baseline_count,
            )

        return None


@dataclass
class WhaleMetrics:
    """Whale accumulation detection metrics."""

    @staticmethod
    def detect_whale_accumulation(
        trades_lf: pl.LazyFrame,
        mint: str,
        first_minutes: int | None = None,
        sol_threshold: float | None = None,
    ) -> list[WhaleSignal]:
        """
        Detect whale accumulation in the first minutes of a token launch.
        
        Identifies traders who have accumulated more than the threshold
        amount of SOL worth of tokens in the early trading period.
        
        Args:
            trades_lf: LazyFrame of PumpFun trades
            mint: Token mint address to analyze
            first_minutes: Window from token launch (default from settings)
            sol_threshold: SOL accumulation threshold (default from settings)
            
        Returns:
            List of WhaleSignal for each whale detected
        """
        if first_minutes is None:
            first_minutes = settings.whale_first_minutes
        if sol_threshold is None:
            sol_threshold = settings.whale_sol_threshold

        # Filter for specific mint
        mint_trades = (
            trades_lf
            .filter(pl.col("mint") == mint)
            .collect()
        )

        if mint_trades.height == 0:
            return []

        # Find first trade time (token launch proxy)
        first_trade_time = mint_trades["observed_at"].min()
        if first_trade_time is None:
            return []

        window_end = first_trade_time + timedelta(minutes=first_minutes)

        # Filter to first N minutes
        early_trades = mint_trades.filter(
            pl.col("observed_at") <= window_end
        )

        if early_trades.height == 0:
            return []

        # Aggregate by trader (only buys)
        whale_candidates = (
            early_trades
            .filter(pl.col("is_buy") == True)  # noqa: E712
            .group_by("trader")
            .agg([
                pl.col("sol_amount").sum().alias("total_sol"),
                pl.col("token_amount").sum().alias("total_tokens"),
                pl.len().alias("trade_count"),
                pl.col("observed_at").min().alias("first_trade"),
                pl.col("observed_at").max().alias("last_trade"),
                pl.col("virtual_sol_reserves").last().alias("last_sol_reserves"),
                pl.col("virtual_token_reserves").last().alias("last_token_reserves"),
            ])
            .filter(pl.col("total_sol") >= sol_threshold)
        )

        signals: list[WhaleSignal] = []

        for row in whale_candidates.iter_rows(named=True):
            # Calculate market cap estimate from virtual reserves
            market_cap = None
            if row["last_sol_reserves"] and row["last_token_reserves"]:
                # Simplified market cap: virtual_sol_reserves represents bonding curve liquidity
                market_cap = Decimal(str(row["last_sol_reserves"]))

            # Determine severity based on accumulation size
            total_sol = row["total_sol"]
            if total_sol >= 50:
                severity = SignalSeverity.CRITICAL
            elif total_sol >= 25:
                severity = SignalSeverity.HIGH
            elif total_sol >= 15:
                severity = SignalSeverity.MEDIUM
            else:
                severity = SignalSeverity.LOW

            signal = WhaleSignal(
                severity=severity,
                mint=mint,
                description=(
                    f"Whale detected: {row['trader'][:8]}... accumulated "
                    f"{total_sol:.2f} SOL in first {first_minutes} minutes"
                ),
                trader_address=row["trader"],
                total_sol_accumulated=Decimal(str(total_sol)),
                total_tokens_accumulated=Decimal(str(row["total_tokens"])),
                trade_count=row["trade_count"],
                first_trade_at=row["first_trade"],
                last_trade_at=row["last_trade"],
                estimated_market_cap_sol=market_cap,
            )
            signals.append(signal)

        return signals
