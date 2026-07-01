---
name: python-langgraph-workflow
description: Use this skill when managing a Python LangGraph repository using uv and a Makefile. Covers dependency syncing, running quality controls (lint, format, typecheck, tests), generating agent graphs, and executing the git commit/push workflow.
---

# LangGraph Python Local CI & Git Push Workflow

This skill hooks into the project's native `uv` and `Makefile` lifecycle tasks, ensuring all LangGraph agents, validation suites, and formatting checks pass cleanly before committing changes.

## 🛠️ Environment Constraints

- **Package Manager:** `uv`
- **Python Runtime Wrapper:** `uv run`
- **Task Runner:** `make`

---

## 🏃‍♂️ Step 1: Pre-Commit Quality Verification

Run the unified check command. This will execute formatting checks, Ruff/Pylint linting, Mypy type-checking, Pytest suites, and codespell in sequence. **Stop immediately if this command fails.**

```bash
make check
```

### Optional Specialized Targets

If a specific sub-task in the check fails, use these isolated commands to debug or fix:

- **Auto-format Code:** `make format`
- **Run Unit Tests:** `make test`
- **Visualize LangGraph State Machine:** Generate and inspect the compiled graph image:

```bash
make graph
```

---

## 🔍 Step 2: Stage & Diff Analysis

Once the codebase passes `make check`, audit the workspace modifications before committing.

1. **Check Workspace Status:**

```bash
git status
```

2. **Stage Changes:**

```bash
git add .
```

3. **Review Staged Changes:** Run the following command to review the exact lines modified in the graphs, prompts, or tests:

```bash
git diff --cached
```

- **Agent Instruction:** Read through the staged diff carefully. Note changes to LangGraph nodes, conditional edges, state schemas, or system prompts to write a precise, technical commit message.

---

## 🔀 Step 3: Git Commit & Push

Only proceed to this step after all local verification targets have passed and the staged changes have been audited.

1. **Commit with Context:**
   - Craft a concise, clear commit message using the imperative mood (e.g., `feat: add conditional router edge to conversational agent graph`).
   - Base the message directly on the specific logical changes found during the `git diff --cached` step.

```bash
git commit -m "<descriptive-message-from-diff>"
```

2. **Push to Remote:**

```bash
git push origin HEAD
```
