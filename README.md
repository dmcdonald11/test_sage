# Document Processing Agency

A production-ready Agency Swarm implementation for intelligent web document processing and semantic search. This agency crawls websites, parses multiple document formats using Docling, performs hybrid chunking, generates embeddings, and stores content in PostgreSQL with pgvector for RAG applications.

**🌐 [Agencii](https://agencii.ai/)** - The official cloud platform for Agency Swarm deployments  
**🔗 [GitHub App](https://github.com/apps/agencii)** - Automated deployment integration

---

## 🎯 Features

- **🌐 Web Crawling**: Intelligent web crawling with automatic document discovery
- **📄 Multi-Format Parsing**: Support for 12+ document formats (PDF, DOCX, XLSX, PPTX, HTML, Markdown, Images, Audio, CSV, XML, VTT, JSON)
- **🧩 Hybrid Chunking**: Structure-aware chunking with token limits using Docling
- **🔢 Vector Embeddings**: Semantic embeddings with sentence-transformers
- **🎛️ Flexible Model Configuration**: Choose between HuggingFace (free) or OpenAI (paid) models
- **💾 Vector Storage**: PostgreSQL with pgvector for efficient similarity search
- **🔍 Semantic Search**: Find content by meaning, not just keywords
- **🏗️ Production Ready**: Docker containerization and automated deployment

---

## 🚀 Quick Start

### 1. Use This Template

Click **"Use this template"** to create your own repository, or:

```bash
git clone https://github.com/your-username/agency-github-template.git
cd agency-github-template
```

> **🌐 For Production**: Sign up at [agencii.ai](https://agencii.ai/) and use this template for automated cloud deployment

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up PostgreSQL with pgvector

This agency requires PostgreSQL with the pgvector extension:

```bash
# Using Docker (recommended for development)
docker run -d \
  --name postgres-vector \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=vector_store \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Or install locally:
# 1. Install PostgreSQL 12+
# 2. Install pgvector extension: https://github.com/pgvector/pgvector
```

### 4. Set Up Environment Variables

Create a `.env` file and configure:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=vector_store
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password

# Model Configuration (New!)
# Choose your model source: HuggingFace (free, local) or OpenAI (paid, API)
MODEL_SOURCE=HuggingFace

# Tokenizer Model
# HuggingFace: sentence-transformers/all-MiniLM-L6-v2, BAAI/bge-small-en-v1.5
# OpenAI: cl100k_base, p50k_base
TOKENIZER_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Embedding Model
# HuggingFace: sentence-transformers/all-MiniLM-L6-v2, BAAI/bge-large-en-v1.5
# OpenAI: text-embedding-3-small, text-embedding-3-large
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Chunking Configuration
MAX_CHUNK_TOKENS=512  # Maximum tokens per chunk (default: 512)
```

> 📖 **For detailed model configuration options**, see [ENV_CONFIGURATION.md](ENV_CONFIGURATION.md)

### 5. Test the Document Processing Agency

```bash
python agency.py
```

This runs the agency in terminal mode. You can interact with it using natural language:

**Example Commands:**
- "Process this URL: https://docling-project.github.io/docling/"
- "Search for information about document parsing"
- "List all collections in the database"

---

## 🛠️ Agency Capabilities

### DocumentProcessor Agent

The DocumentProcessor agent provides three main tools:

1. **CrawlAndProcessUrl**: Crawls a URL, discovers documents, parses them with Docling, chunks content, generates embeddings, and stores in PostgreSQL
   - Supports 12+ document formats
   - Automatic document discovery from web pages
   - Hybrid chunking preserves document structure
   - Configurable embedding models and chunk sizes

2. **SearchSimilarChunks**: Performs semantic similarity search on stored documents
   - Vector-based retrieval using cosine similarity
   - Filter by collection name
   - Configurable top-k results and similarity threshold
   - Returns chunks with source metadata and context

3. **ListCollections**: Lists all document collections with statistics
   - Shows chunk counts per collection
   - Displays unique source counts
   - Provides creation/update timestamps

---

## 🏗️ Project Structure

```
agency-github-template/
├── agency.py                 # Main entry point
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container configuration
├── .env                     # Environment variables (create this)
├── example_agent/           # Your agency folder
    ├── __init__.py
    ├── example_agent.py
    ├── instructions.md
    ├── files/               # Local files accessible to the agent (via files_folder)
    └── tools/
        └── ExampleTool.py
├── example_agent2/
├── agency_manifesto.md  # Shared instructions
├── requirements.txt
├── .env
└──...
```

---

## 🔧 Creating Your Own Agency

### 🤖 **AI-Assisted Agency Creation with Cursor**

This template includes **AI-powered agency creation** using Cursor IDE:

1. **Open this project in Cursor IDE**

2. **Use the AI Assistant** to create your agency by referencing:
   ```
   📁 .cursor/rules/workflow.mdc
   ```
3. **Simply ask the AI:**

   > "Create a new agency using the .cursor workflow"

   The AI will guide you through the complete 7-step process:

   - ✅ PRD Creation
   - ✅ Folder Structure Setup
   - ✅ Tool Development
   - ✅ Agent Creation
   - ✅ Agency Configuration
   - ✅ Testing & Validation
   - ✅ Iteration & Refinement

### 📋 **What the AI Will Do For You**

The AI assistant will automatically:

- Create proper folder structures
- Generate agent classes and instructions
- Build custom tools with full functionality
- Set up communication flows
- Create the main agency file
- Test everything to ensure it works

### 🚀 **Manual Alternative (Advanced Users)**

If you prefer manual setup, replace the `ExampleAgency/` folder with your own agency structure following the Agency Swarm conventions.

### Agency Structure Requirements

Your agency must follow this structure:

- **Agency Folder**: Contains all agents and manifesto
- **Agent Folders**: Each agent has its own folder with:
  - `AgentName.py` - Agent class definition
  - `instructions.md` - Agent-specific instructions
  - `tools/` - Folder containing agent tools
- **agency_manifesto.md** - Shared instructions for all agents

---

## 🚀 Production Deployment with Agencii

### **🌐 Deploy to Agencii Cloud Platform**

For production deployment, use the [Agencii](https://agencii.ai/) platform:

#### **Step 1: Create Account & Use Template**

1. **Sign up** at [agencii.ai](https://agencii.ai/)
2. **Use this template** to create your repository
3. **Develop your agency** using Cursor IDE with `.cursor` workflow

#### **Step 2: Install GitHub App**

1. **Install** the [Agencii GitHub App](https://github.com/apps/agencii)
2. **Grant permissions** to your repository
3. **Configure** environment variables in Agencii dashboard

#### **Step 3: Deploy**

1. **Push to main branch** - Agencii automatically detects and deploys
2. **Monitor deployment** in your Agencii dashboard
3. **Access your live agency** via provided endpoints

### **🔄 Automatic Deployments**

- **Auto-deploy** on every push to `main` branch
- **Zero-downtime** deployments with rollback capability
- **Environment management** through Agencii dashboard

---

## 🔨 Development Workflow

### **🎯 Recommended: AI-Assisted Development**

1. **Open Cursor IDE** with this template
2. **Ask the AI**: _"Create a new agency using the .cursor workflow"_
3. **Follow the guided process** - the AI handles everything automatically
4. **Test your agency**: `python agency.py`
5. **Deploy to production**: Install [Agencii GitHub App](https://github.com/apps/agencii) and push to main

### **⚙️ Manual Development (Advanced)**

If you prefer hands-on development:

1. **Create Tools**: Build agent tools in `tools/` folders
2. **Configure Agents**: Write `instructions.md` and agent classes
3. **Test Locally**: Run `python agency.py`
4. **Deploy**: Push to your preferred platform

The `.cursor/rules/workflow.mdc` file contains the complete development specifications for manual implementation.

---

## 📚 Key Features

- **🌐 Agencii Cloud Deploy**: One-click deployment to [Agencii platform](https://agencii.ai/)
- **🤖 AI-Assisted Creation**: Built-in Cursor IDE workflow for automated agency development
- **🔄 Auto-Deploy**: Automatic deployment on push to main branch
- **🚀 Ready-to-Deploy**: Dockerfile and requirements included
- **🔧 Modular Structure**: Easy to customize and extend
- **🛠️ Example Implementation**: Complete working example
- **📦 Container Ready**: Docker configuration for any platform
- **🔒 Environment Management**: Secure API key handling via Agencii dashboard
- **🧪 Local Testing**: Terminal demo for development
- **📋 Guided Workflow**: 7-step process with AI assistance

---

## 📖 Learn More

- **[Agency Swarm Documentation](https://agency-swarm.ai/)**
- **[Agency Swarm GitHub](https://github.com/VRSEN/agency-swarm)**

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## ⚡ Quick Tips

- **Start Small**: Begin with 1-2 agents and expand
- **Test Tools**: Each tool should work independently
- **Clear Instructions**: Write detailed agent instructions
- **Environment Setup**: Always use `.env` for API keys
- **Documentation**: Update instructions as you develop

---

**Ready to build your AI agency?** 🤖✨

### 🌐 **Production Route (Recommended)**

1. **Sign up** at [agencii.ai](https://agencii.ai/)
2. **Use this template** to create your repository
3. **Install** [Agencii GitHub App](https://github.com/apps/agencii)
4. **Push to main** → Automatic deployment!

### 🛠️ **Development Route**

Open this template in **Cursor IDE** and ask the AI to create your agency using the `.cursor` workflow. The AI will handle everything from setup to testing automatically!

For manual development, replace the `ExampleAgency` with your own implementation and start deploying intelligent agent systems!
