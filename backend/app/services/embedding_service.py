import logging
import asyncio
from typing import List, Optional
from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self.api_key = settings.LLM_API_KEY
        
        if self.provider == "google" and self.api_key and self.api_key != "MOCK_KEY":
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    async def _embed_batch_google(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
        if not self.client:
            # Fallback for deterministic tests (mock embeddings)
            return [[0.0] * self.dimension for _ in texts]
            
        try:
            # Use asyncio.to_thread because the SDK might be sync or we use sync wrapper
            # We map string to EmbedContentConfig with specific task_type
            contents = [
                texts[i:i+10] for i in range(0, len(texts), 10) # batch size 10
            ]
            all_embeddings = []
            
            for batch in contents:
                # The google-genai SDK takes a list of contents or single content
                def _call_api():
                    res = self.client.models.embed_content(
                        model=self.model,
                        contents=batch,
                        config=types.EmbedContentConfig(
                            task_type=task_type,
                            output_dimensionality=self.dimension
                        )
                    )
                    return res.embeddings
                
                embeddings_objs = await asyncio.to_thread(_call_api)
                for emb in embeddings_objs:
                    all_embeddings.append(emb.values)
                    
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings with {self.provider}: {e}")
            raise

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed document chunks. Uses RETRIEVAL_DOCUMENT task type for Google."""
        if not texts:
            return []
        
        if self.provider == "google":
            embeddings = await self._embed_batch_google(texts, task_type="RETRIEVAL_DOCUMENT")
        else:
            # Default deterministic mock
            embeddings = [[0.1] * self.dimension for _ in texts]
            
        self._validate_dimensions(embeddings)
        return embeddings

    async def embed_query(self, query: str) -> List[float]:
        """Embed a search query. Uses RETRIEVAL_QUERY task type for Google."""
        if not query:
            return []
            
        if self.provider == "google":
            embeddings = await self._embed_batch_google([query], task_type="RETRIEVAL_QUERY")
        else:
            embeddings = [[0.1] * self.dimension]
            
        self._validate_dimensions(embeddings)
        return embeddings[0]

    def _validate_dimensions(self, embeddings: List[List[float]]):
        for emb in embeddings:
            if len(emb) != self.dimension:
                raise ValueError(f"Embedding dimension mismatch. Expected {self.dimension}, got {len(emb)}")
