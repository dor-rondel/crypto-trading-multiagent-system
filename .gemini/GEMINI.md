# GEMINI.md

## Project Context

This repository contains an event-driven, agentic trading simulation platform.

The system trades exclusively on testnets while using real market data to generate signals.
The primary LLM provider is **Groq (Llama 3)**, and the workflow is managed via **LangGraph**.

---

## Architectural Mandates

### 1. Singleton Wallet Management
- **Rule:** The `WalletManager` MUST be a Singleton.
- **Rationale:** Prevents redundant initialization of chain providers and ensures wallet keys are loaded only once per session. Access the instance via `WalletManager()`.

### 2. SDK Thread Isolation
- **Rule:** All calls to loop-managing SDKs (specifically **Coinbase AgentKit/CDP**) MUST be wrapped in `asyncio.to_thread`.
- **Rationale:** Prevents "Event loop is already running" errors caused by SDKs attempting to manage their own asyncio loops internally.

### 3. Stateless Execution Node
- **Rule:** The `executor_node` MUST exit immediately after submitting a transaction and recording it as `PENDING` in SQLite.
- **Rationale:** Blockchain confirmation is handled by a parallel `TransactionMonitor` service to keep the agent responsive to new market signals.

### 4. Database Safety & Organization
- **Rule:** All SQL queries MUST be stored in `src/persistence/queries.py` and MUST use parameterized placeholders (`?`).
- **Rationale:** Centralizes schema management and prevents SQL injection from LLM-generated rationale strings.

### 5. Flaky RPC Resilience
- **Rule:** Critical blockchain operations (balances, status checks) MUST use the `@retry_async` decorator from `src/utils/retry.py`.
- **Rationale:** Testnet RPCs are notoriously unstable; automatic retries prevent transient network issues from crashing the agent.

---

## Engineering Standards

- **Python Version:** 3.12+ (managed via `uv`).
- **Pylint Standard:** Code MUST maintain a **10.00/10** rating. Avoid local imports unless strictly required to prevent circular dependencies; if used, silence with `import-outside-toplevel`.
- **Type Safety:** All public methods MUST have Mypy-compliant type annotations.
- **Logging:** Use Python's standard `logging.getLogger(__name__)`.
- **Mandatory Quality Checks:** Before finalizing any task, run `make check`.
