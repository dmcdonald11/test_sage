from dotenv import load_dotenv
from agency_swarm import Agency

from sage_agent import sage_agent
from sage_oracle.sage_oracle import sage_oracle
from document_processor import document_processor
import asyncio

load_dotenv()

# do not remove this method, it is used in the main.py file to deploy the agency (it has to be a method)
def create_agency(load_threads_callback=None):
    agency = Agency(
        sage_agent,
        name="SageAgentAgency",
        shared_instructions="sage_agent/instructions.md",
        load_threads_callback=load_threads_callback,
    )

    return agency


if __name__ == "__main__":
    agency = create_agency()

    # test 1 message
    # async def main():
    #     response = await agency.get_response("Hello, how are you?")
    #     print(response)
    # asyncio.run(main())

    # run in terminal
    agency.terminal_demo()