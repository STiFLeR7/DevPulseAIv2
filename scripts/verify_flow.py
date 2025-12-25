import asyncio
from unittest.mock import MagicMock, patch
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

async def run_verification():
    print("Verifying DevPulseAI v2 Flow...")
    
    # Mock Environment
    os.environ["SUPABASE_URL"] = "https://example.supabase.co"
    os.environ["SUPABASE_KEY"] = "fake-key"
    os.environ["BYTEZ_API_KEY"] = "fake-bytez"
    
    # Mock Dependencies
    with patch("app.persistence.client.create_client") as mock_supa, \
         patch("httpx.AsyncClient") as mock_http:
             
        # Setup Supabase Mock
        mock_db_client = MagicMock()
        mock_supa.return_value = mock_db_client
        
        # Mock Upsert Return
        mock_db_client.table.return_value.upsert.return_value.select.return_value.execute.return_value.data = [{"id": "UUID-123"}]
        mock_db_client.table.return_value.select.return_value.gte.return_value.execute.return_value.data = [{"id": "UUID-123", "payload": {"title": "Test Rec", "url": "http"}}]
        
        # Mock HTTP (Bytez & GitHub)
        mock_http_instance = MagicMock()
        mock_http.return_value.__aenter__.return_value = mock_http_instance
        
        # GitHub Response
        mock_http_instance.get.return_value.json.return_value = {"items": [{"id": 1, "full_name": "test/repo", "html_url": "url", "description": "desc", "stargazers_count": 100, "language": "py"}]}
        
        # Bytez Response
        mock_http_instance.post.return_value.json.return_value = {
            "choices": [{"message": {"content": "{\"summary_text\": \"Test Summary\", \"score\": 90, \"risk_level\": \"LOW\"}"}}]
        }

        print("-> Dependencies Mocked.")
        
        # Import App Logic (Lazy import to ensure mocks are active if side-effects existed, usually fine)
        from app.api.main import run_ingestion_task, trigger_report
        
        print("-> Testing Ingestion (GitHub)...")
        await run_ingestion_task("github", True)
        print("   [Success] Ingestion task ran.")
        
        print("-> Testing Report Generation...")
        res = await trigger_report()
        print(f"   [Success] Report generated: {len(res['report_html'])} chars")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(run_verification())
    print("Verification Completed Successfully.")
