# Architecture Diagrams

## Before: Full-Context Excel System

```
┌─────────────────────────────────────────────────────────────┐
│                        USER QUERY                            │
│              "Where can I find Italian restaurants?"          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     QUERY RUNNER                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  df = load_excel("Lido Mall AI.xlsx")                 │  │
│  │  context = dataframe_to_text(df)  # ALL ROWS!         │  │
│  │  response = chain.invoke({"context": context, ...})   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    EXCEL FILE LOADING                        │
│  • Read entire Excel file (150 rows)                        │
│  • Convert ALL rows to text                                 │
│  • Build massive context string (~10,000 tokens)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM (Gemini 2.5 Flash)                   │
│  Input:                                                      │
│  • System prompt                                             │
│  • FULL Excel context (~10,000 tokens)  ❌ EXPENSIVE!       │
│  • User query                                                │
│  • Chat history                                              │
│                                                              │
│  Output: Response based on full context                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         RESPONSE                             │
│  "Try Bella Italia (2nd Floor, Unit 205)..."                │
└─────────────────────────────────────────────────────────────┘

PROBLEMS:
❌ Excel loaded on EVERY query (slow)
❌ ALL rows sent to LLM (expensive tokens)
❌ Not scalable (breaks with large datasets)
❌ High latency (~2+ seconds per query)
```

---

## After: FAISS-based RAG System

### Part 1: Offline Indexing (Run Once)

```
┌─────────────────────────────────────────────────────────────┐
│              OFFLINE INDEXING (Manual Step)                  │
│                  python build_index.py                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LOAD EXCEL FILE                           │
│  df = load_excel("Lido Mall AI.xlsx", "Main Data")          │
│  • 150 rows loaded                                           │
│  • Uses existing data_loader.py (unchanged)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              CONVERT ROWS TO TEXT DOCUMENTS                  │
│  For each row:                                               │
│    text = "Store: Bella Italia | Floor: 2 | Category: ..."  │
│                                                              │
│  Result: 150 text documents                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              GENERATE EMBEDDINGS                             │
│  model = SentenceTransformer("all-MiniLM-L6-v2")            │
│  embeddings = model.encode(documents)                        │
│                                                              │
│  Result: 150 vectors × 384 dimensions                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  BUILD FAISS INDEX                           │
│  index = faiss.IndexFlatIP(384)                              │
│  index.add(embeddings)                                       │
│                                                              │
│  Result: Fast similarity search index                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   SAVE TO DISK                               │
│  faiss.write_index(index, "mall.index")                      │
│  json.dump(metadata, "mall_metadata.json")                   │
│                                                              │
│  ✅ Index ready for runtime use!                            │
└─────────────────────────────────────────────────────────────┘
```

### Part 2: Runtime Query Processing

