# Application Runbook

This document provides a brief overview of the server components and instructions for running them.

## Server Components

The application consists of two main server components:

1.  **Frontend Server**: A React-based user interface that provides the chat and file upload functionality for interacting with the Guideline Agent.
2.  **Backend Server**: A FastAPI application that exposes the core AI agentic workflows, including document ingestion and querying, via a REST API.

---

## Server Architecture: External vs. Internal APIs

A key aspect of the backend architecture is that a single FastAPI server hosts both the external-facing API for the UI and the internal, granular APIs for the AI agent's tools. This is achieved through simple **URL path-based routing**.

All the routes for both external and internal APIs converge in a single source file:
**`guidelines_agent/mcp_server/main.py`**

### External UI Endpoints (`/agent`)

-   **Paths:** `/agent/query`, `/agent/ingest`
-   **Purpose:** These are the high-level, public-facing entry points designed for the React UI. They handle complete user goals like answering a question or ingesting a document.
-   **Security:** CORS is enabled for these routes to allow the web browser to make requests to them from `http://localhost:3000`.

### Internal Tool Endpoints (`/mcp`)

-   **Paths:** `/mcp/plan_query`, `/mcp/extract_guidelines`, `/mcp/query_guidelines`, etc.
-   **Purpose:** These are low-level, internal endpoints that expose the individual "tools" the AI agent can use. The "mcp" prefix stands for "Machine Communication Protocol," indicating they are for programmatic use by the agent, not the UI.
-   **Functionality:** Each `/mcp` endpoint performs one specific, discrete task.

### Example Request Flow

1.  **UI Request:** The user submits a query in the UI. The React app sends a `POST` request to the external endpoint: `/agent/invoke`.
2.  **Agent Invocation:** The FastAPI server routes this request to the `agent_invoke` function, which calls the high-level `query_agent`.
3.  **Internal Tool Call:** The agent, as part of its process, decides it needs to use a specific tool (e.g., the `query_planner` tool).
4.  **Server-to-Itself Request:** The code for that tool then makes an HTTP request to the internal endpoint on the *same server*: `http://localhost:8000/mcp/plan_query`.
5.  **Tool Execution:** The server routes this new request to the `plan_query_mcp` function, which executes the tool's logic and returns the result to the agent.
6.  **Final Response:** The agent orchestrates several such internal tool calls and, once finished, sends the final answer back to the UI via the original `/agent/invoke` response.

This design creates a clean separation between the high-level user-facing API and the low-level, internal toolset that the AI agent uses to accomplish its tasks.

---

## Running the Application

### 1. Backend Server

The backend server must be running for the frontend to function. It uses `uvicorn` as the ASGI server.

**To start the server with proper logging:**

Ensure you are in the project root directory (`/home/sundar/sundar_projects/agentic_guidelines_extraction`).

The server is configured to read its logging setup from `logging.yaml`. This file directs all output, including access logs and application logs, to `logs/api_server.log` with timestamps in the IST timezone.

Execute the following command to run the server in the background:

```bash
/home/sundar/sundar_projects/agentic_guidelines_extraction/venv/bin/python -m uvicorn guidelines_agent.mcp_server.main:app --host 0.0.0.0 --port 8000 &
```

**To monitor the logs:**

You can tail the log file to see real-time activity:

```bash
tail -f logs/api_server.log
```

---

### 2. Frontend Server

The frontend server is a standard React development server. It is pre-configured to proxy API requests to the backend.

**To start the server:**

A helper script is provided for convenience. Ensure you are in the project root directory.

Execute the following command to run the server in the background:

```bash
./start_frontend.sh &
```

The user interface will then be accessible at `http://localhost:3000` from your web browser.
