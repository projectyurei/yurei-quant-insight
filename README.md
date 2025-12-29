# Yurei Quant Insight

High-performance Python intelligence layer for quantitative DeFi analysis on Solana.

## Overview

This module connects to the PostgreSQL database populated by `yurei-geyser-client` and performs real-time quantitative analysis to detect "Alpha" signals:

- **Volume Spikes**: >300% volume increase detection
- **Whale Watch**: Large accumulation detection in token launch windows

## Tech Stack

- **Polars**: High-performance DataFrame operations
- **SQLAlchemy Async**: Async PostgreSQL access with `asyncpg`
- **Pydantic**: Configuration and data validation
- **Rich**: Beautiful console output

## Quick Start

```bash
# Install dependencies
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# Run analysis
python main.py
```

## Project Structure

```
yurei-quant-insight/
├── main.py                 # Entry point
├── pyproject.toml          # Dependencies
├── .env.example            # Configuration template
└── src/
    ├── config/             # Pydantic settings
    ├── db/                 # SQLAlchemy models & engine
    ├── models/             # Signal output models
    ├── analysis/           # Ingestion & metrics
    └── output/             # Rich console logger
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `ANALYSIS_INTERVAL_SECONDS` | Loop interval | 30 |
| `VOLUME_SPIKE_THRESHOLD` | % increase for spike | 300 |
| `WHALE_SOL_THRESHOLD` | SOL threshold for whale | 10.0 |

## License

MIT - Yurei AI
