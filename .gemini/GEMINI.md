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

## Plan → Validate → Execute

The system follows a strict separation between planning and execution.

### Modular Workflows

- **Architecture:** Decouple reasoning from execution using LangGraph. Maintain separate files for nodes, state, and graph definitions.
- **Prompts:** All LLM prompts must reside in `src/prompts/` and must be imported. Do not hardcode prompts in agent classes.
- **Models:** Use Pydantic models for all inter-node communication (e.g., `TradePlan`, `TradeAction`).
- **Validation:** Every trade plan must pass through a deterministic `RiskValidator` before execution.

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
Native gas tokens (ETH, AVAX) do not follow the ERC-20 standard.
- **Compatibility:** Protocols like Uniswap V3 require ERC-20 compliance.
- **Wrapping:** The system interacts with **WETH** and **WAVAX** contracts to enable seamless swaps with USDC while maintaining exposure to the native asset's price action.

---

## Architectural Mandates (v2.0 Updates)

### 1. Singleton Wallet Management
- **Rule:** The `WalletManager` MUST be a Singleton.
- **Rationale:** Prevents redundant initialization of chain providers and ensures wallet keys are loaded only once per session. Access the instance via `WalletManager()`.

### 2. SDK Thread Isolation
- **Rule:** All calls to loop-managing SDKs (specifically **Coinbase AgentKit/CDP**) MUST be wrapped in `asyncio.to_thread`.
- **Rationale:** Prevents "Event loop is already running" errors caused by SDKs attempting to manage their own asyncio loops internally.

### 3. Stateless Execution Node
- **Rule:** The `executor_node` MUST exit immediately after submitting a transaction and recording it as `PENDING` in SQLite.
- **Rationale:** Blockchain confirmation is handled by a parallel `TransactionMonitor` service to keep the agent responsive to new market signals.

### 4. Database Safety & Economic Accountability
- **Rule:** All SQL queries MUST be stored in `src/persistence/queries.py` and MUST use parameterized placeholders (`?`).
- **Mandate:** Every trade MUST record `execution_price` and `cost_basis`. The system MUST maintain a verifiable trail for PnL calculations.
- **Rationale:** Centralizes schema management, prevents SQL injection, and ensures the agent has the necessary data for self-reflection on profitability.

### 5. Multi-Provider Market Context
- **Rule:** Market data aggregation SHOULD utilize multiple providers (CoinGecko + Binance) to ensure resilience.
- **Mandate:** The agent MUST be provided with historical OHLCV data (Trends) and current position PnL context during the planning phase.
- **Rationale:** Prevents single-point-of-failure for market data and gives the LLM the "memory" needed to identify trends and manage exit risks.

### 6. Flaky RPC Resilience
- **Rule:** Critical blockchain operations (balances, status checks) MUST use the `@retry_async` decorator from `src/utils/retry.py`.
- **Rationale:** Testnet RPCs are notoriously unstable; automatic retries prevent transient network issues from crashing the agent.

---

## Wallet Management & Capital

### Three-Wallet Strategy
The system maintains three distinct wallets, one for each supported chain.
- Each wallet uses **USDC** as its base "bank" currency.
- **Gas Requirements:** Each wallet must be funded with a small amount of the chain's native testnet token (SOL, ETH, or AVAX) to cover gas fees for swaps.
- Trades are simulated by swapping USDC for the target asset and back.

### Initialization: Two-Stage Polling
1. **Stage 1: Funding Poll:** The main script polls for native/USDC balances. It will wait indefinitely until at least one wallet is funded. Instructions are provided in `WALLETS.md`.
2. **Stage 2: Market Poll:** Once funds are detected, the system enters its active loop, polling market data providers for signals to trigger the Planner Agent.

---

## Engineering Standards

- **Python Version:** 3.12+ (managed via `uv`).
- **Pylint Standard:** Code MUST maintain a **10.00/10** rating. 
- **Type Safety:** All public methods MUST have Mypy-compliant type annotations.
- **Logging:** Use Python's standard `logging.getLogger(__name__)`. 
- **Mandatory Quality Checks:** Before finalizing any task, run `make check`.
