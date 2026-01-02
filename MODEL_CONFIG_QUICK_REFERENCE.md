# Model Configuration - Quick Reference

## 🎯 Quick Setup

Add to your `.env` file:

```bash
# Choose: HuggingFace (free) or OpenAI (paid)
MODEL_SOURCE=HuggingFace

# For HuggingFace:
TOKENIZER_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_CHUNK_TOKENS=512

# For OpenAI (also add):
# TOKENIZER_MODEL=cl100k_base
# EMBEDDING_MODEL=text-embedding-3-small
# MAX_CHUNK_TOKENS=8191
# OPENAI_API_KEY=sk-...
```

## 📊 Model Comparison

| Feature | HuggingFace | OpenAI |
|---------|-------------|--------|
| **Cost** | Free | ~$0.02 per 1M tokens |
| **Location** | Local | API/Cloud |
| **Speed** | Medium | Fast |
| **Quality** | Good | Excellent |
| **Rate Limits** | None | Yes (tier-based) |
| **Setup** | Download models | API key only |

## 🔧 Common Configurations

### Small & Fast (Development)
```bash
MODEL_SOURCE=HuggingFace
TOKENIZER_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_CHUNK_TOKENS=256
```
- ⚡ Fastest processing
- 💾 Small memory footprint
- ✅ Good for testing

### Balanced (Recommended)
```bash
MODEL_SOURCE=HuggingFace
TOKENIZER_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_CHUNK_TOKENS=512
```
- ⚖️ Good speed/quality balance
- 💰 Free
- ✅ Production-ready

### High Quality (Production)
```bash
MODEL_SOURCE=HuggingFace
TOKENIZER_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
MAX_CHUNK_TOKENS=512
```
- 🎯 Best quality (free)
- 🐌 Slower processing
- ✅ Best for accuracy

### Cloud-Based (Enterprise)
```bash
MODEL_SOURCE=OpenAI
TOKENIZER_MODEL=cl100k_base
EMBEDDING_MODEL=text-embedding-3-small
MAX_CHUNK_TOKENS=8191
OPENAI_API_KEY=sk-...
```
- ☁️ No local compute needed
- 💰 Pay per use
- ⚡ Fast API response

## 🚦 Test Your Config

```bash
python test_model_config.py
```

Expected output:
```
✓ Configuration loaded successfully
✓ HuggingFace tokenizer loaded
✓ OpenAI tokenizer loaded
✓ HuggingFace embeddings loaded
```

## 📚 Popular Models

### HuggingFace Models

| Model | Dimensions | Speed | Quality | Use Case |
|-------|-----------|-------|---------|----------|
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | ⚡⚡⚡ | ⭐⭐⭐ | Development |
| `BAAI/bge-small-en-v1.5` | 384 | ⚡⚡⚡ | ⭐⭐⭐⭐ | Balanced |
| `BAAI/bge-base-en-v1.5` | 768 | ⚡⚡ | ⭐⭐⭐⭐ | Production |
| `BAAI/bge-large-en-v1.5` | 1024 | ⚡ | ⭐⭐⭐⭐⭐ | High Quality |

### OpenAI Models

| Model | Dimensions | Cost/1M tokens | Use Case |
|-------|-----------|----------------|----------|
| `text-embedding-3-small` | 1536 | $0.02 | Cost-effective |
| `text-embedding-3-large` | 3072 | $0.13 | Best quality |
| `text-embedding-ada-002` | 1536 | $0.10 | Legacy |

### OpenAI Tokenizers

| Encoding | Max Tokens | Used By |
|----------|-----------|---------|
| `cl100k_base` | 8191 | GPT-4, GPT-3.5-turbo |
| `p50k_base` | 2048 | Codex, text-davinci-002 |
| `r50k_base` | 2048 | GPT-3 (davinci) |

## ⚠️ Troubleshooting

### "Model not found"
- Check model name spelling
- Verify model exists on HuggingFace Hub
- Check internet connection for download

### "Out of memory"
- Reduce `MAX_CHUNK_TOKENS`
- Use smaller model (e.g., `all-MiniLM-L6-v2`)
- Consider OpenAI API instead

### "Slow performance"
- Use smaller model
- Reduce `MAX_CHUNK_TOKENS`
- Enable GPU (for HuggingFace)
- Consider OpenAI API

### "OpenAI API error"
- Verify `OPENAI_API_KEY` is set correctly
- Check API credits
- Verify model name is correct

## 🔗 Documentation

- **Full Guide**: [ENV_CONFIGURATION.md](ENV_CONFIGURATION.md)
- **Technical Docs**: [docs/MODEL_CONFIGURATION.md](docs/MODEL_CONFIGURATION.md)
- **Changes**: [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)
- **Test**: [test_model_config.py](test_model_config.py)

## 💡 Pro Tips

1. **Start with defaults** - They work well for most cases
2. **Test locally** - Use HuggingFace for development
3. **Scale with OpenAI** - Switch to API for production if needed
4. **Monitor costs** - Track OpenAI usage through dashboard
5. **Optimize chunks** - Adjust `MAX_CHUNK_TOKENS` based on your content

---

**Need help?** Check [ENV_CONFIGURATION.md](ENV_CONFIGURATION.md) for detailed explanations.

