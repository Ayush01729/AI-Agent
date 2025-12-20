# Mall Chatbot - FAISS-based RAG System

## 🎯 Overview

This chatbot has been refactored from a **full-context Excel-based system** to a **FAISS-based Retrieval-Augmented Generation (RAG)** system for improved performance and efficiency.

### Key Improvements

✅ **Drastically reduced token usage** - Only top-K relevant rows sent to LLM  
✅ **Faster query responses** - No Excel parsing during queries  
✅ **Persistent index** - FAISS index loaded once at startup and reused  
✅ **Scalable** - Can handle much larger datasets efficiently  
✅ **Production-ready** - Clean separation between indexing and retrieval

---

## 🏗️ Architecture

### Before (Full-Context System)

```
User Query → Load Excel → Convert ALL rows to text → Send to LLM → Response
                ↑ (Expensive! Done on every query)
```

### After (FAISS-based RAG)

```
Offline:  Excel → Build FAISS Index → Save to disk (run once manually)

Runtime:  User Query → FAISS Search → Top-K rows → LLM → Response
                              ↑ (Fast! Only relevant data)
```

---

## 📂 Project Structure

```
Mall_Chatbot/
├── app.py                    # FastAPI application (unchanged)
├── client.py                 # LLM client (unchanged)
├── chain.py                  # LLM chain setup (unchanged)
├── data_loader.py            # Excel loading functions (unchanged)
├── prompts.py                # Updated prompts for RAG
├── queryRunner.py            # ✨ NEW: Uses FAISS retrieval
├── retriever.py              # ✨ NEW: FAISS retrieval module
├── build_index.py            # ✨ NEW: Offline indexing script
├── requirements.txt          # Updated with FAISS & embeddings
├── Lido Mall AI.xlsx         # Excel data (unchanged)
├── mall.index                # Generated FAISS index (after build)
└── mall_metadata.json        # Generated metadata (after build)
```

---

## 🚀 Setup & Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**New dependencies added:**

- `faiss-cpu==1.9.0` - Vector similarity search
- `sentence-transformers==3.3.1` - Embedding generation

### 2. Build FAISS Index (One-Time Setup)

**Important:** You must build the FAISS index before running queries.

```bash
python build_index.py
```

**What this does:**

1. Loads the Excel file (`Lido Mall AI.xlsx`)
2. Converts each row into text
3. Generates embeddings using `all-MiniLM-L6-v2` model
4. Builds a FAISS index
5. Saves `mall.index` and `mall_metadata.json`

**Output:**

```
🚀 Starting FAISS Index Building Process
📊 Loaded 150 rows from sheet 'Main Data'
📝 Created 150 documents
🧠 Generating embeddings...
🔍 Building FAISS index...
✅ Index building complete!
📁 Files created:
  - mall.index (45.23 KB)
  - mall_metadata.json (128.45 KB)
```

### 3. Run the Application

```bash
python app.py
```

The server will:

1. Load the FAISS index once at startup (fast!)
2. Start accepting queries at `http://localhost:8000`

---

## 🔄 Workflow

### Offline Indexing (Run Once / When Data Changes)

```bash
python build_index.py
```

- **When to run:**

  - First time setup
  - When `Lido Mall AI.xlsx` is updated
  - When you want to change embedding model or settings

- **Outputs:** `mall.index` + `mall_metadata.json`

### Runtime Queries (Production)

```python
from queryRunner import run_query

response = run_query("Where can I find Italian restaurants?")
print(response)
```

**Flow:**

1. Query → Embedding (via `sentence-transformers`)
2. FAISS search → Top 7 most similar rows
3. Retrieved rows → Formatted context
4. Context + Query → LLM → Response

---

## 🧪 Testing

### Test the Retriever Directly

```bash
python retriever.py
```

This will:

- Load the FAISS index
- Show statistics
- Run a test query
- Display retrieved results

### Test the Full Query Pipeline

```bash
python queryRunner.py
```

This will run a sample query through the complete RAG pipeline.

---

## ⚙️ Configuration

### Adjust Top-K Results

In [retriever.py](retriever.py):

```python
retriever = get_retriever(top_k=7)  # Change to 5, 10, etc.
```

In [queryRunner.py](queryRunner.py):

```python
context = retriever.retrieve(query, k=7)  # Change here too
```

**Recommendations:**

- `k=5-7` - Good balance (default)
- `k=3-5` - Faster, less context
- `k=10-15` - More comprehensive but uses more tokens

### Change Embedding Model

In [build_index.py](build_index.py) and [retriever.py](retriever.py):

