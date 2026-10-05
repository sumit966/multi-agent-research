"""FastAPI service exposing the multi-agent research pipeline."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from agents import run_research_pipeline


app = FastAPI(
    title="Multi-Agent Research Assistant API",
    description="LangGraph-style multi-agent workflow: planner, researcher, writer, evaluator",
    version="1.0.0",
)


class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    max_plan_steps: int = Field(5, ge=1, le=10)


class ResearchResponse(BaseModel):
    question: str
    plan: List[str]
    findings: List[Dict[str, Any]]
    evaluation: str
    final_report: str


@app.get("/")
def root():
    return {"message": "Multi-Agent Research Assistant", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/research", response_model=ResearchResponse)
def research(req: ResearchRequest):
    try:
        result = run_research_pipeline(req.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {e}")

    return ResearchResponse(
        question=result["question"],
        plan=result.get("plan", []),
        findings=result.get("findings", []),
        evaluation=result.get("evaluation", ""),
        final_report=result.get("final_report", ""),
    )
