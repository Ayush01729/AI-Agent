"""
FAISS Index Builder for Mall Chatbot

This script builds a FAISS vector index from the Excel data.
Run this manually whenever the Excel data is updated.

Usage:
    python build_index.py

Output:
    - mall.index: FAISS vector index
    - mall_metadata.json: Metadata mapping vector IDs to row data
"""

import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from data_loader import load_excel, dataframe_to_text
import pandas as pd
from typing import List, Dict
import os


# Configuration
EXCEL_PATH = "Lido Mall AI.xlsx"
SHEET_NAME = "Main Data"
INDEX_PATH = "mall.index"
METADATA_PATH = "mall_metadata.json"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast and efficient model


def row_to_text(row: pd.Series) -> str:
    """
    Convert a single dataframe row into a natural language text description.
    This is what gets embedded and searched.
    
    Args:
        row: A pandas Series representing one row from the Excel sheet
        
    Returns:
        A formatted text string describing the row
    """
    parts = []
    for col, val in row.items():
        if pd.notna(val) and str(val).strip():
            parts.append(f"{col}: {val}")
    return " | ".join(parts)


def build_documents(df: pd.DataFrame) -> tuple[List[str], List[Dict]]:
    """
    Convert dataframe rows into documents and metadata.
    
    Args:
        df: The full dataframe from Excel
        
    Returns:
        documents: List of text strings (one per row)
        metadata: List of dictionaries with row data and index
    """
    documents = []
    metadata = []
    
    for idx, row in df.iterrows():
        # Create text representation for embedding
        text = row_to_text(row)
        
        # Create metadata entry (original row data)
        row_dict = {col: str(val) if pd.notna(val) else None 
                   for col, val in row.items()}
        
        documents.append(text)
        metadata.append({
            "row_index": int(idx),
            "data": row_dict,
            "text": text
        })
    
    return documents, metadata


def create_embeddings(documents: List[str], model_name: str = EMBEDDING_MODEL) -> np.ndarray:
    """
    Generate embeddings for all documents using sentence-transformers.
    
    Args:
        documents: List of text strings to embed
        model_name: Name of the sentence-transformer model to use
        
    Returns:
        numpy array of shape (num_documents, embedding_dim)
    """
    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    
    print(f"Generating embeddings for {len(documents)} documents...")
    embeddings = model.encode(
        documents,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True  # Normalize for cosine similarity
    )
    
    return embeddings


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """
    Build a FAISS index from embeddings.
    Uses IndexFlatIP (inner product) for cosine similarity with normalized vectors.
    
    Args:
        embeddings: numpy array of embeddings
        
    Returns:
        FAISS index
    """
    dimension = embeddings.shape[1]
    print(f"Building FAISS index with dimension {dimension}")
    
    # IndexFlatIP with normalized vectors = cosine similarity
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings.astype('float32'))
    
    print(f"Index built with {index.ntotal} vectors")
    return index


def save_index_and_metadata(index: faiss.Index, metadata: List[Dict]):
    """
    Save the FAISS index and metadata to disk.
    
    Args:
        index: FAISS index object
        metadata: List of metadata dictionaries
    """
    # Save FAISS index
    faiss.write_index(index, INDEX_PATH)
    print(f"✅ FAISS index saved to: {INDEX_PATH}")
    
    # Save metadata as JSON
    with open(METADATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"✅ Metadata saved to: {METADATA_PATH}")


def main():
    """
    Main function to orchestrate the indexing process.
    """
    print("=" * 60)
    print("🚀 Starting FAISS Index Building Process")
    print("=" * 60)
    
    # Step 1: Load Excel data using existing logic
    print(f"\n📊 Loading Excel file: {EXCEL_PATH}")
    df = load_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
    print(f"✅ Loaded {len(df)} rows from sheet '{SHEET_NAME}'")
    print(f"Columns: {list(df.columns)}")
    
    # Step 2: Convert rows to documents
    print("\n📝 Converting rows to text documents...")
    documents, metadata = build_documents(df)
    print(f"✅ Created {len(documents)} documents")
    
    # Show sample
    if documents:
        print(f"\n📋 Sample document:\n{documents[0][:200]}...")
    
    # Step 3: Generate embeddings
    print("\n🧠 Generating embeddings...")
    embeddings = create_embeddings(documents, EMBEDDING_MODEL)
    print(f"✅ Embeddings shape: {embeddings.shape}")
    
    # Step 4: Build FAISS index
    print("\n🔍 Building FAISS index...")
    index = build_faiss_index(embeddings)
    
    # Step 5: Save everything
    print("\n💾 Saving index and metadata...")
    save_index_and_metadata(index, metadata)
    
    # Summary
    print("\n" + "=" * 60)
    print("✨ Index building complete!")
    print("=" * 60)
    print(f"📁 Files created:")
    print(f"  - {INDEX_PATH} ({os.path.getsize(INDEX_PATH) / 1024:.2f} KB)")
    print(f"  - {METADATA_PATH} ({os.path.getsize(METADATA_PATH) / 1024:.2f} KB)")
    print(f"\n📊 Statistics:")
    print(f"  - Total documents: {len(documents)}")
    print(f"  - Embedding dimension: {embeddings.shape[1]}")
    print(f"  - Embedding model: {EMBEDDING_MODEL}")
    print("\n💡 Next step: Run the chatbot to use the new FAISS index!")
    print("=" * 60)


if __name__ == "__main__":
    main()
