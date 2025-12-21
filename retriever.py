"""
FAISS-based Retriever for Mall Chatbot

This module handles runtime retrieval of relevant mall data using FAISS.
It loads the pre-built FAISS index once at startup and performs fast similarity searches.

The retriever is designed to:
1. Load FAISS index and metadata from disk (once at startup)
2. Convert user queries into embeddings
3. Retrieve top-K most similar rows from the index
4. Return formatted, concise context for the LLM
"""

import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import os
import time
import logging
import asyncio
from functools import lru_cache
import hashlib


logger = logging.getLogger(__name__)


class FAISSRetriever:
    """
    FAISS-based retrieval system for mall data.
    
    This class encapsulates all retrieval logic and maintains the loaded
    index and embeddings model for efficient reuse across queries.
    """
    
    def __init__(
        self,
        index_path: str = "mall.index",
        metadata_path: str = "mall_metadata.json",
        model_name: str = "all-MiniLM-L6-v2",
        top_k: int = 7
    ):
        """
        Initialize the retriever by loading the FAISS index and metadata.
        
        Args:
            index_path: Path to the FAISS index file
            metadata_path: Path to the metadata JSON file
            model_name: Name of the sentence-transformer model for query embedding
            top_k: Number of top results to retrieve per query
        """
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.model_name = model_name
        self.top_k = top_k
        
        # These will be loaded lazily
        self.index: Optional[faiss.Index] = None
        self.metadata: Optional[List[Dict]] = None
        self.embedding_model: Optional[SentenceTransformer] = None
        
        # Load everything at initialization
        self._load_index()
        self._load_metadata()
        self._load_embedding_model()
    
    def _load_index(self):
        """Load the FAISS index from disk."""
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(
                f"FAISS index not found at {self.index_path}. "
                f"Please run build_index.py first to create the index."
            )
        
        print(f"📂 Loading FAISS index from {self.index_path}")
        self.index = faiss.read_index(self.index_path)
        print(f"✅ Loaded FAISS index with {self.index.ntotal} vectors")
    
    def _load_metadata(self):
        """Load the metadata from disk."""
        if not os.path.exists(self.metadata_path):
            raise FileNotFoundError(
                f"Metadata file not found at {self.metadata_path}. "
                f"Please run build_index.py first to create the metadata."
            )
        
        print(f"📂 Loading metadata from {self.metadata_path}")
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        print(f"✅ Loaded metadata for {len(self.metadata)} entries")
    
    def _load_embedding_model(self):
        """Load the sentence transformer model for query embedding."""
        print(f"🧠 Loading embedding model: {self.model_name}")
        self.embedding_model = SentenceTransformer(self.model_name)
        print(f"✅ Embedding model loaded")
    
    async def embed_query(self, query: str) -> np.ndarray:
        """
        Convert a user query into an embedding vector (async, cached).
        
        Args:
            query: User's natural language query
            
        Returns:
            numpy array of shape (1, embedding_dim)
        """
        # Check cache first
        cache_key = hashlib.md5(query.encode()).hexdigest()
        if hasattr(self, '_embedding_cache') and cache_key in self._embedding_cache:
            logger.debug("Using cached embedding")
            return self._embedding_cache[cache_key]
        
        # Run CPU-bound encoding in thread pool to avoid blocking event loop
        logger.debug("Generating new embedding")
        embedding = await asyncio.to_thread(
            self.embedding_model.encode,
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        result = embedding.astype('float32')
        
        # Cache result (simple LRU with max 100 entries)
        if not hasattr(self, '_embedding_cache'):
            self._embedding_cache = {}
        if len(self._embedding_cache) >= 100:
            # Remove oldest entry
            self._embedding_cache.pop(next(iter(self._embedding_cache)))
        self._embedding_cache[cache_key] = result
        
        return result
    
    async def search(self, query: str, k: Optional[int] = None) -> List[Dict]:
        """
        Search the FAISS index for the most relevant rows (async).
        
        Args:
            query: User's natural language query
            k: Number of results to return (defaults to self.top_k)
            
        Returns:
            List of dictionaries containing retrieved row data and scores
        """
        k = k or self.top_k
        
        # Convert query to embedding (now async)
        query_embedding = await self.embed_query(query)
        
        # Search FAISS index (fast C++ operation, minimal blocking)
        logger.debug("Searching FAISS index")
        distances, indices = self.index.search(query_embedding, k)
        
        # Retrieve metadata for the top-K results
        logger.debug("Retrieving metadata")
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.metadata):  # Safety check
                result = {
                    "row_index": self.metadata[idx]["row_index"],
                    "data": self.metadata[idx]["data"],
                    "text": self.metadata[idx]["text"],
                    "score": float(distance)  # Similarity score (higher = more similar)
                }
                results.append(result)
        
        return results
    
    def format_results_for_llm(self, results: List[Dict]) -> str:
        """
        Format retrieved results into a concise, readable context string for the LLM.
        
        Args:
            results: List of search results from self.search()
            
        Returns:
            Formatted string with retrieved context
        """
        if not results:
            return "No relevant information found in the mall database."
        
        formatted_lines = []
        for i, result in enumerate(results, 1):
            # Use the pre-formatted text from metadata
            text = result["text"]
            score = result["score"]
            formatted_lines.append(f"{i}. {text} [Relevance: {score:.3f}]")
        
        context = "\n".join(formatted_lines)
        return context
    
    async def retrieve(self, query: str, k: Optional[int] = None) -> str:
        """
        High-level retrieval method: search and format results in one call (async).
        
        This is the main method to use in your query pipeline.
        
        Args:
            query: User's natural language query
            k: Number of results to retrieve (defaults to self.top_k)
            
        Returns:
            Formatted context string ready for LLM consumption
        """
        logger.debug(f"Starting retrieval: '{query[:30]}...'")
        
        results = await self.search(query, k)
        context = self.format_results_for_llm(results)
        
        logger.debug("Retrieval complete")
        
        return context
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the loaded index.
        
        Returns:
            Dictionary with index statistics
        """
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "total_metadata": len(self.metadata) if self.metadata else 0,
            "embedding_model": self.model_name,
            "top_k": self.top_k,
            "index_path": self.index_path,
            "metadata_path": self.metadata_path
        }


# Global retriever instance (initialized once)
_retriever_instance: Optional[FAISSRetriever] = None


def get_retriever(
    index_path: str = "mall.index",
    metadata_path: str = "mall_metadata.json",
    model_name: str = "all-MiniLM-L6-v2",
    top_k: int = 7
) -> FAISSRetriever:
    """
    Get or create the global retriever instance.
    
    This function ensures we only load the FAISS index once,
    even if called multiple times.
    
    Args:
        index_path: Path to FAISS index
        metadata_path: Path to metadata JSON
        model_name: Embedding model name
        top_k: Number of results to retrieve
        
    Returns:
        FAISSRetriever instance
    """
    global _retriever_instance
    
    if _retriever_instance is None:
        print("🚀 Initializing FAISS retriever (first time)...")
        _retriever_instance = FAISSRetriever(
            index_path=index_path,
            metadata_path=metadata_path,
            model_name=model_name,
            top_k=top_k
        )
        print("✅ FAISS retriever ready!")
    
    return _retriever_instance


# Convenience function for direct use
def retrieve_context(query: str, top_k: int = 7) -> str:
    """
    Convenience function to retrieve context for a query.
    
    This is the simplest way to use the retriever in your code.
    
    Args:
        query: User's query
        top_k: Number of results to retrieve
        
    Returns:
        Formatted context string
    """
    retriever = get_retriever(top_k=top_k)
    return retriever.retrieve(query, k=top_k)


if __name__ == "__main__":
    # Test the retriever
    print("=" * 60)
    print("🧪 Testing FAISS Retriever")
    print("=" * 60)
    
    try:
        retriever = get_retriever()
        
        # Print stats
        stats = retriever.get_stats()
        print(f"\n📊 Retriever Stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Test query
        test_query = "Where can I find good restaurants for family dinner?"
        print(f"\n🔍 Test Query: {test_query}")
        print("\n📋 Retrieved Context:")
        print("-" * 60)
        context = retriever.retrieve(test_query, k=5)
        print(context)
        print("-" * 60)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Please run 'python build_index.py' first to create the FAISS index.")
