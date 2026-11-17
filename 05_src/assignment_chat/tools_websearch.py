
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain.tools import tool
from dotenv import load_dotenv
import json
from pydantic import BaseModel, Field, tools
from utils.clients import get_client

from langchain_tavily import TavilySearch
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from math_tools import get_math_tool

sys.path.append('../05_src/')

# _logs = get_logger(__name__)
load_dotenv("../05_src/.env")
load_dotenv("../05_src/.secrets")


@tool
def search_web(query: str):
    """
    Performs a web search using the TavilySearch tool.
    """
    search = TavilySearch(
        max_results=1,
        name="search",
        description='search(query="the search query") - a search engine.',
    )
    response = search.invoke({"query": query})
    return response


# response = search_web.invoke({"query": "When is the best time to visit Alaska?"})
# print(response)