"""Test Qdrant Search"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStoreService


async def test_search():
    print("Initializing...")
    embedding = EmbeddingService()
    store = VectorStoreService(embedding, collection_name="sec_filings")
    
    print("\n" + "="*50)
    print("🔍 Testing Search Queries")
    print("="*50)
    
    test_queries = [
        "What are NVIDIA's risks?",
        "What is Apple's revenue?",
        "How is Microsoft performing?",
        "AI semiconductor market",
        "cloud computing growth"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 40)
        
        results = store.search(query, limit=3)
        
        if results:
            for i, r in enumerate(results, 1):
                print(f"\n{i}. Score: {r['score']:.3f}")
                print(f"   Ticker: {r['metadata'].get('ticker', 'Unknown')}")
                print(f"   Filing: {r['metadata'].get('filing_type', 'Unknown')}")
                print(f"   Text: {r['text'][:200]}...")
        else:
            print("   No results found")

if __name__ == "__main__":
    asyncio.run(test_search())