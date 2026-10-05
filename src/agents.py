"""Agent implementations: Planner, Researcher, Writer, Evaluator.

Uses LangGraph + OpenAI when available; otherwise falls back to a
rule-based pipeline that keeps the same interface.
"""
import os
from typing import TypedDict, List, Dict, Any

from mock_llm import MockLLM, MockSearchTool


# ---------- Shared state ----------
class ResearchState(TypedDict):
    question: str
    plan: List[str]
    findings: List[Dict[str, Any]]
    draft: str
    evaluation: str
    final_report: str


# ---------- Try to load real LLM ----------
LLM = None
_real_llm_available = False

try:
    from langchain_openai import ChatOpenAI
    if os.getenv("OPENAI_API_KEY"):
        LLM = ChatOpenAI(model=os.getenv("LLM_MODEL", "gpt-4o-mini"), temperature=0.3)
        _real_llm_available = True
        print("[OK] Loaded OpenAI ChatOpenAI")
except Exception as e:
    print(f"[WARN] Real LLM unavailable ({e.__class__.__name__}). Using MockLLM.")

if LLM is None:
    LLM = MockLLM()


def call_llm(prompt: str, system: str = "") -> str:
    """Unified interface for real or mock LLM."""
    if _real_llm_available:
        from langchain_core.messages import SystemMessage, HumanMessage
        msgs = []
        if system:
            msgs.append(SystemMessage(content=system))
        msgs.append(HumanMessage(content=prompt))
        return LLM.invoke(msgs).content
    return LLM.generate(prompt, system)


SEARCH_TOOL = MockSearchTool()


# ---------- Planner Agent ----------
def planner_agent(state: ResearchState) -> ResearchState:
    prompt = f"Break this research question into 3-4 sub-questions: {state['question']}"
    plan_text = call_llm(prompt, system="You are a research planner.")
    plan = [line.strip() for line in plan_text.split("\n") if line.strip()]
    return {**state, "plan": plan}


# ---------- Researcher Agent ----------
def researcher_agent(state: ResearchState) -> ResearchState:
    findings = []
    for sub_q in state["plan"]:
        results = SEARCH_TOOL.search(sub_q, top_k=3)
        prompt = f"Summarize findings for: {sub_q}\nSources: {results}"
        summary = call_llm(prompt, system="You are a researcher gathering evidence.")
        findings.append({"sub_question": sub_q, "sources": results, "summary": summary})
    return {**state, "findings": findings}


# ---------- Writer Agent ----------
def writer_agent(state: ResearchState) -> ResearchState:
    prompt = (
        f"Question: {state['question']}\n\n"
        f"Findings:\n" + "\n".join(f"- {f['sub_question']}: {f['summary']}" for f in state["findings"])
    )
    draft = call_llm(prompt, system="You are a writer producing a cited research report.")
    return {**state, "draft": draft}


# ---------- Evaluator Agent ----------
def evaluator_agent(state: ResearchState) -> ResearchState:
    prompt = f"Verify that each claim in this draft is supported by sources:\n\n{state['draft']}"
    evaluation = call_llm(prompt, system="You are an evaluator checking claim-source alignment.")
    return {**state, "evaluation": evaluation}


# ---------- Orchestrator (LangGraph if available, else sequential) ----------
def run_research_pipeline(question: str) -> Dict[str, Any]:
    """Run the full multi-agent pipeline."""
    state: ResearchState = {
        "question": question,
        "plan": [],
        "findings": [],
        "draft": "",
        "evaluation": "",
        "final_report": "",
    }

    try:
        from langgraph.graph import StateGraph, END

        graph = StateGraph(ResearchState)
        graph.add_node("planner", planner_agent)
        graph.add_node("researcher", researcher_agent)
        graph.add_node("writer", writer_agent)
        graph.add_node("evaluator", evaluator_agent)

        graph.set_entry_point("planner")
        graph.add_edge("planner", "researcher")
        graph.add_edge("researcher", "writer")
        graph.add_edge("writer", "evaluator")
        graph.add_edge("evaluator", END)

        app = graph.compile()
        result = app.invoke(state)
        print("[OK] Ran via LangGraph")
        result["final_report"] = result["draft"]
        return result

    except Exception as e:
        print(f"[WARN] LangGraph unavailable ({e.__class__.__name__}). Running sequential pipeline.")
        state = planner_agent(state)
        state = researcher_agent(state)
        state = writer_agent(state)
        state = evaluator_agent(state)
        state["final_report"] = state["draft"]
        return state