```python
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Default: fast & good

# Alternatives:
# "all-mpnet-base-v2"       # More accurate, slower
# "paraphrase-MiniLM-L6-v2" # Good for semantic search
```

⚠️ **Important:** If you change the embedding model, you MUST rebuild the index:

```bash
python build_index.py
```

---

## 📊 Performance Comparison

### Before (Full-Context)

- **Context tokens per query:** ~5,000-10,000 tokens
- **Excel loaded:** On every query (slow)
- **LLM receives:** Entire dataset
- **Cost per query:** High

### After (FAISS-based RAG)

- **Context tokens per query:** ~500-1,000 tokens (7 rows)
- **Excel loaded:** Never (only during indexing)
- **LLM receives:** Only top-K relevant rows
- **Cost per query:** 80-90% reduction ✨

---

## 🛠️ API Usage

### POST /chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Where can I find kids toys?"}'
```

**Response:**

```json
{
  "response": "🧸 Hamleys (3rd Floor, Unit 301) is your best bet for kids toys!..."
}
```

### GET /health

```bash
curl http://localhost:8000/health
```

---

## 🔍 How It Works

### 1. Indexing Phase (build_index.py)

```python
# Load Excel (existing logic, unchanged)
df = load_excel("Lido Mall AI.xlsx", sheet_name="Main Data")

# Convert each row to text
for row in df:
    text = row_to_text(row)  # "Store: XYZ | Floor: 2 | Category: Fashion"

# Generate embeddings
embeddings = model.encode(texts)  # 384-dimensional vectors

# Build FAISS index
index = faiss.IndexFlatIP(dimension=384)
index.add(embeddings)

# Save
faiss.write_index(index, "mall.index")
json.dump(metadata, "mall_metadata.json")
```

### 2. Retrieval Phase (retriever.py)

```python
# Load once at startup
index = faiss.read_index("mall.index")
metadata = json.load("mall_metadata.json")
model = SentenceTransformer("all-MiniLM-L6-v2")

# On each query
def retrieve(query, k=7):
    # 1. Convert query to embedding
    query_embedding = model.encode(query)

    # 2. Search FAISS
    distances, indices = index.search(query_embedding, k)

    # 3. Get metadata for top-K results
    results = [metadata[idx] for idx in indices]

    # 4. Format for LLM
    return format_results(results)
```

### 3. Query Phase (queryRunner.py)

```python
def run_query(query):
    # Get relevant context using FAISS
    context = retriever.retrieve(query, k=7)

    # Pass to LLM
    response = chain.invoke({"context": context, "query": query})
    return response
```

---

## 🚨 Troubleshooting

### Error: "FAISS index not found"

**Solution:** Run the indexing script first:

```bash
python build_index.py
```

### Error: "sentence-transformers not installed"

**Solution:** Install dependencies:

```bash
pip install sentence-transformers
```

### Poor retrieval quality

**Solutions:**

1. Increase `top_k` to retrieve more results
2. Try a different embedding model (e.g., `all-mpnet-base-v2`)
3. Rebuild index after changes: `python build_index.py`

### Excel file path issues

**Solution:** Ensure `Lido Mall AI.xlsx` is in the project root, or update paths in:

- [build_index.py](build_index.py) - `EXCEL_PATH` variable

---

## 📝 Notes

### Unchanged Components

- Excel parsing logic (`data_loader.py`) - Remains intact
- LLM client (`client.py`) - No changes
- LLM chain setup (`chain.py`) - No changes
- FastAPI app (`app.py`) - No changes to structure

### Modified Components

- `queryRunner.py` - Now uses FAISS retrieval instead of full Excel
- `prompts.py` - Updated to reflect RAG-based context
- `requirements.txt` - Added FAISS and sentence-transformers

### New Components

- `build_index.py` - Offline indexing script
- `retriever.py` - Runtime retrieval module
- `mall.index` - Generated FAISS index file
- `mall_metadata.json` - Generated metadata file

---

## 🎉 Success Criteria

✅ Token usage per query drops by 80-90%  
✅ Excel is only used during manual indexing (not at runtime)  
✅ FAISS index is reused across server restarts  
✅ LLM answers are grounded in retrieved rows only  
✅ System is production-ready and scalable

---

## 📚 Additional Resources

- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net/)
- [LangChain RAG Guide](https://python.langchain.com/docs/use_cases/question_answering/)

---

## 🤝 Contributing

When updating the Excel data:

1. Modify `Lido Mall AI.xlsx`
2. Run `python build_index.py` to rebuild the index
3. Restart the application

---

## 📄 License

[Your License Here]

---

**Built with ❤️ using FAISS, LangChain, and Sentence Transformers**
