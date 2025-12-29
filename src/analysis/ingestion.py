"""Async data ingestion service for fetching trades into Polars LazyFrames."""

from datetime import datetime, timedelta, timezone

import polars as pl
from sqlalchemy import text

from src.config import settings
from src.db import get_session


class DataIngestionService:
    """
    Service for fetching high-frequency trading data from PostgreSQL.
    
    Converts raw database results into Polars LazyFrames for efficient
    quantitative analysis on large datasets.
    """

    @staticmethod
    async def fetch_recent_pumpfun_trades(
        minutes: int | None = None,
    ) -> pl.LazyFrame:
        """
        Fetch recent PumpFun trades into a Polars LazyFrame.
        
        Args:
            minutes: Lookback window in minutes. Defaults to settings.lookback_minutes.
            
        Returns:
            Polars LazyFrame with trade data, sorted by observed_at DESC.
        """
        if minutes is None:
            minutes = settings.lookback_minutes

        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        query = text("""
            SELECT 
                observed_at,
                slot,
                tx_signature,
                mint,
                trader,
                is_buy,
                sol_amount,
                token_amount,
                virtual_sol_reserves,
                virtual_token_reserves
            FROM pumpfun_trades
            WHERE observed_at >= :cutoff_time
            ORDER BY observed_at DESC
        """)

        async with get_session() as session:
            result = await session.execute(query, {"cutoff_time": cutoff_time})
            rows = result.fetchall()

        # Convert to Polars DataFrame, then LazyFrame for efficiency
        if not rows:
            # Return empty LazyFrame with correct schema
            return pl.LazyFrame(
                schema={
                    "observed_at": pl.Datetime("us", "UTC"),
                    "slot": pl.Int64,
                    "tx_signature": pl.Utf8,
                    "mint": pl.Utf8,
                    "trader": pl.Utf8,
                    "is_buy": pl.Boolean,
                    "sol_amount": pl.Float64,
                    "token_amount": pl.Float64,
                    "virtual_sol_reserves": pl.Float64,
                    "virtual_token_reserves": pl.Float64,
                }
            )

        # Convert rows to dict for Polars
        data = {
            "observed_at": [row[0] for row in rows],
            "slot": [row[1] for row in rows],
            "tx_signature": [row[2] for row in rows],
            "mint": [row[3] for row in rows],
            "trader": [row[4] for row in rows],
            "is_buy": [row[5] for row in rows],
            "sol_amount": [float(row[6]) for row in rows],
            "token_amount": [float(row[7]) for row in rows],
            "virtual_sol_reserves": [float(row[8]) for row in rows],
            "virtual_token_reserves": [float(row[9]) for row in rows],
        }

        df = pl.DataFrame(data)
        return df.lazy()

    @staticmethod
    async def fetch_recent_raydium_swaps(
        minutes: int | None = None,
    ) -> pl.LazyFrame:
        """
        Fetch recent Raydium swaps into a Polars LazyFrame.
        
        Args:
            minutes: Lookback window in minutes. Defaults to settings.lookback_minutes.
            
        Returns:
            Polars LazyFrame with swap data, sorted by observed_at DESC.
        """
        if minutes is None:
            minutes = settings.lookback_minutes

        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        query = text("""
            SELECT 
                observed_at,
                pool,
                amount_in,
                amount_out
            FROM raydium_swaps
            WHERE observed_at >= :cutoff_time
            ORDER BY observed_at DESC
        """)

        async with get_session() as session:
            result = await session.execute(query, {"cutoff_time": cutoff_time})
            rows = result.fetchall()

        if not rows:
            return pl.LazyFrame(
                schema={
                    "observed_at": pl.Datetime("us", "UTC"),
                    "pool": pl.Utf8,
                    "amount_in": pl.Float64,
                    "amount_out": pl.Float64,
                }
            )

        data = {
            "observed_at": [row[0] for row in rows],
            "pool": [row[1] for row in rows],
            "amount_in": [float(row[2]) for row in rows],
            "amount_out": [float(row[3]) for row in rows],
        }

        df = pl.DataFrame(data)
        return df.lazy()

    @staticmethod
    async def get_unique_mints(minutes: int | None = None) -> list[str]:
        """
        Get list of unique token mints from recent trades.
        
        Useful for iterating over tokens to analyze.
        """
        if minutes is None:
            minutes = settings.lookback_minutes

        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        query = text("""
            SELECT DISTINCT mint
            FROM pumpfun_trades
            WHERE observed_at >= :cutoff_time
        """)

        async with get_session() as session:
            result = await session.execute(query, {"cutoff_time": cutoff_time})
            rows = result.fetchall()

        return [row[0] for row in rows]
