"""
Quick Start Guide - FAISS-based Mall Chatbot
============================================

Follow these steps to get the RAG system up and running.
"""

print("""
╔══════════════════════════════════════════════════════════════╗
║          MALL CHATBOT - FAISS RAG SYSTEM SETUP              ║
╚══════════════════════════════════════════════════════════════╝

📋 STEP-BY-STEP SETUP GUIDE
═══════════════════════════════════════════════════════════════

STEP 1: Install Dependencies
────────────────────────────────────────────────────────────────
Run this command to install all required packages:

    pip install -r requirements.txt

This includes:
  ✓ faiss-cpu - Vector similarity search
  ✓ sentence-transformers - Text embeddings
  ✓ langchain, fastapi, etc.

Expected time: 2-3 minutes


STEP 2: Build FAISS Index (REQUIRED - First Time Only)
────────────────────────────────────────────────────────────────
Build the vector index from your Excel data:

    python build_index.py

This will:
  ✓ Load Excel file (Lido Mall AI.xlsx)
  ✓ Generate embeddings for each row
  ✓ Create FAISS index (mall.index)
  ✓ Save metadata (mall_metadata.json)

Expected time: 30-60 seconds
Required disk space: ~200 KB

⚠️  You MUST run this before starting the chatbot!


STEP 3: Test the Retriever (Optional but Recommended)
────────────────────────────────────────────────────────────────
Verify the FAISS retrieval is working:

    python retriever.py

This will show:
  ✓ Index statistics
  ✓ Sample retrieval results
  ✓ Relevance scores

Expected output:
  - Total vectors: X
  - Embedding model: all-MiniLM-L6-v2
  - Top-K: 7


STEP 4: Test Query Pipeline (Optional)
────────────────────────────────────────────────────────────────
Test the complete RAG pipeline:

    python queryRunner.py

This runs a sample query through:
  Query → FAISS Search → LLM → Response


STEP 5: Start the API Server
────────────────────────────────────────────────────────────────
Launch the FastAPI application:

    python app.py

Or use uvicorn directly:

    uvicorn app:app --host 0.0.0.0 --port 8000

Server will be available at:
  🌐 http://localhost:8000
  📋 API docs: http://localhost:8000/docs


STEP 6: Test the API
────────────────────────────────────────────────────────────────
Send a test query using curl:

    curl -X POST http://localhost:8000/chat \\
      -H "Content-Type: application/json" \\
      -d '{"query": "Where can I find Italian restaurants?"}'

Or use the interactive API docs at /docs


═══════════════════════════════════════════════════════════════
📊 PERFORMANCE EXPECTATIONS
═══════════════════════════════════════════════════════════════

Before (Full-Context):
  • Context tokens: 5,000-10,000 per query
  • Excel loaded on every query
  • High latency & cost

After (FAISS RAG):
  • Context tokens: 500-1,000 per query (7 rows)
  • Excel loaded: NEVER (only during indexing)
  • 80-90% cost reduction ✨


═══════════════════════════════════════════════════════════════
🔧 CONFIGURATION OPTIONS
═══════════════════════════════════════════════════════════════

Adjust Top-K Results:
  • Edit retriever.py: top_k=7 (default)
  • Edit queryRunner.py: k=7

Change Embedding Model:
  • Edit build_index.py: EMBEDDING_MODEL
  • Edit retriever.py: model_name
  • Rebuild index: python build_index.py

Supported models:
  • all-MiniLM-L6-v2 (default) - Fast & good
  • all-mpnet-base-v2 - More accurate, slower
  • paraphrase-MiniLM-L6-v2 - Good for semantic search


═══════════════════════════════════════════════════════════════
🚨 TROUBLESHOOTING
═══════════════════════════════════════════════════════════════

Error: "FAISS index not found"
  → Run: python build_index.py

Error: "ModuleNotFoundError: No module named 'faiss'"
  → Run: pip install faiss-cpu

Error: "sentence_transformers not found"
  → Run: pip install sentence-transformers

Poor retrieval quality:
  → Increase top_k (e.g., k=10)
  → Try different embedding model
  → Rebuild index after changes


═══════════════════════════════════════════════════════════════
📁 WHEN TO UPDATE
═══════════════════════════════════════════════════════════════

Rebuild the index when:
  ✓ Excel data is updated (Lido Mall AI.xlsx)
  ✓ Embedding model is changed
  ✓ You want to adjust indexing settings

Command:
  python build_index.py

No need to rebuild if:
  ✗ Only changing top_k parameter
  ✗ Only updating prompts
  ✗ Only changing LLM settings


═══════════════════════════════════════════════════════════════
✅ QUICK CHECKLIST
═══════════════════════════════════════════════════════════════

Before first run:
  ☐ pip install -r requirements.txt
  ☐ python build_index.py
  ☐ Verify mall.index and mall_metadata.json exist

For production deployment:
  ☐ Set environment variables (.env file)
  ☐ Configure CORS in app.py
  ☐ Set up proper error handling
  ☐ Monitor token usage


═══════════════════════════════════════════════════════════════
📚 MORE INFORMATION
═══════════════════════════════════════════════════════════════

See README_RAG.md for:
  • Detailed architecture explanation
  • API usage examples
  • Configuration guide
  • Performance metrics


═══════════════════════════════════════════════════════════════

🎉 You're all set! Happy coding!

""")
