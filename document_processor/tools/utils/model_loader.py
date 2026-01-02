"""
Utility module for loading tokenizers and embedding models based on MODEL_SOURCE.
Supports HuggingFace, OpenAI, and other model sources.
"""

import os
from pathlib import Path
from typing import Any, Tuple
from dotenv import load_dotenv

# Load .env from project root (works regardless of where module is imported from)
_env_path = Path(__file__).parent.parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()  # Fallback to default behavior


def get_tokenizer(model_name: str = None, model_source: str = None):
    """
    Load a tokenizer based on the model source.
    
    Args:
        model_name: The model name/identifier. If None, uses TOKENIZER_MODEL from env
        model_source: The source of the model (HuggingFace, OpenAI, etc.). If None, uses MODEL_SOURCE from env
        
    Returns:
        A tokenizer instance compatible with the chunking process
    """
    # Get configuration from environment if not provided
    if model_name is None:
        model_name = os.getenv("TOKENIZER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    if model_source is None:
        model_source = os.getenv("MODEL_SOURCE", "HuggingFace")
    
    # Normalize model source
    model_source = model_source.lower().strip()
    
    # Load appropriate tokenizer based on source
    if model_source in ["huggingface", "hf", "hugging_face"]:
        # Use HuggingFace transformers tokenizer
        from transformers import AutoTokenizer
        return AutoTokenizer.from_pretrained(model_name)
    
    elif model_source in ["openai", "tiktoken"]:
        # Use OpenAI tokenizer wrapper
        try:
            from .tokenizer import OpenAITokenizerWrapper
        except ImportError:
            # Fallback for when running from different contexts
            from tokenizer import OpenAITokenizerWrapper
        # model_name for OpenAI should be encoding name like "cl100k_base", "p50k_base", etc.
        # Default to cl100k_base if a model name is provided
        encoding_name = model_name if model_name in ["cl100k_base", "p50k_base", "r50k_base", "gpt2"] else "cl100k_base"
        max_length = int(os.getenv("MAX_CHUNK_TOKENS", "8191"))
        return OpenAITokenizerWrapper(model_name=encoding_name, max_length=max_length)
    
    else:
        # Default to HuggingFace for unknown sources
        print(f"Warning: Unknown MODEL_SOURCE '{model_source}', defaulting to HuggingFace")
        from transformers import AutoTokenizer
        return AutoTokenizer.from_pretrained(model_name)


def get_embedding_model(model_name: str = None, model_source: str = None):
    """
    Load an embedding model based on the model source.
    
    Args:
        model_name: The model name/identifier. If None, uses EMBEDDING_MODEL from env
        model_source: The source of the model (HuggingFace, OpenAI, etc.). If None, uses MODEL_SOURCE from env
        
    Returns:
        An embedding model instance
    """
    # Get configuration from environment if not provided
    if model_name is None:
        model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    if model_source is None:
        model_source = os.getenv("MODEL_SOURCE", "HuggingFace")
    
    # Normalize model source
    model_source = model_source.lower().strip()
    
    # Get max chunk tokens from environment
    max_chunk_tokens = int(os.getenv("MAX_CHUNK_TOKENS", "512"))
    
    # Load appropriate embedding model based on source
    if model_source in ["huggingface", "hf", "hugging_face"]:
        # Use sentence-transformers
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_name)
        model.max_seq_length = max_chunk_tokens
        return model
    
    elif model_source in ["openai"]:
        # Use OpenAI embeddings API
        import openai
        from openai import OpenAI
        
        # Return a wrapper object that mimics SentenceTransformer interface
        class OpenAIEmbeddingWrapper:
            def __init__(self, model_name: str, max_seq_length: int):
                self.model_name = model_name
                self.max_seq_length = max_seq_length
                self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                # Get tokenizer for this model
                self.tokenizer = get_tokenizer(model_name="cl100k_base", model_source="OpenAI")
            
            def encode(self, texts, show_progress_bar=False, batch_size=32, 
                      normalize_embeddings=False, convert_to_numpy=True):
                """Generate embeddings using OpenAI API"""
                import numpy as np
                
                # Handle single text
                if isinstance(texts, str):
                    texts = [texts]
                
                # Batch the requests
                all_embeddings = []
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    
                    # Call OpenAI API
                    response = self.client.embeddings.create(
                        model=self.model_name,
                        input=batch
                    )
                    
                    # Extract embeddings
                    batch_embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(batch_embeddings)
                
                # Convert to numpy if requested
                if convert_to_numpy:
                    all_embeddings = np.array(all_embeddings)
                
                # Normalize if requested
                if normalize_embeddings and convert_to_numpy:
                    norms = np.linalg.norm(all_embeddings, axis=1, keepdims=True)
                    all_embeddings = all_embeddings / norms
                
                return all_embeddings
        
        # Common OpenAI embedding model names
        if model_name not in ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"]:
            print(f"Warning: '{model_name}' may not be a valid OpenAI embedding model. Common models: text-embedding-3-small, text-embedding-3-large")
        
        return OpenAIEmbeddingWrapper(model_name=model_name, max_seq_length=max_chunk_tokens)
    
    else:
        # Default to HuggingFace for unknown sources
        print(f"Warning: Unknown MODEL_SOURCE '{model_source}', defaulting to HuggingFace")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_name)
        model.max_seq_length = max_chunk_tokens
        return model


def get_model_config() -> Tuple[str, str, str, int]:
    """
    Get model configuration from environment variables.
    
    Returns:
        A tuple of (tokenizer_model, embedding_model, model_source, max_chunk_tokens)
    """
    tokenizer_model = os.getenv("TOKENIZER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    model_source = os.getenv("MODEL_SOURCE", "HuggingFace")
    max_chunk_tokens = int(os.getenv("MAX_CHUNK_TOKENS", "512"))
    
    # Debug output
    print(f"[DEBUG] get_model_config() loaded:")
    print(f"  MODEL_SOURCE: {model_source}")
    print(f"  TOKENIZER_MODEL: {tokenizer_model}")
    print(f"  EMBEDDING_MODEL: {embedding_model}")
    print(f"  MAX_CHUNK_TOKENS: {max_chunk_tokens}")
    
    return tokenizer_model, embedding_model, model_source, max_chunk_tokens

