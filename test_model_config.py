"""
Test script for model configuration system.
This script tests the model loader utilities and verifies different configurations work correctly.
"""

import os
import sys
from pathlib import Path

# Add document_processor path
doc_processor_path = Path(__file__).parent / "document_processor" / "tools"
sys.path.insert(0, str(doc_processor_path))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_model_config():
    """Test getting model configuration from environment."""
    from utils.model_loader import get_model_config
    
    print("=" * 80)
    print("Testing Model Configuration")
    print("=" * 80)
    
    tokenizer_model, embedding_model, model_source, max_chunk_tokens = get_model_config()
    
    print(f"\n✓ Configuration loaded successfully:")
    print(f"  Model Source: {model_source}")
    print(f"  Tokenizer Model: {tokenizer_model}")
    print(f"  Embedding Model: {embedding_model}")
    print(f"  Max Chunk Tokens: {max_chunk_tokens}")
    print()
    
    return model_source, tokenizer_model, embedding_model


def test_huggingface_tokenizer():
    """Test loading HuggingFace tokenizer."""
    from utils.model_loader import get_tokenizer
    
    print("=" * 80)
    print("Testing HuggingFace Tokenizer")
    print("=" * 80)
    
    try:
        tokenizer = get_tokenizer(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_source="HuggingFace"
        )
        
        # Test tokenization
        test_text = "This is a test sentence for tokenization."
        tokens = tokenizer.encode(test_text, add_special_tokens=False)
        
        print(f"\n✓ HuggingFace tokenizer loaded successfully")
        print(f"  Model: sentence-transformers/all-MiniLM-L6-v2")
        print(f"  Test text: '{test_text}'")
        print(f"  Token count: {len(tokens)}")
        print()
        
        return True
    except Exception as e:
        print(f"\n✗ Failed to load HuggingFace tokenizer: {str(e)}")
        print()
        return False


def test_openai_tokenizer():
    """Test loading OpenAI tokenizer."""
    from utils.model_loader import get_tokenizer
    
    print("=" * 80)
    print("Testing OpenAI Tokenizer")
    print("=" * 80)
    
    try:
        tokenizer = get_tokenizer(
            model_name="cl100k_base",
            model_source="OpenAI"
        )
        
        # Test tokenization
        test_text = "This is a test sentence for tokenization."
        tokens = tokenizer.tokenize(test_text)
        
        print(f"\n✓ OpenAI tokenizer loaded successfully")
        print(f"  Encoding: cl100k_base")
        print(f"  Test text: '{test_text}'")
        print(f"  Token count: {len(tokens)}")
        print()
        
        return True
    except Exception as e:
        print(f"\n✗ Failed to load OpenAI tokenizer: {str(e)}")
        print()
        return False


def test_huggingface_embeddings():
    """Test loading HuggingFace embedding model."""
    from utils.model_loader import get_embedding_model
    
    print("=" * 80)
    print("Testing HuggingFace Embedding Model")
    print("=" * 80)
    
    try:
        model = get_embedding_model(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_source="HuggingFace"
        )
        
        # Test embedding generation
        test_texts = ["This is a test sentence.", "Another test sentence."]
        embeddings = model.encode(test_texts, convert_to_numpy=True)
        
        print(f"\n✓ HuggingFace embedding model loaded successfully")
        print(f"  Model: sentence-transformers/all-MiniLM-L6-v2")
        print(f"  Test texts: {len(test_texts)}")
        print(f"  Embedding shape: {embeddings.shape}")
        print(f"  Embedding dimension: {embeddings.shape[1]}")
        print()
        
        return True
    except Exception as e:
        print(f"\n✗ Failed to load HuggingFace embedding model: {str(e)}")
        print()
        return False


def test_openai_embeddings():
    """Test loading OpenAI embedding model."""
    from utils.model_loader import get_embedding_model
    
    print("=" * 80)
    print("Testing OpenAI Embedding Model")
    print("=" * 80)
    
    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠ Skipping OpenAI embedding test: OPENAI_API_KEY not set")
        print()
        return None
    
    try:
        model = get_embedding_model(
            model_name="text-embedding-3-small",
            model_source="OpenAI"
        )
        
        # Test embedding generation
        test_texts = ["This is a test sentence."]
        embeddings = model.encode(test_texts, convert_to_numpy=True)
        
        print(f"\n✓ OpenAI embedding model loaded successfully")
        print(f"  Model: text-embedding-3-small")
        print(f"  Test texts: {len(test_texts)}")
        print(f"  Embedding shape: {embeddings.shape}")
        print(f"  Embedding dimension: {embeddings.shape[1]}")
        print()
        
        return True
    except Exception as e:
        print(f"\n✗ Failed to load OpenAI embedding model: {str(e)}")
        print()
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "MODEL CONFIGURATION TEST SUITE" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    results = {}
    
    # Test 1: Model configuration
    try:
        model_source, tokenizer_model, embedding_model = test_model_config()
        results['config'] = True
    except Exception as e:
        print(f"✗ Configuration test failed: {str(e)}")
        results['config'] = False
        return
    
    # Test 2: HuggingFace tokenizer
    results['hf_tokenizer'] = test_huggingface_tokenizer()
    
    # Test 3: OpenAI tokenizer
    results['openai_tokenizer'] = test_openai_tokenizer()
    
    # Test 4: HuggingFace embeddings
    results['hf_embeddings'] = test_huggingface_embeddings()
    
    # Test 5: OpenAI embeddings (optional)
    results['openai_embeddings'] = test_openai_embeddings()
    
    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print()
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    total = len(results)
    
    print(f"Passed:  {passed}/{total - skipped} ✓")
    print(f"Failed:  {failed}/{total - skipped} ✗")
    if skipped > 0:
        print(f"Skipped: {skipped}/{total} ⚠")
    print()
    
    # Detailed results
    for test_name, result in results.items():
        status = "✓ PASS" if result is True else ("✗ FAIL" if result is False else "⚠ SKIP")
        print(f"  {status} - {test_name}")
    
    print()
    print("=" * 80)
    
    if failed == 0:
        print("All tests completed successfully!" if skipped == 0 else "All enabled tests completed successfully!")
    else:
        print(f"⚠ {failed} test(s) failed. Please check the error messages above.")
    
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()

