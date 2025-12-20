from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from queryRunner import run_query, run_query_async, run_query_streaming
import uvicorn
from contextlib import asynccontextmanager
import time
import logging
import json

# Configure efficient logging (WARNING level for production)
logging.basicConfig(
    level=logging.WARNING,  # Change to DEBUG for development
    format='%(levelname)s - %(name)s - %(message)s',  # Simplified format, no timestamps
    handlers=[
        logging.StreamHandler()  # Console output
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load FAISS index and model before accepting requests
    print("🚀 Pre-loading FAISS index and embedding model...")
    from queryRunner import run_query, chain, retriever
    app.state.run_query = run_query
    print("✅ Ready to serve requests!")
    yield

app = FastAPI(title="Mall Chatbot API", description="API for Lulu Mall Shopping Assistant", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"  

class ChatResponse(BaseModel):
    response: str
    processing_time_ms: float = None
    profiling: dict = None

@app.get("/")
async def root():
    return {"message": "Welcome to Mall Chatbot API", "status": "running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    t0 = time.perf_counter()
    
    try:
        if not request.query or request.query.strip() == "":
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Process the query with session support
        response = await run_query_async(request.query, session_id=request.session_id)
        
        total_time = (time.perf_counter() - t0) * 1000
        
        return ChatResponse(
            response=response,
            processing_time_ms=round(total_time, 2)
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/sessions")
async def session_stats():
    """Get statistics about active sessions"""
    from chain import get_session_stats
    return get_session_stats()

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming endpoint that returns tokens as they arrive from the LLM.
    Frontend should use EventSource or fetch with streaming to consume this.
    """
    try:
        if not request.query or request.query.strip() == "":
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        async def event_generator():
            """Generate Server-Sent Events format"""
            try:
                async for chunk in run_query_streaming(request.query, session_id=request.session_id):
                    # Send as SSE format: "data: <json>\n\n"
                    yield f"data: {chunk}\n\n"
                
                # Send completion signal
                done_msg = json.dumps({"done": True})
                yield f"data: {done_msg}\n\n"
            except Exception as e:
                logger.error(f"Error in streaming: {str(e)}")
                error_msg = json.dumps({"error": str(e)})
                yield f"data: {error_msg}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    except Exception as e:
        logger.error(f"Error setting up streaming: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error setting up streaming: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
