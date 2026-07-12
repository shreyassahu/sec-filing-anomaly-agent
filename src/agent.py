from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
from langchain.messages import SystemMessage, ToolMessage, HumanMessage
from typing import Literal
from langgraph.graph import StateGraph, START, END, MessagesState
import operator
from dotenv import load_dotenv
from src.tools import postgres_query, rag_retrieval, edgar_api, anomaly_detector
load_dotenv()

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
    "- When answering financial questions, always provide the requested metric first, "
    "then add brief year-over-year context if the data is available. Keep responses concise "
    "— no more than 5-6 lines unless the user asks for detail."


    "COMPANY CONTEXT:\n"
    "Five companies are pre-loaded in the database: Apple (AAPL, CIK 0000320193), "
    "JPMorgan Chase (JPM, CIK 0000019617), Microsoft (MSFT, CIK 0000789019), "
    "ExxonMobil (XOM, CIK 0000034088), and Johnson & Johnson (JNJ, CIK 0000200406). "
    "For any other company, use edgar_api to fetch their data first."
)

class SECAgent:

    class AgentState(TypedDict):
        messages: Annotated[list[AnyMessage], operator.add]
        company_context: dict
        retrieved_metrics: list
        retrieved_docs: list
        api_response: dict
        anomalies_found: dict
        llm_calls: int

    def __init__(self):
        self.model = init_chat_model("claude-haiku-4-5", temperature=0)
        self.tools = [postgres_query, rag_retrieval, edgar_api, anomaly_detector]
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        self.model_with_tools = self.model.bind_tools(self.tools)




    def llm_call(self, state: dict):
        """
        LLM decides whether to call a tool or not
        """

        return {
            "messages": [
                self.model_with_tools.invoke(
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


    def tool_node(self, state: dict):
        """
        Performs the tool call
        """

        result = []
        for tool_call in state["messages"][-1].tool_calls:
            tool = self.tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
        return {"messages": result}


    def should_continue(self, state: MessagesState) -> Literal["tool_node", END]:
        """
        Decide if we should continue the loop or stop based on whether the LLM made a tool call
        """

        messages = state["messages"]
        last_message = messages[-1]


        if last_message.tool_calls:
            return "tool_node"
        
        return END
        
    # In src/agent.py — add this method to SECAgent
    def build(self):
        agent_builder = StateGraph(MessagesState)
        agent_builder.add_node("llm_call", self.llm_call)
        agent_builder.add_node("tool_node", self.tool_node)
        agent_builder.add_edge(START, "llm_call")
        agent_builder.add_conditional_edges("llm_call", self.should_continue, ["tool_node", END])
        agent_builder.add_edge("tool_node", "llm_call")
        return agent_builder.compile()


# agent_builder = StateGraph(MessagesState)

# agent_builder.add_node("llm_call", llm_call)
# agent_builder.add_node("tool_node", tool_node)

# agent_builder.add_edge(START, "llm_call")
# agent_builder.add_conditional_edges("llm_call",
#                                     should_continue,
#                                     ["tool_node", END])

# agent_builder.add_edge("tool_node", "llm_call")


# agent = agent_builder.compile()


# # messages = [HumanMessage(content="Why did Apple's revenue decline in 2023?")]
# # messages = [HumanMessage(content="What was JPMorgan's total debt in 2024?")]
# messages = [HumanMessage(content="What were Nvidia's financial anomalies in 2024?")]
# messages = agent.invoke({"messages" : messages})

# # tool_names = [tc["name"] for msg in messages for tc in getattr(msg, "tool_calls", [])]

# for m in messages["messages"]:
#     # m.pretty_print()
#     for tc in getattr(m, "tool_calls", []):
#         print(tc["name"])







