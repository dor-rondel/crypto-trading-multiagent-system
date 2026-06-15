# Agentic Testnet Trading System

## Overview

This project is an event-driven, agentic cryptocurrency trading simulation platform built for test networks.

The system executes simulated trading strategies against:

- **Solana Devnet** (via `solana-py`)
- **Ethereum Sepolia** (via `AgentKit/CDP`)
- **Avalanche Fuji** (via `AgentKit/CDP`)

Real market data is used to generate trading signals, while all trade execution occurs on testnets using a **three-wallet USDC strategy** to avoid risking real capital.

---

## Goals

- Evaluate AI-generated trading strategies safely
- Simulate multi-chain portfolio management
- Test autonomous trading workflows
- Support long-running blockchain operations
- Maintain reproducibility and auditability

---

## Core Technologies

### AI / Workflow

- LangGraph
- LangChain
- **Groq** (via LangChain-Groq)
- **LangSmith** (for observability)
- **Coinbase AgentKit** (for EVM execution)

### Blockchain

- **Solana Python SDK** (`solana-py`)
- **Coinbase CDP SDK**
- **web3.py** (for deterministic validations)

### Infrastructure

- Python 3.12+
- **SQLite (aiosqlite)** for persistent trade tracking

---

## Architecture

### Modular LangGraph Workflow
The system uses a decoupled LangGraph architecture to separate reasoning from execution:

- **Planner Agent (`src/agents/planner.py`):** Uses Groq (Llama 3) to analyze market data and portfolio state, generating a structured `TradePlan`.
- **Risk Validator (`src/services/risk_validator.py`):** A deterministic node that enforces balance constraints, maximum trade limits, and slippage guardrails.
- **Trade Executor (`src/workflows/nodes.py`):** Dispatches validated actions to chain-specific wallet adapters and records them in the database.

### Background Services
- **Market Watcher (`src/services/market_watcher.py`):** Aggregates price snapshots and triggers the agent loop.
- **Transaction Monitor (`src/services/transaction_monitor.py`):** A parallel service that polls the blockchain to update the status of `PENDING` trades in SQLite.

---

## Design Principles

### Stateless Non-Blocking Execution
To handle flaky testnets, the agent loop completes immediately after submitting a transaction. The `TransactionMonitor` handles the asynchronous confirmation, allowing the agent to stay responsive to new signals.

### Singleton Wallet Management
The `WalletManager` is a singleton ensuring that wallet keys and initialized providers are shared across the application, preventing redundant initialization and race conditions.

### SDK Thread Isolation
Calls to loop-heavy SDKs (like Coinbase AgentKit) are offloaded to separate threads using `asyncio.to_thread` to prevent event loop conflicts.

### Centralized Persistence
All SQL queries are centralized in `src/persistence/queries.py` and use parameterized queries to prevent injection from LLM-generated rationale strings.

---

## Development

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- `libffi-dev` (required for `cffi` build)

### Install

```bash
# Install dependencies and setup virtual environment
make install
```

### Visualization
Generate a visual map of the trading graph:
```bash
make graph
```

### Run Full System
```bash
uv run src/workflows/main.py
```

### Run Quality Checks
```bash
# Formatter, Ruff, Pylint (10/10), Mypy, and Pytest
make check
```

---

## Future Roadmap & Backlog

### Roadmap
- **Phase 1: Foundation** (Completed)
- **Phase 2: Agentic Trading** (Completed)
- **Phase 3: Real Execution & Persistence** (Completed)
- **Phase 4: Advanced Features** (Next)

### Backlog (v2)
- **Stateful Resume:** Utilize LangGraph checkpointers to interrupt and resume specific workflow threads upon transaction confirmation.
- **Position Cost-Basis Tracking:** Extend SQLite to track realized/unrealized PnL based on cost-basis stored in the DB.
- **Market Data Resilience:** Implement a Binance API fallback in the `MarketWatcher`.
- **RPC Connectivity:** Automatic RPC endpoint fallbacks for chain connectivity.
- **Backtesting & Simulation:** Develop an engine to evaluate strategies against historical data.
