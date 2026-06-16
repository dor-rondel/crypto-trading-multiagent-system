# GEMINI.md

## Project Context

This repository contains an event-driven, agentic trading simulation platform.

The system trades exclusively on testnets while using real market data to generate signals.
The primary LLM provider is **Groq** for high-speed inference.
**LangSmith** is used for workflow observability and tracing.
The workflow is managed via **LangGraph**.

Supported chains:

- Solana Devnet (`solana-py`)
- Ethereum Sepolia (`AgentKit/CDP`)
- Avalanche Fuji (`AgentKit/CDP`)

---

# Architectural Constraints

## Multi-Agent Architecture (v2.0)

The system follows a strict separation between data acquisition, specialized analysis, and final decision-making.

### Modular Workflows

- **Architecture:** Decouple reasoning from execution using LangGraph. Maintain separate files for nodes, state, and graph definitions.
- **Fan-out/Fan-in:** Utilize parallel specialized subagents (Analysts) to provide context to a central Aggregator Agent.
- **Prompts:** All LLM prompts must reside in `src/prompts/` and must be imported. Do not hardcode prompts in agent classes.
- **Models:** Use Pydantic models for all inter-node communication (e.g., `TradePlan`, `TradeAction`, and Analyst Reports).
- **Validation:** Every trade plan must pass through a deterministic `RiskValidator` before execution.

### Agents vs. Tools vs. Services

- **Agents (`src/agents/`):** Intelligence layer. Contains the Aggregator and specialized analysts. Analysts must only reason about data, not fetch it.
- **Tools (`src/tools/`):** Data acquisition layer. Contains fetchers for Market Data, Gas Prices, News, etc.
- **Services (`src/services/`):** Core infrastructure layer. Contains Wallet management, Risk validation, and Monitoring.

### Executors Execute Plans

Executors perform blockchain operations.

- **EVM Chains:** Use `AgentKit` and the `Coinbase CDP SDK` for swaps and wallet management. `web3.py` may be used for low-level deterministic checks.
- **Solana:** Use `solana-py` for transaction construction and signing.
- Executors must never generate strategy decisions.

#### Technical Rationale: Solana Memo Program
On Solana, the system uses the **Memo Program** (`MemoSq9gHqT9VkU4beuy66Gf364aJ6Eic52pD34j3K`) to record trade intents (e.g., `"BUY 1 SOL with 145 USDC"`) directly on-chain.

#### Technical Rationale: Wrapped Tokens (WETH/WAVAX)
Protocols like Uniswap V3 require ERC-20 compliance. The system interacts with **WETH** and **WAVAX** contracts to enable seamless swaps with USDC.

---

## Architectural Mandates

### 1. Singleton Wallet Management
- **Rule:** The `WalletManager` MUST be a Singleton. Access the instance via `WalletManager()`.

### 2. SDK Thread Isolation
- **Rule:** All calls to loop-managing SDKs (specifically **Coinbase AgentKit/CDP**) MUST be wrapped in `asyncio.to_thread`.

### 3. Stateless Execution Node
- **Rule:** The `executor_node` MUST exit immediately after submitting a transaction and recording it as `PENDING` in SQLite.

### 4. Database Safety & Economic Accountability
- **Rule:** All SQL queries MUST be stored in `src/persistence/queries.py` and MUST use parameterized placeholders (`?`).
- **Mandate:** Every trade MUST record `execution_price` and `cost_basis`.

### 5. Multi-Provider Market Context
- **Rule:** Market data aggregation SHOULD utilize multiple providers (CoinGecko + Binance) to ensure resilience.
- **Mandate:** The agent MUST be provided with historical OHLCV data (Trends) and current position PnL context during the planning phase.

### 6. Flaky RPC Resilience
- **Rule:** Critical blockchain operations (balances, status checks) MUST use the `@retry_async` decorator from `src/utils/retry.py`.

---

## Engineering Standards

- **Python Version:** 3.12+ (managed via `uv`).
- **Pylint Standard:** Code MUST maintain a **10.00/10** rating. 
- **Type Safety:** All public methods MUST have Mypy-compliant type annotations.
- **Logging:** Use Python's standard `logging.getLogger(__name__)`. 
- **Mandatory Quality Checks:** Before finalizing any task, run `make check`.
