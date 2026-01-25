"""
Query Runner - FAISS-based RAG System

This module handles user queries using FAISS retrieval instead of full Excel context.
The FAISS index is loaded once at startup and reused for all queries.
"""

from client import llm
from chain import build_chain, build_streaming_chain_with_history
from retriever import get_retriever
import time
import logging
from profiling import QueryProfiler
import hashlib
from langchain_core.callbacks import AsyncCallbackHandler
from typing import Any, Dict, List, AsyncGenerator
import json

logger = logging.getLogger(__name__)

# Custom callback handler to track Time to First Token (TTFT)
class TTFTCallbackHandler(AsyncCallbackHandler):
    """Callback handler to measure time to first token."""
    
    def __init__(self):
        self.llm_start_time = None
        self.first_token_time = None
        self.ttft_ms = None
    
    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Record when LLM starts generating."""
        self.llm_start_time = time.perf_counter()
    
    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Record when first token arrives."""
        if self.first_token_time is None and self.llm_start_time is not None:
            self.first_token_time = time.perf_counter()
            self.ttft_ms = (self.first_token_time - self.llm_start_time) * 1000
            logger.warning(f"⚡ Time to First Token (TTFT): {self.ttft_ms:.2f}ms")
    
    def get_ttft(self) -> float:
        """Get TTFT in milliseconds."""
        return self.ttft_ms if self.ttft_ms is not None else 0.0

# Simple LRU cache for LLM responses (max 50 queries, 1 hour TTL)
_response_cache = {}
_cache_timestamps = {}
CACHE_TTL_SECONDS = 3600
MAX_CACHE_SIZE = 50

# Initialize streaming chain with automatic history management
# Note: This is the default chain using 'prompts' module
streaming_chain_with_history = build_streaming_chain_with_history(llm)

# Cache for different prompt modules' chains
_prompt_chains = {
    'prompts': streaming_chain_with_history
}

# Initialize the FAISS retriever (loads index once at startup)
# This replaces the expensive Excel loading and full-context approach
try:
    retriever = get_retriever(top_k=7)  # Retrieve top 7 most relevant rows
    print("✅ FAISS retriever initialized successfully")
except FileNotFoundError as e:
    print(f"❌ FAISS index not found: {e}")
    print("💡 Please run 'python build_index.py' to create the index first")
    retriever = None


def run_query(query: str, session_id: str = "default") -> str:
    """
    Process a user query using FAISS retrieval + LLM.
    
    Flow:
    1. User query → FAISS search for top-K relevant rows
    2. Retrieved rows → formatted as context
    3. Context + query → LLM for final answer
    
    Args:
        query: User's natural language query
        session_id: Session identifier (not used in sync version)
        
    Returns:
        LLM's response based on retrieved context
    """
    if retriever is None:
        return "Error: FAISS index not loaded. Please run build_index.py first."
    
    # Create profiler for this query
    profiler = QueryProfiler(f"sync_query_{int(time.time()*1000)}")
    
    # Retrieve relevant context using FAISS (replaces full Excel context)
    profiler.start("retrieval")
    context = retriever.retrieve(query, k=7)
    profiler.end("retrieval")
    
    # Pass only the retrieved context to the LLM (not the entire Excel sheet)
    profiler.start("llm_invocation")
    chain = build_chain(llm)
    response = chain.invoke({"context": context, "query": query})
    profiler.end("llm_invocation")
    
    # Log profiling summary
    profiler.log_summary()
    
    return response['text']


async def run_query_async(query: str, session_id: str = "default") -> str:
    """
    Async version of run_query for use in FastAPI with response caching.
    
    Args:
        query: User's natural language query
        session_id: Unique session identifier for the user
        
    Returns:
        LLM's response based on retrieved context
    """
    if retriever is None:
        return "Error: FAISS index not loaded. Please run build_index.py first."
    
    # Check cache first (normalize query for better cache hits)
    query_normalized = query.strip().lower()
    cache_key = hashlib.md5(query_normalized.encode()).hexdigest()
    
    current_time = time.time()
    if cache_key in _response_cache:
        # Check if cache entry is still valid (within TTL)
        if current_time - _cache_timestamps.get(cache_key, 0) < CACHE_TTL_SECONDS:
            logger.debug(f"Cache hit for query: '{query[:30]}...'")
            return _response_cache[cache_key]
        else:
            # Cache expired, remove it
            del _response_cache[cache_key]
            del _cache_timestamps[cache_key]
    
    # Create profiler for this query
    profiler = QueryProfiler(f"async_query_{int(time.time()*1000)}")
    logger.debug(f"Processing query for session {session_id}: '{query[:50]}...'")
    
    # Retrieve relevant context using FAISS (async)
    profiler.start("retrieval")
    logger.debug("Starting FAISS retrieval")
    context = await retriever.retrieve(query, k=7)
    profiler.end("retrieval")
    logger.debug(f"Retrieval complete: {profiler.get_duration('retrieval'):.2f}ms")
    
    # Async LLM invocation with TTFT tracking
    profiler.start("llm_invocation")
    logger.debug("Invoking LLM")
    
    # Create callback handler to track first token time
    ttft_handler = TTFTCallbackHandler()
    
    # Create session-specific chain
    session_chain = build_chain(llm)
    
    response = await session_chain.ainvoke(
        {"context": context, "query": query},
        config={"callbacks": [ttft_handler]}
    )
    
    profiler.end("llm_invocation")
    
    # Log both TTFT and total LLM time
    ttft = ttft_handler.get_ttft()
    total_llm_time = profiler.get_duration('llm_invocation')
    
    if ttft > 0:
        logger.warning(f"⚡ TTFT: {ttft:.2f}ms | Total LLM: {total_llm_time:.2f}ms | Token Generation: {total_llm_time - ttft:.2f}ms")
    else:
        logger.debug(f"LLM invocation complete: {total_llm_time:.2f}ms")
    
    # Log profiling summary at debug level
    logger.debug(f"Query complete: {profiler.get_total_duration():.2f}ms")
    
    # Store in cache (with LRU eviction if cache is full)
    response_text = response['text']
    if len(_response_cache) >= MAX_CACHE_SIZE:
        # Remove oldest entry (first key in dict)
        oldest_key = next(iter(_response_cache))
        del _response_cache[oldest_key]
        del _cache_timestamps[oldest_key]
    
    _response_cache[cache_key] = response_text
    _cache_timestamps[cache_key] = current_time
    logger.debug(f"Cached response (cache size: {len(_response_cache)})")
    
    return response_text


