# src/eval/eval_agent.py
from langchain.messages import HumanMessage
from src.agent import SECAgent


class AgentEval:
    def __init__(self):
        self.sec_agent = SECAgent()
        self.agent = self.sec_agent.build()



    def test_simple_lookup_apple_revenue(self):
        """Apple revenue 2023 — single postgres call, known value."""
        
        question = "What was Apple's revenue in 2023?"
        expected_tools = ["postgres_query"]
        expected_value = "383"  # $383.3B
        expected_ticker = "AAPL"

        # Run agent
        result = self.agent.invoke({"messages": [HumanMessage(content=question)]})
        messages = result["messages"]

        # Check 1: Right tools called
        tool_names = [tc["name"] for msg in messages for tc in getattr(msg, "tool_calls", [])]
        assert "postgres_query" in tool_names, f"Expected postgres_query, got {tool_names}"

        # Check 2: Right parameters
        for msg in messages:
            for tc in getattr(msg, "tool_calls", []):
                if tc["name"] == "postgres_query":
                    assert tc["args"]["ticker"] == expected_ticker, f"Expected AAPL, got {tc['args']['ticker']}"

        # Check 3: Answer contains expected value
        final_answer = messages[-1].content
        assert expected_value in final_answer, f"Expected {expected_value} in answer, got: {final_answer[:200]}"

        # Check 4: No unnecessary tools called
        assert "edgar_api" not in tool_names, "Should not call edgar_api for existing company"
        assert "anomaly_detector" not in tool_names, "Should not call anomaly_detector for simple lookup"

        print("PASSED: test_simple_lookup_apple_revenue")

    
    def test_simple_lookup_msft_operating_income(self):
        """MSFT Operating Income 2023 — single postgres call, known value."""

        question = "What was Microsoft's operating income in 2023?"

        expected_tools = ["postgres_query"]
        expected_value = "88"
        expected_ticker = "MSFT"

        #Run agent
        result = self.agent.invoke({"messages": [HumanMessage(content=question)]})
        messages = result["messages"]

        # Check 1: Right tools called
        tool_names = [tc["name"] for msg in messages for tc in getattr(msg, "tool_calls", [])]
        for tool in expected_tools:
            assert tool in tool_names, f"Expected postgres_query, got {tool_names}"

        # Check 2: Right parameters
        for msg in messages:
            for tc in getattr(msg, "tool_calls", []):
                if tc["name"] == "postgres_query":
                    assert tc["args"]["ticker"] == expected_ticker, f"Expected MSFT, got {tc['args']['ticker']}"
        

        # Check 3: Answer contains expected value
        final_answer = messages[-1].content
        assert expected_value in final_answer, f"Expected {expected_value} in answer, got: {final_answer[:200]}"

        # Check 4: No unnecessary tools called
        assert "edgar_api" not in tool_names, "Should not call edgar_api for existing company"
        assert "anomaly_detector" not in tool_names, "Should not call anomaly_detector for simple lookup"

        print("PASSED: test_simple_lookup_msft_revenue")

    
    def test_simple_lookup_jpm_total_debt(self):
        """JPM total_debt 2025 — single postgres call, known value."""

        question = "What was JP Morgan's total debt in 2025?"

        expected_tools = ["postgres_query"]
        expected_value = "435"
        expected_ticker = "JPM"

        #Run agent
        result = self.agent.invoke({"messages": [HumanMessage(content=question)]})
        messages = result["messages"]

        # Check 1: Right tools called
        tool_names = [tc["name"] for msg in messages for tc in getattr(msg, "tool_calls", [])]
        for tool in expected_tools:
            assert tool in tool_names, f"Expected postgres_query, got {tool_names}"

        # Check 2: Right parameters
        for msg in messages:
            for tc in getattr(msg, "tool_calls", []):
                if tc["name"] == "postgres_query":
                    assert tc["args"]["ticker"] == expected_ticker, f"Expected JPM, got {tc['args']['ticker']}"
        

        # Check 3: Answer contains expected value
        final_answer = messages[-1].content
        assert expected_value in final_answer, f"Expected {expected_value} in answer, got: {final_answer[:200]}"

        # Check 4: No unnecessary tools called
        assert "edgar_api" not in tool_names, "Should not call edgar_api for existing company"
        assert "anomaly_detector" not in tool_names, "Should not call anomaly_detector for simple lookup"

        print("PASSED: test_simple_lookup_jpm_total_debt")


    def test_multi_tool_anomaly_with_explanation(self):

        question = "Were there any financial anomalies for ExxonMobil? Explain the biggest one."
        expected_tools = ["anomaly_detector", "rag_retrieval"]
        expected_values = ["net income", "revenue", "35.4"]
        expected_ticker = "XOM"


        #Run agent
        result = self.agent.invoke({"messages": [HumanMessage(content=question)]})
        messages = result["messages"]

        # Check 1: Right tools called
        tool_names = [tc["name"] for msg in messages for tc in getattr(msg, "tool_calls", [])]
        for tool in expected_tools:
            assert tool in tool_names, f"Expected {tool}, got {tool_names}"

        
        # Check 2: Right parameters
        for msg in messages:
            for tc in getattr(msg, "tool_calls", []):
                if tc["name"] == "anomaly_detector":
                    assert tc["args"]["ticker"] == expected_ticker, f"Expected XOM, got {tc['args']['ticker']}"

        
        # Check 3: Answer contains expected value
        final_answer = messages[-1].content
        final_lower = final_answer.lower()
        for expected_value in expected_values:
            assert expected_value in final_lower, f"Expected {expected_value} in answer, got: {final_answer}"

        # Check 4: No unnecessary tools called
        assert "edgar_api" not in tool_names, "Should not call edgar_api for existing company"


        print("PASSED: test_multi_tool_anomaly_with_explanation")



    def test_multi_tool_apple_anomalies(self):
        question = "What anomalies did Apple have? Explain them."
        expected_tools = ["anomaly_detector", "rag_retrieval"]
        expected_ticker = "AAPL"
        expected_values = ["stockholders_equity", "equity"] 

        result = self.agent.invoke({"messages": [HumanMessage(content=question)]})
        messages = result["messages"]

        tool_names = [tc["name"] for msg in messages for tc in getattr(msg, "tool_calls", [])]
        for tool in expected_tools:
            assert tool in tool_names, f"Expected {tool}, got {tool_names}"

        for msg in messages:
            for tc in getattr(msg, "tool_calls", []):
                if tc["name"] == "anomaly_detector":
                    assert tc["args"]["ticker"] == expected_ticker

        final_lower = messages[-1].content.lower()
        has_any = any(v in final_lower for v in expected_values)
        assert has_any, f"Expected one of {expected_values} in answer"
        print("PASSED: test_multi_tool_apple_anomalies")


    def test_unknown_company_ingestion(self):
        """Agent should call edgar_api when company not in DB, then answer."""
        question = "What was Walmart's revenue in 2024?"
        expected_tools = ["edgar_api", "postgres_query"]

        result = self.agent.invoke({"messages": [HumanMessage(content=question)]})
        messages = result["messages"]

        tool_names = [tc["name"] for msg in messages for tc in getattr(msg, "tool_calls", [])]
        assert "edgar_api" in tool_names, f"Expected edgar_api, got {tool_names}"
        assert "postgres_query" in tool_names, f"Expected postgres_query, got {tool_names}"

        for msg in messages:
            for tc in getattr(msg, "tool_calls", []):
                if tc["name"] == "edgar_api":
                    assert tc["args"]["ticker"] == "WMT"

        final_lower = messages[-1].content.lower()
        assert "revenue" in final_lower, "Answer should mention revenue"
        assert "$" in messages[-1].content, "Answer should contain a dollar amount"
        print("PASSED: test_unknown_company_ingestion")


    def test_missing_metric_jpm_operating_income(self):
        """JPM doesn't have operating income — agent should handle gracefully."""
        question = "What was JPMorgan's operating income in 2024?"

        result = self.agent.invoke({"messages": [HumanMessage(content=question)]})
        messages = result["messages"]

        final_lower = messages[-1].content.lower()
        # Should NOT hallucinate a number — should explain it's unavailable
        has_explanation = any(term in final_lower for term in [
            "not available", "not reported", "unavailable", "null",
            "not applicable", "different structure", "banks",
            "not use", "doesn't report", "does not report"
        ])
        assert has_explanation, f"Expected explanation of missing data, got: {final_lower[:300]}"
        print("PASSED: test_missing_metric_jpm_operating_income")

    
    def test_missing_company_invalid_ticker(self):
        """Completely invalid ticker — should fail gracefully."""
        question = "What was XYZFAKE's revenue in 2024?"

        result = self.agent.invoke({"messages": [HumanMessage(content=question)]})
        messages = result["messages"]

        final_lower = messages[-1].content.lower()
        has_error = any(term in final_lower for term in [
        "not found", "couldn't find", "could not find",
        "no company", "unable to find", "don't have",
        "does not exist", "invalid", "not a valid"
        ])
        assert has_error, f"Expected error message for invalid ticker, got: {final_lower[:300]}"
        print("PASSED: test_missing_company_invalid_ticker")

    
    def test_cross_company_comparison(self):
        """Compare metrics across two companies."""
        question = "Compare Apple and Microsoft's revenue in 2024."
        expected_tickers = ["AAPL", "MSFT"]

        result = self.agent.invoke({"messages": [HumanMessage(content=question)]})
        messages = result["messages"]

        tool_names = [tc["name"] for msg in messages for tc in getattr(msg, "tool_calls", [])]
        assert "postgres_query" in tool_names

        # Should have called postgres for both companies
        queried_tickers = []
        for msg in messages:
            for tc in getattr(msg, "tool_calls", []):
                if tc["name"] == "postgres_query":
                    queried_tickers.append(tc["args"]["ticker"])

        for ticker in expected_tickers:
            assert ticker in queried_tickers, f"Expected query for {ticker}, got {queried_tickers}"

        # Answer should mention both companies
        final_lower = messages[-1].content.lower()
        assert "apple" in final_lower, "Answer should mention Apple"
        assert "microsoft" in final_lower, "Answer should mention Microsoft"
        print("PASSED: test_cross_company_comparison")



      
        










if __name__ == "__main__":
    agentEval = AgentEval()
    # agentEval.test_simple_lookup_apple_revenue()
    # agentEval.test_simple_lookup_msft_operating_income()
    # agentEval.test_simple_lookup_jpm_total_debt()
    # agentEval.test_multi_tool_anomaly_with_explanation()
    # agentEval.test_multi_tool_apple_anomalies()
    # agentEval.test_unknown_company_ingestion()
    # agentEval.test_missing_metric_jpm_operating_income()
    # agentEval.test_missing_company_invalid_ticker()
    agentEval.test_cross_company_comparison()