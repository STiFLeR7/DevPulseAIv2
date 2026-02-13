"""Test HuggingFace MCP-powered adapter."""
import asyncio
from app.adapters.huggingface import HuggingFaceAdapter


async def main():
    hf = HuggingFaceAdapter()

    print("--- Trending Models ---")
    models = await hf.fetch_new_models(limit=3)
    print(f"  Count: {len(models)}")
    for s in models:
        dl = s.metadata.get("downloads", 0)
        ts = s.metadata.get("trending_score", 0)
        print(f"  {s.title} | {dl:,} downloads | trending={ts}")

    print("\n--- Papers ---")
    papers = await hf.fetch_papers(limit=3)
    print(f"  Count: {len(papers)}")
    for s in papers:
        print(f"  {s.title[:70]}")

    print("\n--- Trending Spaces ---")
    spaces = await hf.fetch_trending_spaces(limit=3)
    print(f"  Count: {len(spaces)}")
    for s in spaces:
        print(f"  {s.title}")

    total = len(models) + len(papers) + len(spaces)
    print(f"\n=== TOTAL: {total} signals from HuggingFace MCP ===")


if __name__ == "__main__":
    asyncio.run(main())
