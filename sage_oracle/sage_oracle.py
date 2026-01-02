"""
Sage Oracle Agent - Advanced Document Processing and Knowledge Extraction
"""

from agents import ModelSettings
from agency_swarm import Agent
from openai.types.shared import Reasoning

sage_oracle = Agent(
    name="Sage Oracle",
    description="Advanced document processing and knowledge extraction specialist with concurrent processing capabilities, supporting multiple input sources, intelligent chunking, vector embeddings, and comprehensive storage solutions.",
    instructions="./instructions.md",
    tools_folder="./tools",
    files_folder="./files",
    model="gpt-5",
    model_settings=ModelSettings(
        reasoning=Reasoning(
            effort="high",
            summary="auto",
        ),
    ),
)
