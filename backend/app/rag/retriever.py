"""Retriever Service for RAG"""
import logging
from typing import Any, Dict, List, Optional

from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStoreService

logger = logging.getLogger(__name__)


class RetrieverService:
    """Retriever service for RAG pipeline"""
    
    def __init__(
        self,
        vector_store: VectorStoreService,
        embedding_service: EmbeddingService,
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_conditions: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            filter_conditions: Optional filters
            min_score: Minimum relevance score
        
        Returns:
            List of retrieved documents
        """
        # Search vector store
        results = self.vector_store.search(
            query=query,
            limit=top_k,
            filter_conditions=filter_conditions,
        )
        
        # Filter by score
        if min_score > 0:
            results = [r for r in results if r.get("score", 0) >= min_score]
        
        logger.info(f"Retrieved {len(results)} documents for query: {query[:50]}...")
        
        return results
    
    def retrieve_with_context(
        self,
        query: str,
        top_k: int = 5,
        context_window: int = 1,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Retrieve with surrounding context
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            context_window: Number of neighboring chunks to include
        
        Returns:
            List of retrieved documents with context
        """
        # Get initial results
        results = self.retrieve(query, top_k, **kwargs)
        
        # Add context if available
        # For simplicity, we'll just return the results
        # In production, you might want to fetch neighboring chunks
        return results
    
    def format_context(
        self,
        results: List[Dict[str, Any]],
        include_metadata: bool = True,
    ) -> str:
        """
        Format retrieved documents as context for LLM
        
        Args:
            results: Retrieved documents
            include_metadata: Whether to include metadata
        
        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant information found."
        
        context_parts = []
        
        for i, result in enumerate(results):
            parts = []
            
            if include_metadata:
                metadata = result.get("metadata", {})
                parts.append(f"Source: {metadata.get('ticker', 'Unknown')}")
                parts.append(f"Filing: {metadata.get('filing_type', 'Unknown')}")
                parts.append(f"Date: {metadata.get('filing_date', 'Unknown')}")
                parts.append(f"Section: {metadata.get('section', 'Unknown')}")
                parts.append("")
            
            parts.append(result.get("text", ""))
            parts.append("")
            parts.append("---")
            
            context_parts.append("\n".join(parts))
        
        return "\n".join(context_parts)
    
    def retrieve_for_question(
        self,
        question: str,
        ticker: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Retrieve documents specifically for a question about a company
        
        Args:
            question: User question
            ticker: Company ticker
            top_k: Number of documents to retrieve
        
        Returns:
            Dictionary with results and context
        """
        # Filter by ticker
        filter_conditions = {
            "ticker": ticker,
        }
        
        # Retrieve documents
        results = self.retrieve(
            query=question,
            top_k=top_k,
            filter_conditions=filter_conditions,
        )
        
        # Format context
        context = self.format_context(results)
        
        return {
            "results": results,
            "context": context,
            "ticker": ticker,
            "question": question,
        }