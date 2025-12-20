from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from prompts import prompt, prompt_streaming
# from langchain_classic.memory import ConversationBufferWindowMemory
# from langchain_classic.chains import LLMChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import LLMChain
from typing import Dict
import time

# Session-based message stores for RunnableWithMessageHistory
_session_stores: Dict[str, ChatMessageHistory] = {}
SESSION_TIMEOUT_SECONDS = 3600  # 1 hour
MAX_SESSIONS = 100


def get_session_history(session_id: str) -> ChatMessageHistory:
    """
    Get or create chat message history for a session.
    Used by RunnableWithMessageHistory for automatic memory management.
    
    This function is called by LangChain to:
    - Load history before generating response
    - Save messages after response completes
    """
    # Cleanup old sessions periodically
    current_time = time.time()
    
    if not hasattr(get_session_history, '_last_cleanup'):
        get_session_history._last_cleanup = current_time
    
    # Cleanup every 5 minutes
    if current_time - get_session_history._last_cleanup > 300:
        expired = [
            sid for sid, store in _session_stores.items()
            if hasattr(store, '_last_access') and 
            current_time - store._last_access > SESSION_TIMEOUT_SECONDS
        ]
        for sid in expired:
            del _session_stores[sid]
        get_session_history._last_cleanup = current_time
    
    # Enforce max sessions
    if len(_session_stores) >= MAX_SESSIONS and session_id not in _session_stores:
        oldest_sid = min(
            _session_stores.keys(),
            key=lambda sid: getattr(_session_stores[sid], '_last_access', 0)
        )
        del _session_stores[oldest_sid]
    
    # Get or create store
    if session_id not in _session_stores:
        _session_stores[session_id] = ChatMessageHistory()
    
    # Update access time
    _session_stores[session_id]._last_access = current_time
    
    return _session_stores[session_id]


def build_chain(llm):
    """Build non-streaming chain with memory (legacy)"""
    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        input_key="query",
        return_messages=True,
        k=3
    )
    return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)


def build_streaming_chain(llm):
    """Build streaming-capable chain using LCEL (LangChain Expression Language)"""
    # LCEL chain that supports proper token-by-token streaming
    return prompt_streaming | llm | StrOutputParser()


def build_streaming_chain_with_history(llm):
    """
    Build streaming chain with automatic message history management.
    Uses LangChain's RunnableWithMessageHistory for production-grade memory.
    
    This automatically:
    - Loads conversation history before generating
    - Streams tokens in real-time
    - Saves conversation after streaming completes
    """
    base_chain = build_streaming_chain(llm)
    
    chain_with_history = RunnableWithMessageHistory(
        base_chain,
        get_session_history,
        input_messages_key="query",
        history_messages_key="chat_history",
    )
    
    return chain_with_history


def get_session_stats() -> Dict:
    """Get statistics about active sessions"""
    return {
        "active_sessions": len(_session_stores),
        "max_sessions": MAX_SESSIONS,
        "timeout_seconds": SESSION_TIMEOUT_SECONDS
    }

