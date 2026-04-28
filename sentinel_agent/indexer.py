import os
import chromadb

# 1. Setup Local Vector DB (persistent)
chroma_client = chromadb.PersistentClient(path="./sentinel_db")

# ❌ Removed SentenceTransformerEmbeddingFunction (causing errors)
# ✅ Using default embeddings (works on Python 3.13)

collection = chroma_client.get_or_create_collection(
    name="codebase"
)

def index_project(target_dir):
    print(f"🔍 Scanning project: {target_dir}")
    
    for root, _, files in os.walk(target_dir):
        # Ignore bulky or irrelevant folders
        if any(x in root for x in ["node_modules", ".git", "sentinel_db", "dist"]):
            continue
            
        for file in files:
            if file.endswith(('.js', '.json', '.env', '.md')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if not content.strip():
                            continue
                        
                        # Add to Vector DB
                        collection.upsert(
                            documents=[content],
                            metadatas=[{"path": file_path, "filename": file}],
                            ids=[file_path]
                        )
                        print(f"✅ Indexed: {file}")
                except Exception as e:
                    print(f"⚠️ Could not read {file}: {e}")

if __name__ == "__main__":
    PROJECT_PATH = "/Users/vikasmahar/Desktop/Sentinel_SDK/app-to-fix"
    index_project(PROJECT_PATH)
    print("\n🚀 Codebase Memory Created Successfully!")