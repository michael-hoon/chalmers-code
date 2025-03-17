from dotenv import load_dotenv
import os

load_dotenv()

from langgraph.graph import StateGraph, START, END

from state import (
    OverallState,
)

from react_agents import (
    generate_itinerary
)

from utils import (
    save_graph
)

# generate graph for visualisation

save_graph(
    generate_itinerary.get_graph(), 
    "itinerary_graph.png",
)