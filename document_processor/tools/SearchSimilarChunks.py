from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Optional, List, Dict, Any
import os
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()


class SearchSimilarChunks(BaseTool):
    """
    Performs vector similarity search on stored document chunks to find semantically
    similar content. Uses cosine similarity with pgvector for efficient retrieval.
    """
    
    query: str = Field(
        ...,
        description="The search query text to find similar chunks"
    )
    
    collection_name: Optional[str] = Field(
        default=None,
        description="Optional: Filter results by collection name. If None, searches across all collections."
    )
    
    top_k: int = Field(
        default=5,
        description="Number of results to return (default: 5)"
    )
    
    similarity_threshold: float = Field(
        default=0.7,
        description="Minimum similarity score (0-1). Only return results above this threshold (default: 0.7)"
    )
    
    embedding_model: Optional[str] = Field(
        default=None,
        description="Override the default embedding model for query encoding"
    )
    
    def run(self):
        """
        Execute the similarity search.
        """
        try:
            # Validate inputs
            if not self.query or len(self.query.strip()) == 0:
                return json.dumps({
                    "success": False,
                    "error": "ValidationError",
                    "message": "Query cannot be empty"
                }, indent=2)
            
            if self.top_k <= 0:
                return json.dumps({
                    "success": False,
                    "error": "ValidationError",
                    "message": "top_k must be a positive integer"
                }, indent=2)
            
            if not 0 <= self.similarity_threshold <= 1:
                return json.dumps({
                    "success": False,
                    "error": "ValidationError",
                    "message": "similarity_threshold must be between 0 and 1"
                }, indent=2)
            
            # Run the async search
            results = asyncio.run(self._search())
            
            return json.dumps({
                "success": True,
                "query": self.query,
                "collection_name": self.collection_name,
                "results_count": len(results),
                "results": results
            }, indent=2)
        
        except Exception as e:
            error_result = {
                "success": False,
                "error": type(e).__name__,
                "message": str(e),
                "query": self.query
            }
            return json.dumps(error_result, indent=2)
    
    async def _search(self):
        """
        Perform the actual similarity search.
        """
        # Step 1: Generate query embedding
        query_embedding = await self._generate_query_embedding()
        
        # Step 2: Search in PostgreSQL
        results = await self._search_postgres(query_embedding)
        
        return results
    
    async def _generate_query_embedding(self):
        """
        Generate embedding for the search query.
        """
        from .utils.model_loader import get_embedding_model, get_model_config
        
        # Get model configuration from environment
        _, embedding_model_name, model_source, _ = get_model_config()
        
        # Use override if provided, otherwise use env config
        if self.embedding_model:
            embedding_model_name = self.embedding_model
        
        # Load embedding model based on MODEL_SOURCE
        model = get_embedding_model(model_name=embedding_model_name, model_source=model_source)
        
        # Generate embedding
        embedding = model.encode([self.query])  # Pass as list for batch processing
        
        # Handle different return types (numpy array vs list)
        if hasattr(embedding, 'tolist'):
            return embedding[0].tolist()  # Get first item and convert to list
        else:
            return embedding[0]  # Already a list
    
    async def _search_postgres(self, query_embedding):
        """
        Search PostgreSQL using vector similarity.
        """
        import asyncpg
        from pgvector.asyncpg import register_vector
        
        # Connect to PostgreSQL
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "vector_store"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )
        
        try:
            # Register pgvector type
            await register_vector(conn)
            
            # Perform similarity search with or without collection filter
            if self.collection_name:
                results = await conn.fetch(
                    """
                    SELECT 
                        chunk_text,
                        num_tokens,
                        source_url,
                        source_document,
                        doc_type,
                        headings,
                        metadata,
                        collection_name,
                        1 - (embedding <=> $1) as similarity
                    FROM document_chunks
                    WHERE collection_name = $2
                    AND 1 - (embedding <=> $1) >= $3
                    ORDER BY embedding <=> $1
                    LIMIT $4
                    """,
                    query_embedding,
                    self.collection_name,
                    self.similarity_threshold,
                    self.top_k,
                )
            else:
                results = await conn.fetch(
                    """
                    SELECT 
                        chunk_text,
                        num_tokens,
                        source_url,
                        source_document,
                        doc_type,
                        headings,
                        metadata,
                        collection_name,
                        1 - (embedding <=> $1) as similarity
                    FROM document_chunks
                    WHERE 1 - (embedding <=> $1) >= $2
                    ORDER BY embedding <=> $1
                    LIMIT $3
                    """,
                    query_embedding,
                    self.similarity_threshold,
                    self.top_k,
                )
            
            # Convert results to list of dictionaries
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "chunk_text": row["chunk_text"],
                    "num_tokens": row["num_tokens"],
                    "source_url": row["source_url"],
                    "source_document": row["source_document"],
                    "doc_type": row["doc_type"],
                    "headings": json.loads(row["headings"]) if row["headings"] else [],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "collection_name": row["collection_name"],
                    "similarity_score": float(row["similarity"])
                })
            
            return formatted_results
        
        finally:
            await conn.close()


if __name__ == "__main__":
    # Test the tool
    # Note: Requires PostgreSQL with pgvector and existing data
    tool = SearchSimilarChunks(
        query="How to use Docling for document parsing?",
        collection_name="test_collection",
        top_k=5,
        similarity_threshold=0.5
    )
    
    print("Testing SearchSimilarChunks tool...")
    print("Note: This requires PostgreSQL with pgvector and existing document chunks.")
    print(tool.run())

