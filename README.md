# Multi-Agent Research Assistant

A production-ready multi-agent system that produces cited research reports by orchestrating four specialized AI agents: **Planner**, **Researcher**, **Writer**, and **Evaluator**. Built with LangGraph, LangChain, and OpenAI, with a fully functional offline mock fallback.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

## Overview

Instead of sending a single prompt to an LLM, this project decomposes a research task into four specialized agents that pass structured state between them:

1. **Planner Agent** — breaks the research question into 3-4 sub-questions
2. **Researcher Agent** — gathers evidence for each sub-question using a search tool
3. **Writer Agent** — synthesizes findings into a structured report
4. **Evaluator Agent** — verifies each claim against the sources (self-reflection loop)

The pipeline is orchestrated with **LangGraph** as a state graph, and if OpenAI is not configured, it automatically falls back to a **MockLLM** that keeps the full pipeline functional in offline/demo mode.

## Problem Statement

Single-shot LLM answers have well-known problems:

- **Hallucination** — the model invents facts that sound plausible
- **No structure** — answers are often rambling and lack organization
- **No verification** — there's no step that checks claims against sources
- **No transparency** — you can't see how the answer was built

For research tasks, these failures are unacceptable.

## Solution

A multi-agent pipeline that:

- **Plans** the research systematically instead of answering blindly
- **Gathers** evidence from sources with tool calling
- **Writes** structured reports with clear sections
- **Evaluates** the draft against sources before returning (reduces hallucination)
- **Falls back to a MockLLM** when no API key is set, so the pipeline always runs

## Architecture

User Question
     |
     v
+-------------+
|  Planner    |  Breaks question into sub-questions
+------+------+
       |
       v
+-------------+
| Researcher  |  For each sub-question: calls search tool,
|             |  summarizes evidence
+------+------+
       |
       v
+-------------+
|  Writer     |  Synthesizes all findings into a structured report
+------+------+
       |
       v
+-------------+
| Evaluator   |  Checks each claim against sources (self-reflection)
+------+------+
       |
       v
Final Report + Citations

## Tech Stack

| Category | Technologies |
|----------|-------------|
| Orchestration | LangGraph |
| LLM Framework | LangChain, langchain-openai |
| LLM | OpenAI GPT-4o-mini (or MockLLM fallback) |
| API | FastAPI, Uvicorn, Pydantic |
| Tools | Mock web search (extendable) |
| Testing | pytest, httpx |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| Language | Python 3.11+ |

## Project Structure

multi-agent-research/
├── src/
│   ├── __init__.py
│   ├── agents.py          # 4 agents + pipeline orchestrator
│   └── mock_llm.py        # MockLLM + MockSearchTool for offline mode
├── api/
│   ├── __init__.py
│   └── main.py            # FastAPI service exposing /research
├── tests/
│   ├── __init__.py
│   └── test_api.py        # pytest tests
├── data/                   # For future report caching
├── .github/workflows/ci.yml
├── Dockerfile
├── requirements.txt
├── requirements-optional.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md

## Quick Start

### 1. Clone

git clone https://github.com/sumit966/multi-agent-research.git
cd multi-agent-research

### 2. Virtual environment

Windows:
python -m venv venv
venv\Scripts\activate

macOS / Linux:
python3 -m venv venv
source venv/bin/activate

### 3. Install base dependencies

pip install -r requirements.txt

### 4. (Optional) Install LangGraph + OpenAI for real LLM

pip install -r requirements-optional.txt

If this fails on Python 3.14, skip it. The project automatically falls back to MockLLM.

### 5. (Optional) Configure OpenAI

Copy .env.example to .env and set your key:

OPENAI_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o-mini

If you skip this step, the pipeline uses MockLLM and still runs end-to-end.

### 6. Start the API

uvicorn api.main:app --reload

API runs at http://localhost:8000

### 7. Open Swagger UI

http://localhost:8000/docs

## API Usage

### POST /research

Request:
{
  "question": "What is retrieval-augmented generation?",
  "max_plan_steps": 5
}

