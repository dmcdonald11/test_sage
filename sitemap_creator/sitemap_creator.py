from agents import ModelSettings
from openai.types.shared import Reasoning
from agency_swarm import Agent


sitemap_creator = Agent(
    name="SitemapCreator",
    description="A specialized agent that crawls websites to discover all URLs and create comprehensive sitemaps by following links up to 5 levels deep.",
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

