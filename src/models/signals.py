"""Pydantic models for Alpha signal output."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class SignalSeverity(str, Enum):
    """Severity levels for alpha signals."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlphaSignal(BaseModel):
    """Base model for all alpha signals."""

    signal_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: SignalSeverity
    mint: str
    description: str

    def to_log_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "signal_type": self.signal_type,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "mint": self.mint,
            "description": self.description,
        }


class VolumeSignal(AlphaSignal):
    """Signal for volume spike detection."""

    signal_type: Literal["VOLUME_SPIKE"] = "VOLUME_SPIKE"

    # Volume metrics
    recent_volume_sol: Decimal = Field(description="Volume in last 5 minutes (SOL)")
    baseline_volume_sol: Decimal = Field(description="Volume in previous 15 minutes (SOL)")
    spike_percentage: float = Field(description="Percentage increase")
    trade_count_recent: int = Field(description="Number of trades in recent window")
    trade_count_baseline: int = Field(description="Number of trades in baseline window")

    def to_log_dict(self) -> dict:
        """Extended log dict with volume metrics."""
        base = super().to_log_dict()
        base.update({
            "recent_volume_sol": str(self.recent_volume_sol),
            "baseline_volume_sol": str(self.baseline_volume_sol),
            "spike_percentage": round(self.spike_percentage, 2),
            "trade_count_recent": self.trade_count_recent,
            "trade_count_baseline": self.trade_count_baseline,
        })
        return base


class WhaleSignal(AlphaSignal):
    """Signal for whale accumulation detection."""

    signal_type: Literal["WHALE_WATCH"] = "WHALE_WATCH"

    # Whale metrics
    trader_address: str = Field(description="Whale trader address")
    total_sol_accumulated: Decimal = Field(description="Total SOL spent")
    total_tokens_accumulated: Decimal = Field(description="Total tokens acquired")
    trade_count: int = Field(description="Number of trades by this whale")
    first_trade_at: datetime = Field(description="First trade timestamp")
    last_trade_at: datetime = Field(description="Last trade timestamp")
    estimated_market_cap_sol: Decimal | None = Field(
        default=None,
        description="Estimated market cap at time of detection",
    )

    def to_log_dict(self) -> dict:
        """Extended log dict with whale metrics."""
        base = super().to_log_dict()
        base.update({
            "trader_address": self.trader_address,
            "total_sol_accumulated": str(self.total_sol_accumulated),
            "total_tokens_accumulated": str(self.total_tokens_accumulated),
            "trade_count": self.trade_count,
            "first_trade_at": self.first_trade_at.isoformat(),
            "last_trade_at": self.last_trade_at.isoformat(),
            "estimated_market_cap_sol": (
                str(self.estimated_market_cap_sol) 
                if self.estimated_market_cap_sol else None
            ),
        })
        return base
