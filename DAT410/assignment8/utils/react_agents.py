from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

from .prompts import (
    SUPERVISOR_SYSTEM_PROMPT,
    RESEARCH_SYSTEM_PROMPT,
    VISA_SYSTEM_PROMPT,
    TRANSPORT_SYSTEM_PROMPT,
    ACCOMMODATION_SYSTEM_PROMPT,
    CULINARY_SYSTEM_PROMPT,
    FINANCE_SYSTEM_PROMPT,
    ITINERARY_SYSTEM_PROMPT,
)

from .tools import (
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
