import logging
from typing import Annotated, Literal, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from IPython.display import Image, display
from langchain_google_genai import ChatGoogleGenerativeAI
from PIL import Image
from io import BytesIO
from langchain_community.tools.tavily_search import TavilySearchResults

# Setup basic logging configuration
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()


# Define the tools for the agent to use
@tool
def search(query: str):
    """Call to surf the web."""
    logging.info(f"Tool 'search' called with query: {query}")
    # This is a placeholder, but don't tell the LLM that...
    if "taipei" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


# tools = [search]

# Initialize TavilySearchResults tool (replace custom search tool)
web_search_tool = TavilySearchResults(k=3)
tools = [web_search_tool]
tool_node = ToolNode(tools)

## ChatGoogleGenerativeAI
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash").bind_tools(tools)


# Define the function that determines whether to continue or not
def should_continue(state: MessagesState) -> Literal["tools", END]:
    messages = state["messages"]
    last_message = messages[-1]
    logging.info(f"Last message in state: {last_message.content}")
    # If the LLM makes a tool call, then we route to the "tools" node
    if last_message.tool_calls:
        logging.info("Routing to 'tools' node")
        return "tools"
    # Otherwise, we stop (reply to the user)
    logging.info("Stopping at END")
    return END


# Define the function that calls the model
def call_model(state: MessagesState):
    messages = state["messages"]
    logging.info(f"Calling model with messages: {messages}")
    response = model.invoke(messages)
    logging.info(f"Model response: {response.content}")
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


# Define a new graph
workflow = StateGraph(MessagesState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.add_edge(START, "agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    "agent",
    should_continue,
)

# Add normal edge from tools to agent
workflow.add_edge("tools", "agent")

# Initialize memory to persist state between graph runs
checkpointer = MemorySaver()

# Compile the graph
app = workflow.compile(checkpointer=checkpointer)

# Use the Runnable with verbose logging
final_state = app.invoke(
    {"messages": [HumanMessage(content="what is the weather in Taipei?")]},
    config={"configurable": {"thread_id": 42}},
)

# Log and display the final state
logging.info(f"Final state: {final_state['messages'][-1].content}")

image_data = app.get_graph().draw_mermaid_png()

# Open the image using PIL
image = Image.open(BytesIO(image_data))
image.show()

print(final_state["messages"][-1].content)
