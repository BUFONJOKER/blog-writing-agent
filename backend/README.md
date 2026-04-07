# 🧠 Backend Service

> The orchestration brain of the project: LangGraph workflow, node logic, and backend integration layer.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Workflow-orange)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Scaffold-green?logo=fastapi)](https://fastapi.tiangolo.com)

---

## 📖 Table of Contents

- [What This Service Does](#-what-this-service-does)
- [Tech Stack](#-tech-stack)
- [Architecture Flow](#-architecture-flow)
- [Project Areas](#-project-areas)
- [Requirements](#-requirements)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Current Status](#-current-status)
- [Next Milestones](#-next-milestones)
- [Planning Source](#-planning-source)

---

## 🎯 What This Service Does

- Runs the multi-step LangGraph blog generation workflow
- Connects agent nodes to MCP research tools
- Manages state and checkpoint-aware execution
- Provides API layer scaffolding for frontend integration

---

## 🧱 Tech Stack

- Python 3.11+
- LangGraph + LangChain
- FastAPI (integration layer scaffold)
- PostgreSQL-oriented checkpointing in current runner

---

## 🏗️ Architecture Flow

```text
Prompt Input
	↓
Router
	↓
Research/Tool Loop
	↓
Plan → Draft → Edit → Critique
	↓
Finalization
```

---

## 📁 Project Areas

- agent/workflow.py: graph definition, edges, and routing logic
- agent/main.py: local runner entrypoint for graph execution
- agent/nodes/: node implementations (router, planner, editor, critic, etc.)
- agent/tools.py: tool initialization and binding
- api/: FastAPI app and route scaffolding

---

## ⚙️ Requirements

- Python 3.11+
- uv (recommended)
- PostgreSQL-compatible URL for the current checkpointing setup

---

## 🚀 Getting Started

### Install Dependencies

```bash
cd backend
uv sync
```

### Run Backend Agent Workflow

```bash
python -m agent.main
```

This executes the workflow directly and supports interactive flow in the terminal.

---

## 🔐 Environment Variables

Common variables currently used in backend code:

- DB_URL
- HORIZON_TOKEN
- HUGGINGFACEHUB_API_TOKEN

Variables referenced in broader project/deployment docs:

- DATABASE_URL
- MCP_SERVER_URL
- MCP_AUTH_TOKEN

---

## 📌 Current Status

Implemented:

- Multi-node LangGraph workflow with conditional edges
- Tool loop integration through LangGraph ToolNode

In progress:

- FastAPI route implementations under api/routes/
- Additional API schemas, validation, and integration hardening

---

## 🛠️ Next Milestones

- Complete route implementations in api/routes/
- Add stronger request/response schemas and validation
- Expand automated tests around routing and node behavior
- Improve environment/config consistency across local and deployment setups

---

## 🗺️ Planning Source

- Root project plan: ../README.md
- Detailed planning exports: ../docs/
