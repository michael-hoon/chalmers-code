from datetime import datetime
from loguru import logger
from typing import List
from langchain_community.tools.tavily_search import TavilySearchResults
import requests
from pydantic import Field
import os
from rich.console import Console
from rich.markdown import Markdown

from dotenv import load_dotenv
load_dotenv()

WEATHER_API_KEY = os.environ['WEATHER_API_KEY']
TAVILY_API_KEY = os.environ['TAVILY_API_KEY']

def get_current_datetime() -> str:
    """
    Useful for getting the current datetime, to reference current date when planning events.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"🧭 Retrieved current time: {current_time}")
    return current_time

def web_search(
        query: str = Field(description="The mandatory query to search on the web.")
    ) -> str:
    """
    Search for general web results.

    This function performs a search using the Tavily AI search engine, which is designed
    to provide comprehensive, accurate, and trusted results. 
    The maximum number of results is 5, and we return the combined content of all results as a single string.
    """
    logger.info(f"🔍 Searching on web: \n{query}")
    tavily_search = TavilySearchResults(
        api_key=TAVILY_API_KEY, 
        max_results=5, 
        search_depth='advanced', 
        max_tokens=1000)
    
    results = tavily_search.invoke(query)
    return "\n\n".join([result['content'] for result in results])

def get_weather(
        query: str
    ) -> List:
    """
    Search WeatherAPI to get the weather for a city.
    """
    endpoint = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={query}&aqi=no"
    response = requests.get(endpoint)
    data = response.json()

    if data.get("location"):
        return data
    else:
        return "Weather Data Not Found for the given location."

def itinerary_generator(
    itinerary_content: str = Field(description="The content of the generated itinerary."),
):
    """
    The useful tool that the itinerary_agent uses to write and store the itinerary content, in markdown format.
    """
    logger.info("📄 generating_itinerary")

    console = Console(record=True, soft_wrap=True)
    md = Markdown(str(itinerary_content), justify="left")
    console.print(md)

    file_fullname = "final_itinerary.md"
    with open(file_fullname, "w") as f:
        f.write(itinerary_content)