Response:
{
  "question": "What is retrieval-augmented generation?",
  "plan": [
    "1. Define RAG precisely.",
    "2. Break it into retrieval + generation components.",
    "3. Gather evidence on real-world usage.",
    "4. Synthesize into a structured answer."
  ],
  "findings": [
    {
      "sub_question": "1. Define RAG precisely.",
      "sources": [
        {
          "title": "Source 1 on 1. Define RAG precisely.",
          "url": "https://example.com/source-1",
          "snippet": "Relevant content for: 1. Define RAG..."
        }
      ],
      "summary": "Findings for query: 1. Define RAG precisely..."
    }
  ],
  "evaluation": "PASS - All claims are supported by the provided sources.",
  "final_report": "Report:\n\nBased on the research provided..."
}

### Other Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| / | GET | API info |
| /health | GET | Health check |
| /docs | GET | Swagger UI |
| /redoc | GET | Alternative docs |

### cURL Example

curl -X POST "http://localhost:8000/research" -H "Content-Type: application/json" -d "{\"question\": \"What is retrieval-augmented generation?\", \"max_plan_steps\": 5}"

## Agent Design

### Planner Agent

Prompt: "Break this research question into 3-4 sub-questions: {question}"

Output: An ordered list of sub-questions that decompose the original problem.

### Researcher Agent

For each sub-question:
- Calls SEARCH_TOOL.search(sub_question, top_k=3)
- Summarizes the retrieved evidence with an LLM call

Output: List of {sub_question, sources, summary} dicts.

### Writer Agent

Prompt combines the question and all findings, then asks for a structured report.

Output: A draft report with Overview, Key Points, and Conclusion.

### Evaluator Agent

Prompt: "Verify that each claim in this draft is supported by sources."

Output: PASS or FAIL with explanation. This is the self-reflection step that keeps hallucination low.

## Offline Mode

If OPENAI_API_KEY is missing OR langchain-openai is not installed:

- The system uses MockLLM (deterministic template responses)
- The search tool returns synthetic source results
- The pipeline still runs end-to-end with the same interface

This makes the project:
- Fully testable in CI without API keys
- Runnable on any machine for demos
- Easy to swap in real LLMs later

## Testing

pytest tests/ -v

Tests cover:
- Root endpoint responds correctly
- Health check returns expected status
- /research returns plan, findings, evaluation, and final_report
- Invalid question (too short) returns 422 validation error

## Docker

Build:
docker build -t multi-agent-research .

Run:
docker run -p 8000:8000 multi-agent-research

## CI/CD Pipeline

Every push to main triggers GitHub Actions:

1. Install Python 3.11 + dependencies
2. Run pytest test suite (offline mode, no API key needed)

See .github/workflows/ci.yml.

## Key Learnings

- Multi-agent beats single-prompt for research tasks - planning + verification steps reduce hallucination
- LangGraph state graphs - typed ResearchState flows cleanly between agents
- Self-reflection loop - the Evaluator agent catches unsupported claims
- Graceful degradation - MockLLM keeps the pipeline functional without API keys
- LangChain tool calling - extendable to real search APIs (Tavily, SerpAPI, Bing)
- FastAPI + Pydantic - typed request/response with auto-generated Swagger docs
- Docker + CI - reproducible environments for agent workflows

## Future Improvements

- Real web search tool (Tavily / SerpAPI / Bing Search API)
- Persistent memory across research sessions (Redis)
- Multi-document ingestion (upload PDFs, ask questions)
- RAG integration for the Researcher agent (use ChromaDB + embeddings)
- Streaming responses via Server-Sent Events
- Cost tracking per agent call
- Deploy to GCP Cloud Run
- Human-in-the-loop review between Writer and Evaluator

## License

MIT License - see LICENSE file.

## Author

Sumit Raj
- M.Tech Applied AI & ML @ VNIT Nagpur
- Ex-Software Engineer Intern @ Salesforce
- GitHub: https://github.com/sumit966
- LinkedIn: https://www.linkedin.com/in/er-sumit-raj-/
- Portfolio: https://sumit966-github-io.vercel.app
- Email: info.sr0909@gmail.com

If you found this project useful, please consider giving it a star!
