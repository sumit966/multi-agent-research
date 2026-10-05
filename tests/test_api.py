"""Tests for Multi-Agent Research Assistant API."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "message" in r.json()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_research_returns_report():
    payload = {"question": "What is retrieval-augmented generation?", "max_plan_steps": 3}
    r = client.post("/research", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "plan" in body
    assert "findings" in body
    assert "final_report" in body
    assert len(body["plan"]) > 0


def test_research_invalid_question():
    payload = {"question": "hi"}  # too short
    r = client.post("/research", json=payload)
    assert r.status_code == 422
