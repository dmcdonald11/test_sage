from agents import ModelSettings
from openai.types.shared import Reasoning
from agency_swarm import Agent


sage_agent = Agent(
    name="SageAgent",
    description="A specialized agent for web crawling, document processing, and knowledge extraction. Capable of crawling documentation sites, regular web pages, converting PDF documents to markdown, and extracting structured content using advanced processing strategies.",
    instructions="./instructions.md",
    tools_folder="./tools",
    files_folder="./files",
    model="o4-mini",
    model_settings=ModelSettings(
        max_tokens=25000,
        reasoning=Reasoning(
            effort="medium",
            summary="auto",
        ),
    ),
)

