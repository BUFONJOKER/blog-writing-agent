
---

## 🚀 Getting Started

### Local Development (WSL2/Ubuntu)
Use these commands for rapid testing and debugging during development.

* **Standard Execution**: Run the server using the FastMCP CLI.
```bash
uv run fastmcp run server.py
```
* **Interactive Debugging**: Launch the MCP Inspector to test tools like `web_search_tool` in a web UI.
```bash
uv run fastmcp dev inspector server.py
    ```

---

## 🐳 Docker Deployment
The Docker image is optimized using a **multi-stage build** to remain under **500MB**. It uses **Python 3.12-slim** and the **SSE transport** for compatibility with Cursor and Hugging Face.

### 1. Build the Image
Build the production-ready image. This process uses `uv` to sync dependencies into a private virtual environment.
```bash
docker build -t bufonjoker/blog-writing-agent-mcp-server:latest .
```

### 2. Run the Container
Start the server in SSE mode. This mapping allows you to access the `/health` and `/sse` endpoints on port **8000**.
```bash
docker run -it --rm \
  -p 8000:8000 \
  --env-file .env \
  bufonjoker/blog-writing-agent-mcp-server:latest
```

### 3. Connect to Cursor
Once the container is running, add it to Cursor via **Settings > Features > MCP**:
* **Type**: `sse`
* **URL**: `http://localhost:8000/sse`

---

### 🛠️ Configuration
Ensure your `.env` file contains the following before running:
* `TAVILY_API_KEY`: Required for research tools.
* `PORT`: Defaults to 8000.

---
