from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
from langchain.messages import SystemMessage, ToolMessage, HumanMessage
from typing import Literal
from langgraph.graph import StateGraph, START, END, MessagesState
import operator
from IPython.display import Image, display
from dotenv import load_dotenv
load_dotenv()


model = init_chat_model(
    "claude-haiku-4-5",
    temperature=0
)

system_prompt = (
    "You are an AI financial analyst that helps PE fund analysts evaluate public companies "
    "using data extracted from SEC 10-K filings. You answer questions about financial metrics, "
    "year-over-year trends, anomalies, and risk factors.\n\n"

    "TOOL USAGE STRATEGY:\n"
    "1. Always start with postgres_query to check if the company's data exists in the database.\n"
    "2. If no data is found, use edgar_api with the company's ticker to ingest their filings first, "
    "then query again with postgres_query.\n"
    "3. When asked about anomalies or unusual changes, use anomaly_detector to flag metrics "
    "with >15% year-over-year change.\n"
    "4. When anomalies are found, use rag_retrieval to search the MD&A and Risk Factors sections "
    "for narrative context that explains why the change occurred.\n"
    "5. For questions about risks, strategy, or management commentary, use rag_retrieval directly.\n\n"

    "RESPONSE GUIDELINES:\n"
    "- Always include actual numbers with dollar amounts and percentages in your response.\n"
    "- When reporting anomalies, show both the current and prior year values and the percentage change.\n"
    "- When narrative context is available from RAG, use it to explain why a metric changed.\n"
    "- If a metric is unavailable (e.g., operating income for banks like JPMorgan), "
    "acknowledge it and explain that banks have a different income statement structure.\n"
    "- Present financial data in tables when comparing multiple metrics or companies.\n\n"

    "COMPANY CONTEXT:\n"
    "Five companies are pre-loaded in the database: Apple (AAPL, CIK 0000320193), "
    "JPMorgan Chase (JPM, CIK 0000019617), Microsoft (MSFT, CIK 0000789019), "
    "ExxonMobil (XOM, CIK 0000034088), and Johnson & Johnson (JNJ, CIK 0000200406). "
    "For any other company, use edgar_api to fetch their data first."
)

#Define Tools
@tool
def postgres_query(cik: str, fiscal_year: int = None, metric_name: str = None):
    """
    Fetch financial metrics from the database for a specific company.
    Returns revenue, net_income, operating_income, total_debt, and stockholders_equity.
    If fiscal_year is provided, returns metrics for that year only.
    If metric_name is provided, returns only that metric across available years.
    If neither is provided, returns all metrics for all available years.
    """
    return {"status": "stub", "message": "Postgres tool not yet implemented"}

@tool
def rag_retrieval(query_text: str, cik: str = None, fiscal_year: int = None, section_name: str = None):
    """
    Search narrative sections of SEC 10-K filings for relevant context.
    Sections available: 'mda' (Management's Discussion and Analysis) and 'risk_factors'.
    Use this to find explanations for financial changes, risk discussions, and management commentary.
    Filters by company (cik), fiscal year, and section name if provided.
    """
    return {"status": "stub", "message": "RAG retrieval tool not yet implemented"}

@tool
def edgar_api(ticker: str):
    """
    Fetch and ingest the latest 3 years of 10-K filings from SEC EDGAR for a company
    not yet in the database. Takes a stock ticker (e.g., 'TSLA'), resolves it to a CIK,
    downloads filings, parses financial metrics, and stores them in the database.
    Only use this when postgres_query returns no data for the requested company.
    """
    return {"status": "stub", "message": "EDGAR API tool not yet implemented"}

@tool
def anomaly_detector(cik: str, fiscal_year: int):
    """
    Compare financial metrics for the given fiscal year against the prior year
    for a specific company. Flags any metric with a year-over-year change
    exceeding 15%. Returns flagged anomalies with the metric name, both values,
    percentage change, and severity level.
    """
    return {"status": "stub", "message": "Anomaly detector tool not yet implemented"}

# Augment the LLM with tools
tools = [postgres_query, rag_retrieval, edgar_api, anomaly_detector]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    company_context: dict
    retrieved_metrics: list
    retrieved_docs: list
    api_response: dict
    anomalies_found: dict
    llm_calls: int

def llm_call(state: dict):
    """
    LLM decides whether to call a tool or not
    """

    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content=system_prompt
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }


def tool_node(state: dict):
    """
    Performs the tool call
    """

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}


def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """
    Decide if we should continue the loop or stop based on whether the LLM made a tool call
    """

    messages = state["messages"]
    last_message = messages[-1]


    if last_message.tool_calls:
        return "tool_node"
    
    return END


agent_builder = StateGraph(MessagesState)

agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call",
                                    should_continue,
                                    ["tool_node", END])

agent_builder.add_edge("tool_node", "llm_call")


agent = agent_builder.compile()

display(Image(agent.get_graph(xray=True).draw_mermaid_png()))

messages = [HumanMessage(content="What is the annual revenue of Apple in the FY-2023??")]
messages = agent.invoke({"messages" : messages})

for m in messages["messages"]:
    m.pretty_print()







