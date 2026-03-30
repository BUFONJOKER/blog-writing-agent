# 🤖 Blog Writing AI Agent with MCP Tools

## 📌 Overview

This project is a **production-grade AI blog writing agent** built using LangGraph and enhanced with an **MCP (Model Context Protocol) tool server**.

The system behaves like a real **autonomous AI agent** by:

* Performing research using external tools
* Planning and structuring content
* Writing and refining iteratively
* Critiquing and improving outputs
* Producing publish-ready blog posts

---

## 🧠 Core Agent Loop

```text
Think → Research → Plan → Write → Edit → Critique → Improve → Finalize
```

---

## 🔄 Full Workflow

```text
START
  ↓
router_node
  ↓
 ┌───────────────┐
 │ needs_research│
 └──────┬────────┘
        │
   YES  ▼         NO
research_query   summarizer
        │          │
        └────┬─────┘
             ▼
      research loop 🔁
             ▼
         planner_node
             ▼
     task_executer_node
             ▼
        assembler_node
             ▼
         editor_node
             ▼
         critic_node
             ▼
     ┌───────────────┐
     │needs_revision?│
     └──────┬────────┘
            │
       YES  ▼         NO
   task_executer   finalize_node
        │               │
        └───────🔁──────┘
                 ▼
                END
```

---

## 🔌 MCP Tool Integration

Your MCP server provides tools like:

* `web_search_tool`
* `fetch_page_tool`
* `extract_keywords_tool`
* `summarize_research`

These tools are used **intelligently across nodes**.

---

## 🧩 Node-by-Node + Tool Usage

---

### 🔀 `router_node`

**Purpose:**

* Decide whether research is required

**Tool Usage:**
❌ No tools used

**Logic:**

* Analyze prompt complexity
* Set:

  * `needs_research = True/False`

---

### 🔍 `research_query_gen_node`

**Purpose:**

* Generate search queries
* Identify knowledge gaps

**Tool Usage:**
❌ No external tools (LLM-based)

**Output:**

* `research_queries`
* `research_gaps`
* `more_research_needed`

---

### 🌐 `researcher_node` (Tool Powerhouse) ⭐

**Purpose:**

* Execute real-world research using MCP tools

**Tool Usage:**

#### 1. Web Search

```python
web_search_tool(query)
```

#### 2. Fetch Web Pages

```python
fetch_page_tool(url)
```

#### 3. Extract Keywords

```python
extract_keywords_tool(content)
```

#### 4. Summarize Research

```python
summarize_research(results)
```

---

**Flow:**

```text
queries → web_search → urls → fetch_page → content → summarize
```

---

**Updates State:**

* `research_results`
* `research_summary`

---

### 🔁 Research Loop

**Logic:**

* If gaps exist:

```python
more_research_needed = True
```

→ regenerate queries → repeat research

---

### 📄 `summarizer_node`

**Purpose:**

* Provide context when research is skipped

**Tool Usage:**
✅ Optional:

```python
summarize_research(prompt)
```

---

### 🧠 `planner_node`

**Purpose:**

* Create structured blog outline

**Tool Usage:**
❌ No tools

**Uses:**

* `research_summary`
* `metadata`

---

### ✍️ `task_executer_node`

**Purpose:**

* Generate blog sections

**Tool Usage:**
✅ Optional enhancement:

```python
extract_keywords_tool(research_summary)
```

👉 Helps:

* SEO optimization
* keyword-rich writing

---

**Special Behavior:**

* Uses:

```python
feedback
```

for rewriting

---

### 🧱 `assembler_node`

**Purpose:**

* Combine sections into full draft

**Tool Usage:**
❌ No tools

---

### ✨ `editor_node`

**Purpose:**

* Improve quality and readability

**Tool Usage:**
✅ Optional:

```python
extract_keywords_tool(draft)
```

👉 Helps:

* SEO refinement
* keyword balancing

---

### 🔍 `critic_node` ⭐ (Decision Engine)

**Purpose:**

* Evaluate blog quality

**Tool Usage:**
❌ No tools (LLM reasoning)

---

**Outputs:**

```json
{
  "feedback": {
    "issues": [...],
    "suggestions": [...]
  },
  "needs_revision": true,
  "quality_score": 6,
  "confidence_score": 0.7
}
```

---

### 🔁 Revision Loop

**When triggered:**

```python
needs_revision == True
```

**Flow:**

* Send feedback → `task_executer_node`
* Improve draft
* Re-evaluate

---

### 🏁 `finalize_node`

**Purpose:**

* Prepare final blog output

**Tool Usage:**
❌ No tools

---

**Responsibilities:**

* Format markdown
* Clean structure
* Final polish

---

## 🔑 Tool Usage Summary

| Tool                    | Used In               | Purpose               |
| ----------------------- | --------------------- | --------------------- |
| `web_search_tool`       | researcher_node       | Find relevant sources |
| `fetch_page_tool`       | researcher_node       | Get full content      |
| `extract_keywords_tool` | writer/editor         | SEO optimization      |
| `summarize_research`    | researcher/summarizer | Context creation      |

---

## 🧠 State + Tool Synergy

Tools enrich state fields:

| State Field         | Tool Contribution       |
| ------------------- | ----------------------- |
| `research_results`  | web_search + fetch_page |
| `research_summary`  | summarize_research      |
| `metadata.keywords` | extract_keywords        |
| `draft`             | tool-informed writing   |

---

## 🔥 What Makes This Powerful

### ✅ Real Data (Not Hallucinated)

* Uses live search + page fetch

### ✅ SEO Optimized

* Keyword extraction integrated

### ✅ Self-Improving

* Critic-driven revisions

### ✅ Scalable

* Easily add more tools (e.g., trends, analytics)

---

## 🚀 Future Tool Integrations

* Google Trends API
* Competitor blog analyzer
* Image generation tools
* Internal knowledge base (RAG)

---

## 🧠 Final Insight

This system combines:

```text
LLM Intelligence + External Tools + Agent Loops
```

→ Result:

👉 A **real-world, production-ready AI blog writing agent**

---

## ✅ Result

* Research-backed blogs
* SEO-aware writing
* Iterative improvement
* Publish-ready output

---
