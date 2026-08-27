"""Vector Store Service using Qdrant"""
import logging
import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from app.rag.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for vector database operations using Qdrant"""
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        collection_name: str = "sec_filings",
        url: Optional[str] = None,
        prefer_grpc: bool = False
    ):
        self.embedding_service = embedding_service
        self.collection_name = collection_name
        self.client = None
        self._init_client(url, prefer_grpc)
        self._ensure_collection()
    
    def _init_client(self, url: Optional[str], prefer_grpc: bool):
        """Initialize Qdrant client"""
        try:
            # Try to connect to Qdrant
            if url:
                self.client = QdrantClient(
                    url=url,
                    prefer_grpc=prefer_grpc,
                )
            else:
                # Use local Qdrant
                self.client = QdrantClient(host="localhost", port=6333)
            
            # Test connection
            self.client.get_collections()
            logger.info(f"Connected to Qdrant at {url or 'localhost:6333'}")
        except Exception as e:
            logger.warning(f"Qdrant connection failed: {e}. Using in-memory mode.")
            # Use in-memory for development
            self.client = QdrantClient(":memory:")
    
    def _ensure_collection(self):
        """Ensure collection exists"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_service.embedding_dimension,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection exists: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """
        Add documents to vector store
        
        Args:
            documents: List of document dicts with 'text' and 'metadata'
            batch_size: Batch size for embedding
        
        Returns:
            Number of documents added
        """
        if not documents:
            return 0
        
        total_added = 0
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Extract texts
            texts = [doc["text"] for doc in batch]
            
            # Generate embeddings
            embeddings = self.embedding_service.embed_batch(texts)
            
            # Create points with UUID IDs
            points = []
            for doc, embedding in zip(batch, embeddings):
                if not embedding:
                    continue
                
                # Generate UUID from chunk_id or create new one
                chunk_id = doc.get("chunk_id", str(uuid.uuid4()))
                try:
                    # Try to parse as UUID
                    point_id = str(uuid.UUID(chunk_id))
                except (ValueError, TypeError):
                    # Create a deterministic UUID from the string
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))
                
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "text": doc["text"],
                            "metadata": doc.get("metadata", {}),
                            "chunk_id": chunk_id,
                        }
                    )
                )
            
            # Upsert to Qdrant
            if points:
                try:
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=points,
                    )
                    total_added += len(points)
                    logger.info(f"Added {len(points)} documents (batch {i//batch_size + 1})")
                except Exception as e:
                    logger.error(f"Failed to upsert documents: {e}")
        
        logger.info(f"Total documents added: {total_added}")
        return total_added
    
    def search(
        self,
        query: str,
        limit: int = 5,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using whichever Qdrant client this
        service resolved to (remote server or in-memory fallback).

        Args:
            query: Search query
            limit: Number of results
            filter_conditions: Optional filter conditions

        Returns:
            List of search results
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_query(query)

        if not query_embedding:
            return []

        try:
            query_filter = self._build_filter(filter_conditions) if filter_conditions else None

            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            )

            formatted = []
            for point in response.points:
                payload = point.payload or {}
                formatted.append({
                    "text": payload.get("text", ""),
                    "metadata": payload.get("metadata", {}),
                    "chunk_id": payload.get("chunk_id", ""),
                    "score": point.score,
                    "id": point.id,
                })

            logger.info(f"Search found {len(formatted)} results")
            return formatted

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _build_filter(self, conditions: Dict[str, Any]) -> models.Filter:
        """Build a Qdrant Filter object from simple equality/IN conditions"""
        must_conditions = []

        for key, value in conditions.items():
            field_key = f"metadata.{key}"
            if isinstance(value, list):
                must_conditions.append(
                    models.FieldCondition(key=field_key, match=models.MatchAny(any=value))
                )
            else:
                must_conditions.append(
                    models.FieldCondition(key=field_key, match=models.MatchValue(value=value))
                )

        return models.Filter(must=must_conditions)
    
    def _format_results(self, results: List) -> List[Dict[str, Any]]:
        """Format search results (kept for compatibility)"""
        formatted = []
        
        for result in results:
            formatted.append({
                "text": result.payload.get("text", ""),
                "metadata": result.payload.get("metadata", {}),
                "chunk_id": result.payload.get("chunk_id", ""),
                "score": result.score,
                "id": result.id,
            })
        
        return formatted
    
    def delete_collection(self):
        """Delete the collection"""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        try:
            info = self.client.get_collection(collection_name=self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count if hasattr(info, 'points_count') else "unknown",
                "status": info.status if hasattr(info, 'status') else "unknown",
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {"error": str(e)}