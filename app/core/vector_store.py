import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from app.core.config import get_settings
from typing import List, Dict, Any

settings = get_settings()

class VectorStore:
    def __init__(self):
        self.settings = settings
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.settings.EMBEDDING_MODEL
        )
        # Initialize client once to avoid overhead and file lock issues
        import chromadb
        self.client = chromadb.PersistentClient(path=self.settings.CHROMA_PERSIST_DIR)
        self.collection = self.client.get_or_create_collection(
            name="financial_data",
            embedding_function=self.embedding_fn
        )

    def _get_collection_sync(self):
        """Helper to get collection (now just returns cached instance)"""
        return self.collection

    async def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]]):
        """Add texts and metadata to the vector store (Non-blocking)"""
        if not texts:
            return
            
        import uuid
        ids = [str(uuid.uuid4()) for _ in texts]
        
        def _add_sync():
            collection = self._get_collection_sync()
            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
        
        import asyncio
        await asyncio.to_thread(_add_sync)

    async def similarity_search(self, query: str, n_results: int = 5, filter: Dict = None) -> List[Dict]:
        """Search for similar documents (Non-blocking)"""
        
        def _search_sync():
            collection = self._get_collection_sync()
            results = collection.query(
                query_texts=[query],
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

        import asyncio
        return await asyncio.to_thread(_search_sync)

# Global instance
vector_store = VectorStore()
