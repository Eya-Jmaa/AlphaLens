"""Ingest Sample SEC Data (Fallback when SEC.gov is rate limited)"""
import asyncio
import sys
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import logging

from app.rag import DocumentChunker, EmbeddingService, VectorStoreService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def ingest_sample_data():
    """Ingest sample SEC filings"""
    
    logger.info("Initializing RAG services...")
    
    # Initialize services
    embedding_service = EmbeddingService()
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
    vector_store = VectorStoreService(
        embedding_service=embedding_service,
        collection_name="sec_filings",
    )
    
    # Sample SEC filing data
    sample_data = {
        "NVDA": {
            "10-K": """
            ITEM 1A. RISK FACTORS
            Our business is subject to numerous risks including:
            - Dependence on semiconductor manufacturing partners like TSMC
            - Intense competition in AI and graphics markets from AMD and Intel
            - Regulatory changes affecting exports to China
            - Rapid technological change in the AI industry
            - Intellectual property disputes
            - Global economic conditions affecting demand
            
            ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS
            Revenue increased 126% to $60.9 billion in fiscal 2024.
            Data center revenue grew 217% to $47.5 billion driven by AI demand.
            Gaming revenue increased 15% to $10.4 billion.
            Professional visualization revenue grew 21% to $1.6 billion.
            Automotive revenue grew 21% to $1.1 billion.
            Gross margin expanded to 72.7% from 56.9%.
            Operating income grew to $33.0 billion.
            
            ITEM 8. FINANCIAL STATEMENTS
            Total assets: $111.6 billion
            Cash and equivalents: $20.0 billion
            Total debt: $17.2 billion
            Shareholders' equity: $62.3 billion
            """,
            "10-Q": """
            QUARTERLY HIGHLIGHTS
            Record revenue of $22.1 billion in Q2 2024.
            Data center revenue of $18.4 billion up 154% year-over-year.
            Strong demand for H200 and Blackwell platforms.
            Gross margins remain strong at 72.3%.
            """,
        },
        "AAPL": {
            "10-K": """
            ITEM 1A. RISK FACTORS
            - Global supply chain disruptions
            - Competition in smartphone market from Samsung and Google
            - Regulatory scrutiny of App Store practices
            - Currency fluctuations
            - Changes in consumer preferences
            
            ITEM 7. MANAGEMENT'S DISCUSSION
            Services revenue reached record $85.2 billion.
            iPhone revenue $200.6 billion.
            Mac revenue $29.4 billion.
            iPad revenue $28.3 billion.
            Wearables, Home and Accessories $39.8 billion.
            Operating margin 30.8% of revenue.
            
            ITEM 8. FINANCIAL STATEMENTS
            Total assets: $352.6 billion
            Cash and equivalents: $32.7 billion
            Total debt: $108.0 billion
            Shareholders' equity: $74.0 billion
            """,
        },
        "MSFT": {
            "10-K": """
            ITEM 1A. RISK FACTORS
            - Competition in cloud computing from AWS and Google Cloud
            - Cybersecurity threats
            - Regulatory changes in AI
            - Economic conditions affecting enterprise spending
            - Talent acquisition and retention
            
            ITEM 7. MANAGEMENT'S DISCUSSION
            Azure revenue grew 30% to $60.9 billion.
            Office Commercial revenue $51.4 billion.
            LinkedIn revenue $16.2 billion.
            Windows revenue $24.5 billion.
            Operating income $94.5 billion.
            
            ITEM 8. FINANCIAL STATEMENTS
            Total assets: $512.2 billion
            Cash and equivalents: $75.8 billion
            Total debt: $58.3 billion
            Shareholders' equity: $206.2 billion
            """,
        },
        "GOOGL": {
            "10-K": """
            ITEM 1A. RISK FACTORS
            - Competition in search and advertising
            - Regulatory scrutiny of data privacy
            - Changes in AI landscape
            - Dependence on advertising revenue
            
            ITEM 7. MANAGEMENT'S DISCUSSION
            Google Search revenue $175.0 billion.
            YouTube advertising $31.5 billion.
            Google Cloud revenue $33.0 billion.
            Google Services revenue $276.0 billion.
            Operating income $84.0 billion.
            
            ITEM 8. FINANCIAL STATEMENTS
            Total assets: $402.4 billion
            Cash and equivalents: $113.0 billion
            Total debt: $28.5 billion
            Shareholders' equity: $283.0 billion
            """,
        },
        "AMZN": {
            "10-K": """
            ITEM 1A. RISK FACTORS
            - Competition in e-commerce and cloud
            - Supply chain disruptions
            - Regulatory scrutiny
            - Workforce management
            
            ITEM 7. MANAGEMENT'S DISCUSSION
            North America revenue $352.8 billion.
            International revenue $118.3 billion.
            AWS revenue $90.8 billion.
            Operating income $36.9 billion.
            
            ITEM 8. FINANCIAL STATEMENTS
            Total assets: $527.9 billion
            Cash and equivalents: $73.4 billion
            Total debt: $66.3 billion
            Shareholders' equity: $201.9 billion
            """,
        },
    }
    
    total_chunks = 0
    
    for ticker, filings in sample_data.items():
        logger.info(f"Processing {ticker}...")
        
        for filing_type, text in filings.items():
            try:
                logger.info(f"  Processing {filing_type}")
                
                # Prepare metadata
                metadata = {
                    "ticker": ticker,
                    "filing_type": filing_type,
                    "filing_date": "2024-01-01",
                    "source": "sample_data",
                    "doc_id": f"{ticker}_{filing_type}",
                }
                
                # Chunk document
                chunks = chunker.chunk_filing(text, metadata)
                
                # Add UUID to each chunk
                for chunk in chunks:
                    chunk["chunk_id"] = str(uuid.uuid4())
                    chunk["metadata"]["chunk_id"] = chunk["chunk_id"]
                
                logger.info(f"    Created {len(chunks)} chunks with UUIDs")
                
                # Add to vector store
                if chunks:
                    added = vector_store.add_documents(chunks, batch_size=50)
                    total_chunks += added
                    logger.info(f"    Added {added} chunks to vector store")
                
            except Exception as e:
                logger.error(f"Failed to ingest {ticker} {filing_type}: {e}")
        
        logger.info(f"Completed {ticker}")
    
    logger.info("\n✅ Ingestion complete!")
    logger.info(f"Total chunks ingested: {total_chunks}")
    
    # Get collection info
    info = vector_store.get_collection_info()
    logger.info(f"Collection info: {info}")
    
    # Test search
    if total_chunks > 0:
        logger.info("\n🔍 Testing search...")
        test_queries = [
            "What are NVIDIA's risks?",
            "What is Apple's revenue?",
            "How is Microsoft performing?",
        ]
        
        for query in test_queries:
            try:
                results = vector_store.search(query, limit=2)
                logger.info(f"\nQuery: {query}")
                if results:
                    for r in results:
                        logger.info(f"  Score: {r['score']:.3f} - Ticker: {r['metadata'].get('ticker')}")
                        logger.info(f"  Text: {r['text'][:100]}...")
                else:
                    logger.info("  No results found")
            except Exception as e:
                logger.error(f"Search failed for '{query}': {e}")
    else:
        logger.warning("No chunks ingested, skipping search test")
    
    return total_chunks


async def main():
    """Main entry point"""
    await ingest_sample_data()


if __name__ == "__main__":
    asyncio.run(main())