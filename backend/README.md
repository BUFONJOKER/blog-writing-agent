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
- [API Routes](#-api-routes)
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
- api/: FastAPI app and route scaffolding, including auth and blog route modules

---

## 🔌 API Routes

### Authentication Routes

All authentication routes are mounted under `/auth`.

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/login` | Authenticate a user and set the access token cookie |
| POST | `/auth/register` | Register a new user |
| POST | `/auth/logout` | Clear the access token cookie |
| PUT | `/auth/update_password` | Update the authenticated user's password |

### Blog Routes

All blog routes are mounted under `/blog` and require an authenticated user.

| Method | Path | Purpose |
|---|---|---|
| POST | `/blog/generate` | Start a new blog generation workflow |
| POST | `/blog/review` | Resume a paused workflow after human review |
| GET | `/blog/status/{thread_id}` | Check the current status of a workflow run |
| POST | `/blog/final_post` | Fetch the finalized blog output for a run |
| GET | `/blog/user_posts/{user_id}` | List all finalized posts for a user |
| GET | `/blog/stream/{thread_id}` | Stream workflow events as server-sent events |
| DELETE | `/blog/delete_thread` | Delete a blog run thread for a user |

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
python -m api.main
```

This executes the workflow directly and supports interactive flow in the terminal.

---

## 🔐 Environment Variables

Common variables currently used in backend code:

- DB_URL (PostgreSQL URL for checkpointing from supabase)
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
- FastAPI route implementations under api/routes/
- Additional API schemas, validation, and integration hardening

---
