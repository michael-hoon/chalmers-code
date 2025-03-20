from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph_supervisor import create_supervisor
from langchain_openai import ChatOpenAI

from utils.prompts import (
    SUPERVISOR_SYSTEM_PROMPT,
)

from utils.react_agents import (
    research_agent,
    visa_agent,
    transport_agent,
    accommodation_agent,
    culinary_agent,
    finance_agent,
    itinerary_agent,
)

from utils.tools import (
    get_current_datetime,
)

llm = ChatOpenAI(
    model="gpt-4o-mini"
) # just use the same model for all

## Agent callback tools ########################################################
checkpointer = MemorySaver() # langgraph in-built persistence layer for conversations, unique thread id
store = InMemoryStore() # memory store across threads

overall_supervisor = create_supervisor(
    agents=[
        research_agent,
        visa_agent,
        transport_agent,
        accommodation_agent,
        culinary_agent,
        finance_agent,
        itinerary_agent,
    ],
    model=llm,
    # supervisor_name="ItinerarySupervisor", # default is "supervisor"
    tools=[
        get_current_datetime,
    ],
    prompt=SUPERVISOR_SYSTEM_PROMPT,
)

generate_itinerary = overall_supervisor.compile(
    name="ItinerarySupervisor",
    checkpointer=checkpointer,
    store=store,
)