async def run_query_streaming(query: str, session_id: str = "default", prompt_module: str = "prompts") -> AsyncGenerator[str, None]:
    """
    Streaming with automatic conversation history management.
    Uses LangChain's RunnableWithMessageHistory for production-grade memory.
    
    Args:
        query: User's natural language query
        session_id: Unique session identifier for multi-user support
        prompt_module: Name of the prompt module to use (default: "prompts")
        
    Yields:
        JSON-formatted strings containing either tokens or error messages
    """
    if retriever is None:
        yield json.dumps({"error": "FAISS index not loaded. Please run build_index.py first."})
        return
    
    try:
        # Get or create chain for this prompt module
        if prompt_module not in _prompt_chains:
            logger.debug(f"Creating new chain for prompt module: {prompt_module}")
            _prompt_chains[prompt_module] = build_streaming_chain_with_history(llm, prompt_module)
        
        streaming_chain = _prompt_chains[prompt_module]
        
        # Check cache first
        query_normalized = query.strip().lower()
        cache_key = hashlib.md5(f"{prompt_module}:{query_normalized}".encode()).hexdigest()
        
        current_time = time.time()
        if cache_key in _response_cache:
            # Check if cache entry is still valid
            if current_time - _cache_timestamps.get(cache_key, 0) < CACHE_TTL_SECONDS:
                logger.debug(f"Cache hit for streaming query: '{query[:30]}...'")
                # Stream cached response as chunks
                cached_response = _response_cache[cache_key]
                chunk_size = 10  # Stream in chunks of 10 chars
                for i in range(0, len(cached_response), chunk_size):
                    chunk = cached_response[i:i+chunk_size]
                    yield json.dumps({"token": chunk})
                return
            else:
                # Cache expired
                del _response_cache[cache_key]
                del _cache_timestamps[cache_key]
        
        # Create profiler
        profiler = QueryProfiler(f"streaming_query_{int(time.time()*1000)}")
        logger.debug(f"Processing streaming query for session {session_id}: '{query[:50]}...'")
        
        # Retrieve context using FAISS
        profiler.start("retrieval")
        context = await retriever.retrieve(query, k=7)
        profiler.end("retrieval")
        logger.debug(f"Retrieval complete: {profiler.get_duration('retrieval'):.2f}ms")
        
        # Stream LLM response with automatic history management
        profiler.start("llm_streaming")
        logger.debug("Starting LLM streaming with automatic history")
        
        full_response = ""
        first_token = True
        
        # Use RunnableWithMessageHistory - it automatically:
        # 1. Loads conversation history
        # 2. Streams tokens in real-time
        # 3. Saves conversation after completion
        async for chunk in streaming_chain.astream(
            {"context": context, "query": query},
            config={"configurable": {"session_id": session_id}}
        ):
            if first_token:
                ttft = (time.perf_counter() - profiler.timings["llm_streaming"]["start"]) * 1000
                logger.warning(f"⚡ Time to First Token (TTFT): {ttft:.2f}ms")
                first_token = False
            
            # LCEL with StrOutputParser returns strings directly
            if chunk:
                full_response += chunk
                yield json.dumps({"token": chunk})
        
        profiler.end("llm_streaming")
        logger.debug(f"Streaming complete: {profiler.get_duration('llm_streaming'):.2f}ms")
        logger.debug(f"✅ Conversation automatically saved to session {session_id}")
        
        # Cache the full response
        if len(_response_cache) >= MAX_CACHE_SIZE:
            oldest_key = next(iter(_response_cache))
            del _response_cache[oldest_key]
            del _cache_timestamps[oldest_key]
        
        _response_cache[cache_key] = full_response
        _cache_timestamps[cache_key] = current_time
        logger.debug(f"Cached streaming response (cache size: {len(_response_cache)})")
        
    except Exception as e:
        logger.error(f"Error in streaming query: {str(e)}")
        yield json.dumps({"error": str(e)})


if __name__ == "__main__":
    # Test the new FAISS-based query system
    query = "suggest me nice places for family dinner"
    print(f"Query: {query}\n")
    print("Response:")
    print(run_query(query))