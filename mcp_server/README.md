
---

# 🧰 MCP Server Service

> A dedicated **FastMCP tool server** that powers research capabilities for the Blog Writing Agent workflow.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastMCP](https://img.shields.io/badge/FastMCP-Tool_Server-1f6feb)
![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker)

---

## 📖 Overview

This service acts as a **tool execution layer** for your agent system. It exposes MCP-compatible tools that enable backend agents to perform web research, fetch content, and return structured data.

---

## 🎯 Core Responsibilities

* Provide MCP-compatible tools for agent workflows
* Enable web research (search + content fetching)
* Support both **local development (stdio)** and **production (SSE transport)**
* Run as an independent, deployable microservice

---

## 🧱 Tech Stack

* **Python 3.11+**
* **FastMCP**
* **Tavily API** (search provider)
* **Docker** (containerization)

---

## 🏗️ Architecture

```
Agent Node
   ↓
MCP Client
   ↓
FastMCP Server
   ↓
Tool Execution (Search / Fetch)
   ↓
Structured Response → Agent
```

---

## 📁 Project Structure

```
mcp_server/
│
├── server.py              # FastMCP server setup & transport modes
├── config.py              # Environment & runtime configuration
│
├── tools/
│   ├── web_search.py      # Search tool
│   └── fetch_page.py      # Web page fetch/scrape tool
│
├── tests/                 # Tool & MCP tests
├── Dockerfile             # Container setup
```

---

## ⚙️ Requirements

* Python **3.11+**
* `uv` (recommended package manager)
* Tavily API key

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
cd mcp_server
uv sync
```

---

### 2. Run Locally

```bash
uv run fastmcp run server.py
```

---

### 3. Run with Inspector (Debug Mode)

```bash
uv run fastmcp dev inspector server.py
```

---

### 4. Run with SSE Transport (Production Mode)

```bash
python server.py --sse
```

---

## 🌐 Hosted Endpoints

* **MCP Endpoint**

  ```
  https://Blog-Research-Tools.fastmcp.app/mcp
  ```

* **SSE Endpoint**

  ```
  https://bufon-joker-blog-writing-agent-mcp-server-v2.hf.space/sse
  ```

---

## 🐳 Docker Usage

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

### Pull from Docker Hub

```bash
docker pull bufonjoker/mcp-server
```

---

## 🔌 Cursor MCP Configuration (SSE)

```
Type: sse
URL:  http://localhost:8000/sse
```

---

## 🔐 Environment Variables

| Variable       | Description                 |
| -------------- | --------------------------- |
| TAVILY_API_KEY | API key for search tool     |
| PORT           | Server port (default: 8000) |

---

## 📌 Current Status

✅ FastMCP server setup complete
✅ Research tools implemented (search + fetch)
✅ Supports stdio and SSE modes
✅ Dockerized for deployment

---

## 🗺️ Project Planning

* Root Plan: `../README.md`
* Detailed Docs: `../docs/`

---
