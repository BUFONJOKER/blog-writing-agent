# 📝 Blog Writing Agent - Full Stack Project

> An AI-powered full-stack application that researches, plans, and drafts blog content using an agent workflow plus external tools.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Framework-orange)](https://langchain-ai.github.io/langgraph/)
[![Next.js](https://img.shields.io/badge/Next.js-Frontend-black?logo=nextdotjs)](https://nextjs.org)

---

## 📖 Table of Contents

- [Demo Videos](#-demo-videos)
- [Problem This App Solves](#-problem-this-app-solves)
- [Problems in the Project](#-problems-in-the-project)
- [What This Project Does](#-what-this-project-does)
- [Tech Stack](#-tech-stack)
- [Architecture Flow](#-architecture-flow)
- [Project Areas](#-project-areas)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Current Status](#-current-status)
- [Next Milestones](#-next-milestones)
- [Planning Source](#-planning-source)
- [Contributing](#-contributing)

---

## 🎬 Demo Videos

### Fast-Paced Highlight Reel

A quicker highlight reel of the main workflow and output.

[Demo of Full Project on YouTube](https://www.youtube.com/watch?v=q1T_noaZJhE)

> **💡 Tip:** Click the settings icon (⚙️) in the video player and select **Speed** → **0.25x** to watch at slower speed for better understanding.

### Full Long Video

A complete end-to-end walkthrough of the project, including setup, workflow execution, and final output review.

[Full Long Demo on YouTube](https://www.youtube.com/watch?v=KgpNe0CwLn4)

---

## 🚩 Problem This App Solves

Writing a high-quality blog is usually slow and manual. Most people have to:

- Research multiple sources by hand
- Gather and organize facts manually
- Draft, edit, and rework the structure several times

If you only use a simple LLM, it often produces generic content from model memory and cannot reliably do live research, source gathering, and multi-step editorial refinement.

This app solves that by using an agent workflow that can:

- Do live research with tools
- Think in steps (plan before writing)
- Write section by section
- Edit and assemble a full draft
- Run critique and revision loops
- Support human review before generating the final blog

---

## ⚠️ Problems in the Project

There are still a few important problems we need to improve:

- The current Ollama-based workflow takes nearly 17 minutes to complete end to end
- Total token usage is very high, at roughly 86,000 tokens including input and output
- We should reduce runtime and token cost to make the system faster and more efficient
- Right now the agent is not a chat app after generation
- After a blog is generated, the user should be able to edit it, add headings, or make other changes using the LLM
- That post-generation editing flow would make the experience feel more like a chat-based assistant

---

## 🎯 What This Project Does

The Blog Writing Agent is a full-stack AI system where:

- The **frontend** collects prompts and presents progress/results.
- The **backend** runs a LangGraph workflow to coordinate writing steps.
- The **MCP server** provides tool-based research (search and page fetch).

---

## 🏗️ Architecture Flow

```text
User Prompt
	↓
Frontend (Next.js)
	↓
Backend Orchestration (LangGraph/FastAPI layer)
	↓
MCP Tools (web search + fetch)
	↓
Plan → Draft → Edit → Critique → Final Output
```

### 🤖 Workflow Nodes (Current Graph Design)

| Step | What it does |
|------|--------------|
| 🔀 Router | Determines whether external research is needed |
| 🔍 Research Query Generator | Creates search queries |
| 🌐 Researcher + Tool Loop | Calls tools and gathers source material |
| 🧾 Summarizer | Condenses research into usable context |
| 🗂️ Planner | Builds blog outline/tasks |
| ✍️ Task Executor | Writes sections |
| 🧵 Assembler + Editor | Combines and improves draft |
| 🧠 Critic | Requests revision loop or finalize |
| ✅ Finalize (+ image planning/generation nodes) | Produces final result |

---

## 🛠️ Tech Stack

### Backend

- Python 3.11+
- LangGraph + LangChain
- FastAPI (route layer present, partially scaffold-level)
- PostgreSQL-oriented checkpointing setup in current agent runner

### Tool Server

- FastMCP
- Tavily-based search and page-fetch tooling

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

---

## 📁 Project Structure

```text
blog-writing-agent/
├── frontend/        # Next.js frontend app
├── backend/         # Agent workflow, nodes, API scaffolding
├── mcp_server/      # FastMCP research tool server
├── docs/            # Exported Notion project docs/tasks
└── README.md
```

---

## 📁 Project Areas

- frontend/: user interface and client-side state
- backend/: workflow orchestration and backend modules
- mcp_server/: FastMCP tools used by the agent
- docs/: exported Notion planning/task documentation

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- pnpm
- uv (recommended)

### 1) Run MCP Server

```bash
cd mcp_server
uv sync
uv run fastmcp run server.py
```

Optional SSE mode:

```bash
python server.py --sse
```

### 2) Run Backend Agent Workflow

```bash
cd backend
uv sync
python -m agent.main
```

### 3) Run Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Open: `http://localhost:3000`

---

## 🔐 Environment Variables

Create service-local `.env` files where needed.

Common variables used across the repo/docs:

- `TAVILY_API_KEY`
- `MCP_AUTH_TOKEN`
- `DB_URL` (or `DATABASE_URL` in deployment-oriented docs)
- `HORIZON_TOKEN`
- `HUGGINGFACEHUB_API_TOKEN`
- `NEXT_PUBLIC_BACKEND_URL`

---

## 📌 Current Status

Implemented now:

- LangGraph workflow with multiple nodes and conditional edges
- MCP tool integration in the agent loop
- Notion-derived planning docs and task structure

Completed recently:

- Backend implementation is completed
- Frontend implementation is completed
- Total time spent on this complete project (browsing + coding), measured with WakaTime: 99 hours 47 minutes

Deployment status (current):

- MCP server is deployed
- Frontend is not deployed yet
- Backend is not deployed yet

Planned upgrades:

- Deploy frontend and backend in future milestones
- Use OpenAI models via API (cloud) in place of the current local Ollama/Qwen 3.5 setup

To avoid confusion, treat this repository as **active development** rather than a fully completed production release.

---

## 🛠️ Next Milestones

- Add richer end-to-end API + UI integration
- Expand structured test coverage across services
- Improve deployment automation and production configuration
- Add publish/export flows for generated blogs
- Add configurable writing styles and tone controls

---

## 🗺️ Planning Source

Primary planning source:

- Notion project: https://southern-dogsled-629.notion.site/Blog-Writing-Agent-Full-Stack-Project-32fc1cfa959c8192abaffdc427593c41
- Exported docs in this repo: `docs/`

---

## 🤝 Contributing

1. Create a feature branch.
2. Keep changes focused by service.
3. Update docs for behavior changes.
4. Open a PR with testing notes.
