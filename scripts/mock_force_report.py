
import asyncio
import os
from app.reports.daily import DailyReportGenerator
from app.core.mailer import MailerService
from datetime import datetime

class MockReportGenerator(DailyReportGenerator):
    def generate_html_report(self) -> str:
        # Mock Categories matching new logic
        categories = {
            "New Trends": [
                {"trend_name": "Agentic Coding", "growth_rate": "+850%"},
                {"trend_name": "Small Language Models", "growth_rate": "+420%"}
            ],
            "New Topics": [ # X
                {"title": "@ElonMusk: AI is accelerating", "url": "https://x.com", "relevance": 95, "risk": "LOW", "summary": "Elon tweets about compute scaling."},
                {"title": "@YannLeCun: Open Source wins", "url": "https://x.com", "relevance": 88, "risk": "LOW", "summary": "Discussion on Meta's new Llama release."}
            ],
            "New Repos": [ # GitHub
                {"title": "google/gemini-api-python", "url": "https://github.com", "relevance": 92, "risk": "LOW", "summary": "Official Python SDK for Gemini API."},
                {"title": "shadcn/ui", "url": "https://github.com", "relevance": 89, "risk": "LOW", "summary": "Beautifully designed components built with Radix UI and Tailwind CSS."}
            ],
            "Updates": [ # HF
                {"title": "HuggingFaceH4/zephyr-7b-beta", "url": "https://huggingface.co", "relevance": 90, "risk": "LOW", "summary": "New fine-tuned Mistral model available."}
            ],
            "Insights": [ # ArXiv
                {"title": "Attention Is All You Need (Revisited)", "url": "https://arxiv.org", "relevance": 98, "risk": "LOW", "summary": "A retrospective analysis of the transformer architecture."}
            ],
            "Blogs": [ # Medium
                {"title": "The State of AI 2025", "url": "https://medium.com", "relevance": 85, "risk": "LOW", "summary": "An in-depth look at the current landscape."}
            ],
            "Summary": []
        }
        return self._render_html(categories, datetime.utcnow().strftime('%Y-%m-%d'))

async def mock_force_report():
    print("--- Sending Mock 'Tech Vibe' Report ---")
    try:
        gen = MockReportGenerator()
        html = gen.generate_html_report()
        
        mailer = MailerService()
        if mailer.send_daily_report(html):
            print("SUCCESS: Mock report sent.")
        else:
            print("FAILURE: Email sending failed.")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(mock_force_report())
