"""Mock LLM + mock tool implementations.

Used when OPENAI_API_KEY is not set, or when langchain/openai are not installed.
Keeps the pipeline fully functional in offline / demo mode.
"""
import re


class MockLLM:
    """Deterministic mock that produces reasonable-looking output."""

    def generate(self, prompt: str, system: str = "") -> str:
        prompt_lower = prompt.lower()

        if "plan" in system.lower() or "planner" in prompt_lower:
            return (
                "1. Define the research question precisely.\n"
                "2. Break it into 3-4 sub-questions.\n"
                "3. Gather evidence for each sub-question.\n"
                "4. Synthesize findings into a structured answer.\n"
                "5. Verify claims against sources."
            )

        if "research" in system.lower() or "researcher" in prompt_lower:
            return (
                f"Findings for query: {prompt[:120]}\n"
                "- Key point 1: A widely accepted fact with cited source.\n"
                "- Key point 2: A secondary factor commonly mentioned.\n"
                "- Key point 3: A nuance or exception worth noting."
            )

        if "write" in system.lower() or "writer" in prompt_lower:
            return (
                f"Report:\n\n"
                f"Based on the research provided, here is a structured answer:\n\n"
                f"Overview: {prompt[:200]}\n\n"
                f"Key points:\n"
                f"1. First major insight.\n"
                f"2. Second major insight.\n"
                f"3. Third major insight.\n\n"
                f"Conclusion: A synthesized takeaway."
            )

        if "evaluat" in system.lower() or "evaluator" in prompt_lower:
            return "PASS - All claims are supported by the provided sources."

        return f"[MOCK-LLM OUTPUT] {prompt[:200]}"


class MockSearchTool:
    """Deterministic mock of a web search tool."""

    def search(self, query: str, top_k: int = 3) -> list:
        return [
            {
                "title": f"Source {i+1} on {query[:50]}",
                "url": f"https://example.com/source-{i+1}",
                "snippet": f"Relevant content for: {query[:80]}..."
            }
            for i in range(top_k)
        ]
