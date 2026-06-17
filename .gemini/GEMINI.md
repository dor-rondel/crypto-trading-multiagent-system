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
- **Analysts:** `gas`, `news`, `trend`, `performance`, `liquidity`, `correlation`, `whale`, `volatility`.
- **Prompts:** All LLM prompts must reside in `src/prompts/` and must be imported. Do not hardcode prompts in agent classes.
- **Models:** Use Pydantic models for all inter-node communication (e.g., `TradePlan`, `TradeAction`, and Analyst Reports).
- **Validation:** Every trade plan must pass through a deterministic `RiskValidator` before execution.

### Agents vs. Tools vs. Services

- **Agents (`src/agents/`):** Intelligence layer. Contains the Aggregator and specialized analysts. Analysts must only reason about data, not fetch it.
- **Tools (`src/tools/`):** Data acquisition layer. Contains fetchers for Market Data, Gas Prices, News (CryptoPanic), Liquidity, Correlation, Whale Flows, Volatility, Technical Indicators, etc.
- **Services (`src/services/`):** Core infrastructure layer. Contains Wallet management, Risk validation, and Monitoring.

### Executors Execute Plans

Executors perform blockchain operations.

- **EVM Chains:** Use `AgentKit` and the `Coinbase CDP SDK` for swaps and wallet management. `web3.py` may be used for low-level deterministic checks.
- **Solana:** Use `solana-py` for transaction construction and signing.
- Executors must never generate strategy decisions.

#### Technical Rationale: Solana Memo Program
On Solana, the system uses the **Memo Program** (`MemoSq9gHqT9VkU4beuy66Gf364aJ6Eic52pD34j3K`) to record trade intents (e.g., `"BUY 1 SOL with 145 USDC"`) directly on-chain.
- **Verifiability:** Every agent decision results in a real transaction hash and a verifiable on-chain record that can be audited via block explorers. 
- **Economic Simulation:** It consumes real Devnet SOL for gas, simulating the economic impact and transaction lifecycle of trading.

#### Technical Rationale: Wrapped Tokens (WETH/WAVAX)
Protocols like Uniswap V3 require ERC-20 compliance. The system interacts with **WETH** and **WAVAX** contracts to enable seamless swaps with USDC while maintaining exposure to the native asset's price action.

---

## Architectural Mandates

### 1. Singleton Wallet Management
- **Rule:** The `WalletManager` MUST be a Singleton. Access the instance via `WalletManager()`.
- **Rationale:** Prevents redundant initialization of chain providers and ensures wallet keys are loaded only once per session, preventing race conditions.

### 2. SDK Thread Isolation
- **Rule:** All calls to loop-managing SDKs (specifically **Coinbase AgentKit/CDP**) MUST be wrapped in `asyncio.to_thread`.
- **Rationale:** Prevents "Event loop is already running" errors caused by SDKs attempting to manage their own asyncio loops internally.

### 3. Stateless Execution Node
- **Rule:** The `executor_node` MUST exit immediately after submitting a transaction and recording it as `PENDING` in SQLite.
- **Rationale:** Blockchain confirmation is handled by a parallel `TransactionMonitor` service to keep the agent responsive to new market signals.

### 4. Database Safety & Economic Accountability
- **Rule:** All SQL queries MUST be stored in `src/persistence/queries.py` and MUST use parameterized placeholders (`?`).
- **Mandate:** Every trade MUST record `execution_price` and `cost_basis`.
- **Rationale:** Centralizes schema management, prevents SQL injection from LLM-generated rationale strings, and ensures the agent has the necessary data for PnL calculations.

### 5. Multi-Provider Market Context
- **Rule:** Market data aggregation SHOULD utilize multiple providers (CoinGecko + Binance + CryptoPanic) to ensure resilience.
- **Mandate:** The agent MUST be provided with pre-calculated technical indicators (RSI, MACD, EMA) during the trend analysis phase.
- **Rationale:** Prevents single-point-of-failure for market data and reduces LLM token usage while increasing precision for entry/exit timing.

### 6. Flaky RPC Resilience
- **Rule:** Critical blockchain operations (balances, status checks) MUST use the `@retry_async` decorator from `src/utils/retry.py`.
- **Rationale:** Testnet RPCs are notoriously unstable; automatic retries prevent transient network issues from crashing the agent.

### 7. Workflow Checkpointing & State Persistence
- **Rule:** The LangGraph workflow MUST utilize a `checkpointer` (e.g., `MemorySaver` or `SqliteSaver`).
- **Mandate:** All graph invocations (`ainvoke`) MUST include a `thread_id` in the `config` to enable state tracking.
- **Rationale:** Ensures the system can recover from failures or handle long-running trade lifecycles without losing context.

---

## Engineering Standards

- **Python Version:** 3.12+ (managed via `uv`).
- **Pylint Standard:** Code MUST maintain a **10.00/10** rating. 
- **Type Safety:** All public methods MUST have Mypy-compliant type annotations.
- **Logging:** Use Python's standard `logging.getLogger(__name__)`. 
- **Mandatory Quality Checks:** Before finalizing any task, run `make check`.
