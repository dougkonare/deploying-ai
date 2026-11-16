from langgraph.graph import StateGraph, MessagesState, START
from langchain.chat_models import init_chat_model
from langgraph.prebuilt.tool_node import ToolNode, tools_condition
from langchain_core.messages import SystemMessage,  HumanMessage

from dotenv import load_dotenv
import json
import requests
import os

from assignment_chat.prompts import return_instructions_root
from assignment_chat.tools_rag_hotels import query_hotels
from assignment_chat.tools_api_weather import get_current_weather_data
from assignment_chat.tools_websearch import search_web
from utils.logger import get_logger
from utils.clients import get_client


_logs = get_logger(__name__)
# load_dotenv(".env")
# load_dotenv(".secrets")

load_dotenv(".env")
load_dotenv(".secrets")

chat_agent = init_chat_model(
    "openai:gpt-4o-mini",
    temperature=1,
    base_url='https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1',
    api_key='any value',
    default_headers={"x-api-key": os.getenv('API_GATEWAY_KEY')}
    
)
tools = [query_hotels, get_current_weather_data, search_web]

instructions = return_instructions_root()


# @traceable(run_type="llm")
def call_model(state: MessagesState):
    """LLM decides whether to call a tool or not"""
    response = chat_agent.bind_tools(tools).invoke( [SystemMessage(content=instructions)] + state["messages"])
    return {
        "messages": [response]
    }

def get_graph():
    
    builder = StateGraph(MessagesState)
    builder.add_node(call_model)
    builder.add_node(ToolNode(tools))
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges(
        "call_model",
        tools_condition,
    )
    builder.add_edge("tools", "call_model")
    graph = builder.compile()
    return graph

