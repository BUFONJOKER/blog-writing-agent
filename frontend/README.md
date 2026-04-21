# 🖥️ Frontend Service

> The user-facing app for prompt input, progress visibility, review steps, and final blog output.

[![Next.js](https://img.shields.io/badge/Next.js-App_Router-black?logo=nextdotjs)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19-blue?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-Enabled-3178C6?logo=typescript)](https://www.typescriptlang.org)

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

- Accepts blog topics/prompts from users
- Calls backend endpoints for run lifecycle operations
- Displays progress and run state to the user
- Presents review and result experiences

---

## 🧱 Tech Stack

- Next.js
- React
- TypeScript
- Tailwind CSS

---

## 🏗️ Architecture Flow

```text
User Input
	↓
Frontend Pages/Components
	↓
API Utility Layer
	↓
Backend Endpoints
	↓
Progress + Review + Result UI
```

---

## 📁 Project Areas

- app/: route-based pages and screens
- components/: reusable UI pieces
- lib/: API utility layer and helpers
- stores/: client-side state management

---

## ⚙️ Requirements

- Node.js 18+
- pnpm

---

## 🚀 Getting Started

```bash
cd frontend
pnpm install
pnpm dev
```

Open: http://localhost:3000

---

## 🔐 Environment Variables

Create frontend/.env.local with at least:

- NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/

This is the base URL used by frontend API calls.

---

## 📌 Current Status

Implemented:

- Next.js app setup with core dependencies
- Base folder layout for pages, components, API utilities, and state
- Full frontend implementation is completed
- Full Next.js frontend is vibe-coded using GitHub Copilot Chat in VS Code
- Live progress and backend status integration is completed
- Run history and final output pages are completed
- Resilience and error feedback across views is improved

Still to improve:

- More robust loading/error states and UX polish
- Support for editing and extending generated blogs after output, closer to a chat-like workflow

---


## 🗺️ Planning Source

- Root project plan: ../README.md
- Detailed planning exports: ../docs/
