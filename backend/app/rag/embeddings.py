"""Local Embedding Service"""
import logging
from typing import List

# Use sentence-transformers for local embeddings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Local embedding service using sentence-transformers"""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu"
    ):
        """
        Initialize embedding service
        
        Args:
            model_name: Name of the sentence-transformers model
            device: 'cpu' or 'cuda' (cuda requires GPU)
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self._init_model()
    
    def _init_model(self):
        """Initialize the embedding model"""
        try:
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device
            )
            logger.info(f"Initialized embedding model: {self.model_name}")
            logger.info(f"Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Embed a single text"""
        if not text:
            return []
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return []
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts in batch"""
        if not texts:
            return []
        
        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
                batch_size=32
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            return [[] for _ in texts]
    
    def embed_query(self, query: str) -> List[float]:
        """Embed a query (uses the same model)"""
        return self.embed_text(query)
    
    @property
    def embedding_dimension(self) -> int:
        """Get embedding dimension"""
        if self.model:
            return self.model.get_sentence_embedding_dimension()
        return 384  # Default for all-MiniLM-L6-v2