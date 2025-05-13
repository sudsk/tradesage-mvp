# app/graph.py
from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph
from app.agents.hypothesis_agent.agent import create as create_hypothesis_agent
from app.agents.research_agent.agent import create as create_research_agent
from app.agents.contradiction_agent.agent import create as create_contradiction_agent
from app.agents.synthesis_agent.agent import create as create_synthesis_agent
from app.agents.alert_agent.agent import create as create_alert_agent

# Define state structure
class TradeSageState(TypedDict):
    input: str
    mode: str
    hypothesis: str
    processed_hypothesis: str
    research_data: Dict
    contradictions: List[Dict]
    synthesis: str
    alerts: List[Dict]
    final_response: str
    error: str

def create_graph():
    """Create the TradeSage AI workflow graph."""
    
    # Initialize agents
    hypothesis_agent = create_hypothesis_agent()
    research_agent = create_research_agent()
    contradiction_agent = create_contradiction_agent()
    synthesis_agent = create_synthesis_agent()
    alert_agent = create_alert_agent()
    
    # Define agent nodes
    def hypothesis_node(state: TradeSageState) -> TradeSageState:
        """Process hypothesis generation/refinement."""
        try:
            result = hypothesis_agent.process(state)
            if result.get("status") == "success":
                state["processed_hypothesis"] = result.get("output", state.get("hypothesis", ""))
            else:
                state["error"] = result.get("error", "Hypothesis processing failed")
            return state
        except Exception as e:
            state["error"] = f"Hypothesis agent error: {str(e)}"
            return state
    
    def research_node(state: TradeSageState) -> TradeSageState:
        """Conduct market research."""
        try:
            result = research_agent.process(state)
            if result.get("status") == "success":
                state["research_data"] = result.get("research_data", {})
            else:
                state["error"] = result.get("error", "Research failed")
            return state
        except Exception as e:
            state["error"] = f"Research agent error: {str(e)}"
            return state
    
    def contradiction_node(state: TradeSageState) -> TradeSageState:
        """Identify contradictions and challenges."""
        try:
            result = contradiction_agent.process(state)
            if result.get("status") == "success":
                state["contradictions"] = result.get("contradictions", [])
            else:
                state["error"] = result.get("error", "Contradiction analysis failed")
            return state
        except Exception as e:
            state["error"] = f"Contradiction agent error: {str(e)}"
            return state
    
    def synthesis_node(state: TradeSageState) -> TradeSageState:
        """Synthesize findings."""
        try:
            result = synthesis_agent.process(state)
            if result.get("status") == "success":
                state["synthesis"] = result.get("synthesis", "")
            else:
                state["error"] = result.get("error", "Synthesis failed")
            return state
        except Exception as e:
            state["error"] = f"Synthesis agent error: {str(e)}"
            return state
    
    def alert_node(state: TradeSageState) -> TradeSageState:
        """Generate alerts and recommendations."""
        try:
            result = alert_agent.process(state)
            if result.get("status") == "success":
                state["alerts"] = result.get("alerts", [])
                state["final_response"] = result.get("recommendations", "")
            else:
                state["error"] = result.get("error", "Alert generation failed")
            return state
        except Exception as e:
            state["error"] = f"Alert agent error: {str(e)}"
            return state

    # Create the workflow graph
    workflow = StateGraph(TradeSageState)
   
    # Add nodes with different names (note the prefix)
    workflow.add_node("hypothesis_agent", hypothesis_node)
    workflow.add_node("research_agent", research_node)
    workflow.add_node("contradiction_agent", contradiction_node)
    workflow.add_node("synthesis_agent", synthesis_node)
    workflow.add_node("alert_agent", alert_node)
   
    # Add edges (define the flow)
    workflow.add_edge("hypothesis_agent", "research_agent")
    workflow.add_edge("research_agent", "contradiction_agent")
    workflow.add_edge("contradiction_agent", "synthesis_agent")
    workflow.add_edge("synthesis_agent", "alert_agent")
   
    # Set entry point
    workflow.set_entry_point("hypothesis_agent")
   
    # Compile and return the graph
    return workflow.compile()
