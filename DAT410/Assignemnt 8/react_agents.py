from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
import argparse

from rich import print as pp

from utils import save_graph

from prompts import (
    SUPERVISOR_SYSTEM_PROMPT,
    RESEARCH_SYSTEM_PROMPT,
    VISA_SYSTEM_PROMPT,
    TRANSPORT_SYSTEM_PROMPT,
    ACCOMMODATION_SYSTEM_PROMPT,
    CULINARY_SYSTEM_PROMPT,
    FINANCE_SYSTEM_PROMPT,
    ITINERARY_SYSTEM_PROMPT,
)

from tools import (
    web_search,
    get_weather,
    get_current_datetime,
    itinerary_generator,
)

llm = ChatOpenAI(
    model="gpt-4o-mini"
) # just use the same model for all

# specialised react agents for multi-agent setup

research_agent = create_react_agent(
    model=llm,
    tools=[web_search, get_weather, get_current_datetime],
    name="research_agent",
    prompt=RESEARCH_SYSTEM_PROMPT,
)

visa_agent = create_react_agent(
    model=llm,
    tools=[web_search, get_current_datetime],
    name="visa_agent",
    prompt=VISA_SYSTEM_PROMPT,
)

transport_agent = create_react_agent(
    model=llm,
    tools=[web_search, get_current_datetime],
    name="transport_agent",
    prompt=TRANSPORT_SYSTEM_PROMPT,
)

accommodation_agent = create_react_agent(
    model=llm,
    tools=[web_search, get_current_datetime],
    name="accommodation_agent",
    prompt=ACCOMMODATION_SYSTEM_PROMPT,
)

culinary_agent = create_react_agent(
    model=llm,
    tools=[web_search, get_current_datetime],
    name="culinary_agent",
    prompt=CULINARY_SYSTEM_PROMPT,
)

finance_agent = create_react_agent(
    model=llm,
    tools=[web_search, get_current_datetime],
    name="finance_agent",
    prompt=FINANCE_SYSTEM_PROMPT,
)

itinerary_agent = create_react_agent(
    model=llm,
    tools=[itinerary_generator],
    name="itinerary_agent",
    prompt=ITINERARY_SYSTEM_PROMPT,
)

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    dry_run = args.dry_run
    content = """
        I am planning a trip to Gothenburg, Sweden. I am a vegetarian and love to try local cuisines, see historical sites, and enjoy the outdoors. I am looking for a 5-day trip with a budget of $2000. Can you help me plan my trip? I am from Singapore and will be traveling in September.
    """ 

    if not dry_run:
        response = generate_itinerary.invoke(
            {"messages": [{"role": "user", "content": content}]},
            {
                "configurable": {
                    "thread_id": "thread-1",
                    "recursion_limit": 999,
                    "initial_agent": "visa_agent",
                }
            },
            debug=1,
        )

        for m in response["messages"]:
            m.pretty_print()
    else:
        pp("🗺 Draw graph")
        save_graph(
            generate_itinerary.get_graph(),
            "itinerary_graph_2.png",
        )