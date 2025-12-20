#!/usr/bin/env python
"""
Installation Script for FAISS-based RAG System
==============================================

This script helps you set up the new FAISS-based retrieval system.
"""

import subprocess
import sys
import os

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def print_step(number, text):
    print(f"\n{'=' * 70}")
    print(f"STEP {number}: {text}")
    print('=' * 70)

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"\n📦 {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if os.path.exists(filepath):
        print(f"✅ {description} found: {filepath}")
        return True
    else:
        print(f"❌ {description} not found: {filepath}")
        return False

def main():
    print_header("🚀 MALL CHATBOT - FAISS RAG SYSTEM INSTALLATION 🚀")
    
    print("""
This script will help you transition from the full-context Excel system
to the new FAISS-based Retrieval-Augmented Generation (RAG) system.

Changes made:
  ✓ Created build_index.py - Offline FAISS indexing script
  ✓ Created retriever.py - Runtime retrieval module
  ✓ Updated queryRunner.py - Now uses FAISS retrieval
  ✓ Updated prompts.py - RAG-aware prompts
  ✓ Updated requirements.txt - Added FAISS & embeddings
  ✓ Updated app.py - Startup optimization
  ✓ Created documentation - README_RAG.md, QUICKSTART.py

Expected improvements:
  • 80-90% reduction in token usage per query
  • Faster response times (no Excel parsing at runtime)
  • Scalable to much larger datasets
  • FAISS index loaded once and reused
    """)
    
    input("\nPress Enter to begin installation...")
    
    # Step 1: Check prerequisites
    print_step(1, "Checking Prerequisites")
    print("\n📋 Verifying required files...")
    
    files_ok = all([
        check_file_exists("requirements.txt", "Requirements file"),
        check_file_exists("Lido Mall AI.xlsx", "Excel data file"),
        check_file_exists("build_index.py", "Index builder script"),
        check_file_exists("retriever.py", "Retriever module"),
        check_file_exists("queryRunner.py", "Query runner"),
    ])
    
    if not files_ok:
        print("\n❌ Some required files are missing. Please check your installation.")
        sys.exit(1)
    
    print("\n✅ All required files present!")
    
    # Step 2: Install dependencies
    print_step(2, "Installing Python Dependencies")
    print("""
New packages to be installed:
  • faiss-cpu (1.9.0) - Vector similarity search
  • sentence-transformers (3.3.1) - Text embedding generation

This may take 2-3 minutes depending on your internet connection.
    """)
    
    proceed = input("Install dependencies now? (y/n): ").lower()
    if proceed == 'y':
        success = run_command(
            f"{sys.executable} -m pip install -r requirements.txt",
            "Installing dependencies"
        )
        if not success:
            print("\n⚠️  Installation failed. You may need to install manually:")
            print("    pip install -r requirements.txt")
            sys.exit(1)
    else:
        print("\n⚠️  Skipping dependency installation. Remember to install manually!")
    
    # Step 3: Build FAISS index
    print_step(3, "Building FAISS Index")
    print("""
This step will:
  1. Load the Excel file (Lido Mall AI.xlsx)
  2. Convert each row to text
  3. Generate embeddings using sentence-transformers
  4. Build and save a FAISS vector index

Output files:
  • mall.index - FAISS vector database
  • mall_metadata.json - Row metadata

Expected time: 30-60 seconds
    """)
    
    proceed = input("Build FAISS index now? (y/n): ").lower()
    if proceed == 'y':
        success = run_command(
            f"{sys.executable} build_index.py",
            "Building FAISS index"
        )
        if success:
            if os.path.exists("mall.index") and os.path.exists("mall_metadata.json"):
                index_size = os.path.getsize("mall.index") / 1024
                metadata_size = os.path.getsize("mall_metadata.json") / 1024
                print(f"\n📊 Index Statistics:")
                print(f"  • mall.index: {index_size:.2f} KB")
                print(f"  • mall_metadata.json: {metadata_size:.2f} KB")
            else:
                print("\n⚠️  Index files not created. Check for errors above.")
        else:
            print("\n⚠️  Index building failed. You can run it manually later:")
            print("    python build_index.py")
    else:
        print("\n⚠️  Skipping index building. You MUST build it before running queries!")
        print("    Run: python build_index.py")
    
    # Step 4: Test retrieval
    print_step(4, "Testing Retrieval System (Optional)")
    print("""
Test the FAISS retrieval to ensure everything is working correctly.
This will run a sample query and show retrieved results.
    """)
    
    proceed = input("Test retrieval now? (y/n): ").lower()
    if proceed == 'y':
        run_command(
            f"{sys.executable} retriever.py",
            "Testing retrieval system"
        )
    
    # Step 5: Final instructions
    print_step(5, "Setup Complete! 🎉")
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    SETUP COMPLETE! ✨                         ║
╚══════════════════════════════════════════════════════════════╝

🚀 NEXT STEPS:

1. Start the API server:
   python app.py

   Or using uvicorn:
   uvicorn app:app --host 0.0.0.0 --port 8000

2. Test the API:
   curl -X POST http://localhost:8000/chat \\
     -H "Content-Type: application/json" \\
     -d '{"query": "Where can I find Italian restaurants?"}'

3. View API docs:
   http://localhost:8000/docs

📚 DOCUMENTATION:
   • README_RAG.md - Detailed architecture and usage guide
   • QUICKSTART.py - Quick reference guide

🔄 WHEN TO UPDATE INDEX:
   Rebuild the FAISS index whenever you update the Excel data:
   python build_index.py

⚙️ CONFIGURATION:
   • Adjust top_k in retriever.py and queryRunner.py
   • Change embedding model in build_index.py
   • See README_RAG.md for details

📊 EXPECTED IMPROVEMENTS:
   ✓ 80-90% reduction in token usage
   ✓ Faster response times
   ✓ No Excel loading at runtime
   ✓ Scalable architecture

💡 NEED HELP?
   • Check README_RAG.md for troubleshooting
   • Run: python QUICKSTART.py for quick reference

Happy chatting! 🎉
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
