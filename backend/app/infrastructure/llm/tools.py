from langchain_core.tools import tool


@tool("search")
def search(query: str) -> str:
    """Search the live web for current information. Use this for news, prices, and recent events."""
    return "This tool is executed by the LocalGPT TinyFish tool loop."


@tool("fetch_content")
def fetch_content(url: str) -> str:
    """Fetch and summarize the main content of a specific web page."""
    return "This tool is executed by the LocalGPT TinyFish tool loop."


@tool("run_web_automation")
def run_web_automation(url: str, goal: str) -> str:
    """Interact with a website to complete a browser task and return the result."""
    return "This tool is executed by the LocalGPT TinyFish tool loop."


TINYFISH_TOOLS = [search, fetch_content, run_web_automation]
