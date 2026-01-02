from agency_swarm.tools import BaseTool
from pydantic import Field
import os
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()


class ListCollections(BaseTool):
    """
    Lists all available collections in the vector database along with their chunk counts.
    Provides an overview of stored document collections for easy navigation and management.
    """
    
    def run(self):
        """
        Execute the list collections query.
        """
        try:
            # Run the async query
            collections = asyncio.run(self._list_collections())
            
            return json.dumps({
                "success": True,
                "collections_count": len(collections),
                "collections": collections
            }, indent=2)
        
        except Exception as e:
            error_result = {
                "success": False,
                "error": type(e).__name__,
                "message": str(e)
            }
            return json.dumps(error_result, indent=2)
    
    async def _list_collections(self):
        """
        Query PostgreSQL for all collections.
        """
        import asyncpg
        
        # Connect to PostgreSQL
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "vector_store"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )
        
        try:
            # Query distinct collections with chunk counts
            results = await conn.fetch(
                """
                SELECT 
                    collection_name,
                    COUNT(*) as chunk_count,
                    COUNT(DISTINCT source_url) as unique_sources,
                    MIN(created_at) as first_added,
                    MAX(created_at) as last_added
                FROM document_chunks
                GROUP BY collection_name
                ORDER BY collection_name
                """
            )
            
            # Format results
            collections = []
            for row in results:
                collections.append({
                    "name": row["collection_name"],
                    "chunk_count": row["chunk_count"],
                    "unique_sources": row["unique_sources"],
                    "first_added": row["first_added"].isoformat() if row["first_added"] else None,
                    "last_added": row["last_added"].isoformat() if row["last_added"] else None
                })
            
            return collections
        
        finally:
            await conn.close()


if __name__ == "__main__":
    # Test the tool
    # Note: Requires PostgreSQL with pgvector and existing data
    tool = ListCollections()
    
    print("Testing ListCollections tool...")
    print("Note: This requires PostgreSQL with pgvector and existing document chunks.")
    print(tool.run())

