# 🧰 MCP Server Service

> Dedicated FastMCP tool server that provides research utilities for the Blog Writing Agent workflow.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-Tool_Server-1f6feb)](https://github.com/jlowin/fastmcp)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker)](https://www.docker.com)

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

- Hosts MCP-compatible tools used by backend agent nodes
- Exposes web research capabilities (search + page fetch)
- Supports local stdio use and deployment-style SSE transport
- Provides a separate deployable tool service for agent orchestration

---

## 🧱 Tech Stack

- Python
- FastMCP
- Tavily API (research/search source)
- Docker (for containerized deployment)

---

## 🏗️ Architecture Flow

```text
Backend Agent Node
  ↓
MCP Client Connection
  ↓
FastMCP Server
  ↓
Tool Calls (search/fetch)
  ↓
Structured Results Returned to Agent
```

---

## 📁 Project Areas

- server.py: FastMCP app setup and transport run modes
- tools/web_search.py: web search tool implementation
- tools/fetch_page.py: page fetching/scraping tool
- config.py: environment loading and runtime settings
- tests/: MCP/tool-focused tests
- Dockerfile: container build and runtime configuration

---

## ⚙️ Requirements

- Python 3.11+
- uv (recommended)
- Tavily API key

---

## 🚀 Getting Started

### Install Dependencies

```bash
cd mcp_server
uv sync
```

### Run Locally (FastMCP CLI)

```bash
uv run fastmcp run server.py
```

### Run With Inspector (Debugging)

```bash
uv run fastmcp dev inspector server.py
```

### Run Deployment-Style SSE Transport

```bash
python server.py --sse
```

### Hosted Endpoint

Current hosted MCP endpoint (as documented):

`https://Blog-Research-Tools.fastmcp.app/mcp`

---

## 🐳 Docker Quick Run

### Build Image

```bash
docker build -t bufonjoker/blog-writing-agent-mcp-server:latest .
```

### Run Container

```bash
docker run -it --rm \
  -p 8000:8000 \
  --env-file .env \
  bufonjoker/blog-writing-agent-mcp-server:latest
```

### Cursor MCP Setup (SSE)

- Type: sse
- URL: http://localhost:8000/sse

---

## 🔐 Environment Variables

Common variables:

- TAVILY_API_KEY
- PORT (defaults to 8000)

---

## 📌 Status

Implemented:

- FastMCP server bootstrapping
- Tool registration for research functions
- Local + SSE run mode support
- Dockerized deployment path

---



## 🗺️ Planning Source

- Root project plan: ../README.md
- Detailed planning exports: ../docs/
