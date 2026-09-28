from rag import answer_question
from ollama_client import generate_text
from web_research import research_topic, format_sources

class DocumentAgent:
    name = "Document Agent"
    def run(self, topic):
        return {
            "agent": self.name,
            "result": answer_question(topic),
        }

class ResearchAgent:
    name = "Research Agent"
    def run(self, topic):
        return {
            "agent": self.name,
            "result": research_topic(topic),
        }

class ReportAgent:
    name = "Report Agent"
    def run(self, topic, document_result, research_result):
        doc = document_result["result"]
        web = research_result["result"]
        doc_sources = "\n\n".join(
            f"[DOCUMENT SOURCE {i}] {d['source']}\n{d['text']}"
            for i, d in enumerate(doc.get("sources", []), start=1)
        )
        web_sources = format_sources(web.get("results", []))
        prompt = f"""
You are an enterprise market research report generator.

Create an executive-level report for:
{topic}

DOCUMENT EVIDENCE:
{doc_sources or "No document evidence was retrieved."}

WEB RESEARCH SOURCES:
{web_sources or "No web sources were retrieved."}

STRICT RULES:
1. Do not invent facts, statistics, competitors, dates, or sources.
2. Keep document evidence and web evidence distinguishable.
3. Cite evidence using [DOCUMENT SOURCE n] or [WEB SOURCE n].
4. If evidence is missing, explicitly state that it was not available.
5. Do not claim that a source says something unless its title/URL/evidence supports it.

Use this structure:
1. Executive Summary
2. Market Overview
3. Key Findings
4. Competitor Insights
5. Risks
6. Opportunities
7. Evidence & Sources
8. Conclusion

Write professional business language.
"""
        report = generate_text(prompt)
        return {"agent": self.name, "report": report}

class AgentOrchestrator:
    def __init__(self):
        self.document_agent = DocumentAgent()
        self.research_agent = ResearchAgent()
        self.report_agent = ReportAgent()

    def run(self, topic):
        document_result = self.document_agent.run(topic)
        research_result = self.research_agent.run(topic)
        report_result = self.report_agent.run(
            topic, document_result, research_result
        )
        return {
            "topic": topic,
            "agents": [
                document_result,
                research_result,
                report_result,
            ],
        }