```
┌─────────────────────────────────────────────────────────────┐
│                        USER QUERY                            │
│              "Where can I find Italian restaurants?"          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               STARTUP (Once - Before Queries)                │
│  retriever = get_retriever()                                 │
│    • Load mall.index (FAISS index)                           │
│    • Load mall_metadata.json                                 │
│    • Load embedding model                                    │
│                                                              │
│  ✅ Ready for queries!                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     QUERY EMBEDDING                          │
│  query_vector = model.encode("Italian restaurants")          │
│  • Converts query to 384-dimensional vector                  │
│  • Same embedding space as indexed documents                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   FAISS SIMILARITY SEARCH                    │
│  distances, indices = index.search(query_vector, k=7)        │
│                                                              │
│  Results (top 7 most similar):                               │
│  1. Bella Italia (score: 0.89)                               │
│  2. Pizza Hut (score: 0.85)                                  │
│  3. Olive Garden (score: 0.82)                               │
│  4. Domino's (score: 0.79)                                   │
│  5. Italian Street Food (score: 0.76)                        │
│  6. Cafe Roma (score: 0.74)                                  │
│  7. Food Court - Italian (score: 0.71)                       │
│                                                              │
│  ⚡ Lightning fast! (~5ms)                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              FORMAT RETRIEVED CONTEXT                        │
│  For each result:                                            │
│    - Get original row data from metadata                     │
│    - Format as readable text with relevance score            │
│                                                              │
│  Formatted context (7 rows):                                 │
│  "1. Store: Bella Italia | Floor: 2 | ... [0.89]            │
│   2. Store: Pizza Hut | Floor: 3 | ... [0.85]               │
│   ..."                                                       │
│                                                              │
│  Result: ~1,000 tokens (vs 10,000 before) ✅                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM (Gemini 2.5 Flash)                   │
│  Input:                                                      │
│  • System prompt (RAG-aware)                                 │
│  • Top 7 retrieved rows (~1,000 tokens) ✅ CHEAP!           │
│  • User query                                                │
│  • Chat history                                              │
│                                                              │
│  Output: Response based on retrieved context only           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         RESPONSE                             │
│  "👉 Bella Italia (2nd Floor, Unit 205) is perfect for...   │
│   ✨ Also check Pizza Hut (3rd Floor)...                    │
│   💡 Tip: Both have family meal deals!..."                  │
└─────────────────────────────────────────────────────────────┘

BENEFITS:
✅ Excel NEVER loaded at runtime (fast)
✅ Only top-K relevant rows sent (cheap)
✅ Scalable to 10,000+ rows
✅ Index reused across requests
✅ 80-90% token cost reduction
```

---

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENT                                  │
│                   (User / Frontend App)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP POST /chat
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         app.py                                   │
│                     (FastAPI Server)                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  @app.post("/chat")                                        │  │
│  │  async def chat(request):                                  │  │
│  │      response = await run_query_async(request.query)      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      queryRunner.py                              │
│                    (Query Orchestrator)                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  retriever = get_retriever(top_k=7)                        │  │
│  │                                                             │  │
│  │  async def run_query_async(query):                         │  │
│  │      context = retriever.retrieve(query, k=7) ─────────┐  │  │
│  │      response = await chain.ainvoke({...})             │  │  │
│  │      return response                                    │  │  │
│  └───────────────────────────────────────────────────────┼──┘  │
└──────────────────────────────────────────────────────────┼──────┘
                              │                             │
                              │                             │
        ┌─────────────────────┴─────────────────┐          │
        │                                        │          │
        ▼                                        ▼          │
┌────────────────┐                    ┌─────────────────────┴─────┐
│    chain.py    │                    │      retriever.py          │
│  (LLM Chain)   │                    │  (FAISS Retrieval)         │
│  ┌──────────┐  │                    │  ┌──────────────────────┐ │
│  │ LLMChain │  │                    │  │ FAISSRetriever       │ │
│  │ + Memory │  │                    │  │                      │ │
│  │ + Prompt │  │                    │  │ • index (FAISS)      │ │
│  └──────────┘  │                    │  │ • metadata (JSON)    │ │
└────────────────┘                    │  │ • model (embeddings) │ │
        │                             │  │                      │ │
        │                             │  │ Methods:             │ │
        ▼                             │  │  • embed_query()     │ │
┌────────────────┐                    │  │  • search()          │ │
│   client.py    │                    │  │  • retrieve()        │ │
│  (LLM Client)  │                    │  └──────────────────────┘ │
│  ┌──────────┐  │                    └───────────────────────────┘
│  │  Gemini  │  │                                │
│  │   API    │  │                                │
│  └──────────┘  │                                │
└────────────────┘                                │
        │                                         │
        │                                         ▼
        │                            ┌──────────────────────────┐
        │                            │   DISK (Persistent)      │
        │                            │  ┌────────────────────┐  │
        │                            │  │  mall.index        │  │
        │                            │  │  (FAISS vectors)   │  │
        │                            │  └────────────────────┘  │
        │                            │  ┌────────────────────┐  │
        │                            │  │ mall_metadata.json │  │
        │                            │  │ (Row data)         │  │
        │                            │  └────────────────────┘  │
        │                            └──────────────────────────┘
        │
        ▼
