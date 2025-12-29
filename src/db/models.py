"""SQLAlchemy ORM models matching the existing database schema."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class PumpfunTrade(Base):
    """
    ORM model for pumpfun_trades table.
    
    Created by yurei-geyser-client for PumpFun DEX trades.
    """

    __tablename__ = "pumpfun_trades"

    # Primary key - using composite of tx_signature and slot for uniqueness
    tx_signature: Mapped[str] = mapped_column(Text, primary_key=True)
    slot: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Timestamp
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False,
        index=True,  # Critical for timeseries queries
    )

    # Token and trader identifiers
    mint: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    trader: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    # Trade direction
    is_buy: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Amounts
    sol_amount: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    token_amount: Mapped[Decimal] = mapped_column(Numeric, nullable=False)

    # Virtual reserves for price/market cap calculation
    virtual_sol_reserves: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    virtual_token_reserves: Mapped[Decimal] = mapped_column(Numeric, nullable=False)

    def __repr__(self) -> str:
        direction = "BUY" if self.is_buy else "SELL"
        return (
            f"<PumpfunTrade {direction} {self.sol_amount} SOL "
            f"for {self.token_amount} tokens of {self.mint[:8]}...>"
        )


class RaydiumSwap(Base):
    """
    ORM model for raydium_swaps table.
    
    Created by yurei-geyser-client for Raydium DEX swaps.
    """

    __tablename__ = "raydium_swaps"

    # Composite primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Timestamp
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Pool identifier
    pool: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    # Swap amounts
    amount_in: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    amount_out: Mapped[Decimal] = mapped_column(Numeric, nullable=False)

    def __repr__(self) -> str:
        return f"<RaydiumSwap {self.amount_in} -> {self.amount_out} on {self.pool[:8]}...>"
