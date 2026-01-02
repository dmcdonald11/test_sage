from agents import ModelSettings
from openai.types.shared import Reasoning
from agency_swarm import Agent


document_processor = Agent(
    name="DocumentProcessor",
    description="An intelligent document processing agent that crawls websites, parses multiple document formats using Docling, performs hybrid chunking, generates embeddings, and provides semantic search over stored content.",
    instructions="./instructions.md",
    tools_folder="./tools",
    files_folder="./files",
    model="gpt-5",
    model_settings=ModelSettings(
        max_tokens=25000,
        reasoning=Reasoning(
            effort="medium",
            summary="auto",
        ),
    ),
)