┌────────────────┐
│   prompts.py   │
│  (Templates)   │
│  ┌──────────┐  │
│  │  System  │  │
│  │  Prompt  │  │
│  │  (RAG)   │  │
│  └──────────┘  │
└────────────────┘

UNCHANGED COMPONENTS:
┌─────────────────────────────────────────────────────────────┐
│                     data_loader.py                           │
│                   (Excel Loading)                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  def load_excel(path, sheet_name):                    │  │
│  │      df = pd.read_excel(path, sheet_name=sheet_name)  │  │
│  │      return df                                         │  │
│  │                                                         │  │
│  │  def dataframe_to_text(df):                            │  │
│  │      # Convert df to text                              │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ✅ Used by build_index.py only (not at runtime)           │
└─────────────────────────────────────────────────────────────┘

OFFLINE COMPONENT:
┌─────────────────────────────────────────────────────────────┐
│                    build_index.py                            │
│                  (Index Builder)                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  df = load_excel(...)                                  │  │
│  │  embeddings = generate_embeddings(df)                  │  │
│  │  index = faiss.IndexFlatIP(...)                        │  │
│  │  index.add(embeddings)                                 │  │
│  │  save(index, metadata)                                 │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ⚙️  Run manually: python build_index.py                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow Comparison

### Before: Full-Context System

```
Request → Load Excel → Convert ALL rows → Send 10K tokens → LLM → Response
          (100ms)      (50ms)              (2000ms)               (Time: ~2150ms)
                                                                   (Cost: High)
```

### After: FAISS RAG System

**Startup (once):**

```
Load FAISS index → Load embeddings model → Ready
(50ms)            (200ms)                  (Time: 250ms one-time)
```

**Per Query:**

```
Request → Embed query → FAISS search → Format → Send 1K tokens → LLM → Response
          (20ms)        (5ms)          (10ms)    (1000ms)              (Time: ~1035ms)
                                                                        (Cost: 80-90% less)
```

---

## File Dependencies

```
app.py
  ├─→ queryRunner.py
  │     ├─→ client.py (LLM)
  │     ├─→ chain.py (LLMChain + Memory)
  │     │     └─→ prompts.py (Templates)
  │     └─→ retriever.py (FAISS)
  │           ├─→ mall.index (FAISS vectors)
  │           ├─→ mall_metadata.json (Row data)
  │           └─→ sentence-transformers (Embeddings)
  │
  └─→ (No Excel at runtime!)

build_index.py (offline)
  ├─→ data_loader.py (Excel loading)
  │     └─→ Lido Mall AI.xlsx
  ├─→ sentence-transformers (Embeddings)
  └─→ faiss (Index creation)
        ├─→ Outputs: mall.index
        └─→ Outputs: mall_metadata.json
```

---

## Scaling Comparison

### Before (Full-Context)

```
Dataset Size    Context Tokens    Query Time    Cost/Query
───────────────────────────────────────────────────────────
100 rows        ~5,000 tokens     ~1.5s         $0.05
500 rows        ~25,000 tokens    ~5s           $0.25  ❌
1,000 rows      ~50,000 tokens    ~10s          $0.50  ❌
5,000 rows      BREAKS! (too many tokens)       N/A     ❌
```

### After (FAISS RAG)

```
Dataset Size    Context Tokens    Query Time    Cost/Query
───────────────────────────────────────────────────────────
100 rows        ~1,000 tokens     ~1s           $0.01
500 rows        ~1,000 tokens     ~1s           $0.01  ✅
1,000 rows      ~1,000 tokens     ~1s           $0.01  ✅
5,000 rows      ~1,000 tokens     ~1.1s         $0.01  ✅
10,000 rows     ~1,000 tokens     ~1.2s         $0.01  ✅
```

**Key Insight:** Context size is CONSTANT regardless of dataset size! ✨
