import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from app.core.config import get_settings
from typing import List, Dict, Any

settings = get_settings()

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        
        # Use sentence-transformers for proper embeddings
        # This runs locally and matches "all-MiniLM-L6-v2"
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
        
        self.collection = self.client.get_or_create_collection(
            name="financial_data",
            embedding_function=self.embedding_fn
        )

    async def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]]):
        """Add texts and metadata to the vector store"""
        if not texts:
            return
            
        # Chroma expects ids
        import uuid
        ids = [str(uuid.uuid4()) for _ in texts]
        
        # Add to collection
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

    async def similarity_search(self, query: str, n_results: int = 5, filter: Dict = None) -> List[Dict]:
        """Search for similar documents"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter
        )
        
        # Format results
        formatted_results = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    "text": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else 0.0
                })
                
        return formatted_results

# Global instance
vector_store = VectorStore()
