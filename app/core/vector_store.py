import chromadb
import sys

from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from app.core.config import get_settings
from typing import List, Dict, Any

settings = get_settings()

class VectorStore:
    def __init__(self):
        # We generally don't initialize PersistentClient here to avoid
        # "SQLite objects created in a thread can only be used in that same thread"
        self.settings = settings
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.settings.EMBEDDING_MODEL
        )

    def _get_collection_sync(self):
        """Helper to get collection in the current thread context"""
        import chromadb
        # Create client inside the thread to satisfy SQLite requirements
        client = chromadb.PersistentClient(path=self.settings.CHROMA_PERSIST_DIR)
        return client.get_or_create_collection(
            name="financial_data",
            embedding_function=self.embedding_fn
        )

    async def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]]):
        """Add texts and metadata to the vector store (Non-blocking)"""
        if not texts:
            return
            
        import uuid
        import asyncio
        ids = [str(uuid.uuid4()) for _ in texts]
        
        # 1. Generate embeddings explicitly (avoid passing model object to worker thread implicitly)
        # Run inference in a thread
        embeddings = await asyncio.to_thread(self.embedding_fn, texts)
        
        def _add_sync(embeddings_list):
            import chromadb
            client = chromadb.PersistentClient(path=self.settings.CHROMA_PERSIST_DIR)
            # Use None for embedding_function to prevent internal calls/state issues
            collection = client.get_or_create_collection(
                name="financial_data",
                embedding_function=None 
            )
            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings_list
            )
        
        # 2. Add to ChromaDB
        import os
        is_cloud = sys.platform == "win32" or os.getenv("RENDER") or os.getenv("RAILWAY_ENVIRONMENT")
        if is_cloud:
            # Skip on cloud platforms (ChromaDB requires persistent filesystem)
            return
        else:
            await asyncio.to_thread(_add_sync, embeddings)

    async def similarity_search(self, query: str, n_results: int = 5, filter: Dict = None) -> List[Dict]:
        """Search for similar documents (Non-blocking)"""
        import asyncio
        
        # 1. Generate query embedding
        query_embeddings = await asyncio.to_thread(self.embedding_fn, [query])
        
        def _search_sync(q_embeds):
            import chromadb
            client = chromadb.PersistentClient(path=self.settings.CHROMA_PERSIST_DIR)
            collection = client.get_or_create_collection(
                name="financial_data",
                embedding_function=None
            )
            results = collection.query(
                query_embeddings=q_embeds,
                n_results=n_results,
                where=filter
            )
            # Format results inside the thread
            formatted_results = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        "text": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else 0.0
                    })
            return formatted_results

        import os
        is_cloud = sys.platform == "win32" or os.getenv("RENDER") or os.getenv("RAILWAY_ENVIRONMENT")
        if is_cloud:
             # Skip on cloud to prevent crashes
             return []
        else:
             return await asyncio.to_thread(_search_sync, query_embeddings)

# Global instance
vector_store = VectorStore()
