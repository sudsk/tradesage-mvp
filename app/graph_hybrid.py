# app/graph_hybrid.py
from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph
from app.agents.hypothesis_agent.agent import create as create_hypothesis_agent
from app.agents.context_agent.agent import create as create_context_agent
from app.agents.synthesis_agent.agent import create as create_synthesis_agent
from app.agents.alert_agent.agent import create as create_alert_agent

# Import hybrid agents
try:
    from app.agents.research_agent.agent_hybrid import create as create_hybrid_research_agent
    HYBRID_RESEARCH_AVAILABLE = True
except ImportError:
    from app.agents.research_agent.agent import create as create_research_agent
    HYBRID_RESEARCH_AVAILABLE = False

try:
    from app.agents.contradiction_agent.agent_hybrid import create as create_hybrid_contradiction_agent
    HYBRID_CONTRADICTION_AVAILABLE = True
except ImportError:
    from app.agents.contradiction_agent.agent import create as create_contradiction_agent
    HYBRID_CONTRADICTION_AVAILABLE = False

# Define enhanced state structure
class TradeSageState(TypedDict):
    input: str
    mode: str
    hypothesis: str
    processed_hypothesis: str
    context: Dict  # NEW: Context from Context Agent    
    research_data: Dict
    contradictions: List[Dict]
    confirmations: List[Dict]
    synthesis: str
    alerts: List[Dict]
    final_response: str
    error: str
    
    # Enhanced fields for hybrid approach
    data_sources: Dict
    confidence_score: float
    research_method: str

def create_hybrid_graph():
    """Create the enhanced TradeSage AI workflow graph with hybrid capabilities."""
    
    print("🚀 Initializing TradeSage Hybrid Graph")
    print("=" * 50)
    
    # Initialize agents with hybrid capability detection
    hypothesis_agent = create_hypothesis_agent()
    context_agent = create_context_agent()    
    synthesis_agent = create_synthesis_agent()
    alert_agent = create_alert_agent()
    
    if HYBRID_RESEARCH_AVAILABLE:
        research_agent = create_hybrid_research_agent()
        print("✅ Hybrid Research Agent loaded")
    else:
        research_agent = create_research_agent()
        print("⚠️  Using standard Research Agent (hybrid not available)")
    
    if HYBRID_CONTRADICTION_AVAILABLE:
        contradiction_agent = create_hybrid_contradiction_agent()
        print("✅ Hybrid Contradiction Agent loaded")
    else:
        contradiction_agent = create_contradiction_agent()
        print("⚠️  Using standard Contradiction Agent (hybrid not available)")
    
    print("=" * 50)
    
    # Define enhanced agent nodes
    def hypothesis_node(state: TradeSageState) -> TradeSageState:
        """Process hypothesis generation/refinement with enhanced error handling."""
        try:
            print("🧠 Processing hypothesis...")
            result = hypothesis_agent.process(state)
            
            if result.get("status") == "success":
                state["processed_hypothesis"] = result.get("output", state.get("hypothesis", ""))
                print(f"   ✅ Hypothesis processed: {state['processed_hypothesis'][:100]}...")
            else:
                error_msg = result.get("error", "Hypothesis processing failed")
                state["error"] = error_msg
                print(f"   ❌ Hypothesis error: {error_msg}")
                
            return state
        except Exception as e:
            error_msg = f"Hypothesis agent error: {str(e)}"
            state["error"] = error_msg
            print(f"❌ {error_msg}")
            return state

    def context_node(state: TradeSageState) -> TradeSageState:
        """Analyze hypothesis and provide intelligent context for other agents."""
        try:
            print("🧠 Analyzing hypothesis context...")
            result = context_agent.process(state)
            
            if result.get("status") == "success":
                context = result.get("context", {})
                state["context"] = context
                
                # Log context summary
                asset_info = context.get("asset_info", {})
                print(f"   ✅ Context: {asset_info.get('asset_name', 'Unknown')} ({asset_info.get('primary_symbol', 'N/A')})")
                print(f"      Type: {asset_info.get('asset_type', 'Unknown')} | Direction: {context.get('hypothesis_details', {}).get('direction', 'Unknown')}")
                
            else:
                error_msg = result.get("error", "Context analysis failed")
                state["error"] = error_msg
                print(f"   ❌ Context error: {error_msg}")
                
            return state
        except Exception as e:
            error_msg = f"Context agent error: {str(e)}"
            state["error"] = error_msg
            print(f"❌ {error_msg}")
            return state
            
    def research_node(state: TradeSageState) -> TradeSageState:
        """Conduct market research using hybrid approach."""
        try:
            print("🔬 Conducting hybrid research...")
            result = research_agent.process(state)
            
            if result.get("status") == "success":
                research_data = result.get("research_data", {})
                state["research_data"] = research_data
                
                # Extract metadata about research method
                state["research_method"] = research_data.get("research_method", "unknown")
                state["data_sources"] = research_data.get("data_sources", {})
                state["confidence_score"] = research_data.get("confidence_score", 0.5)
                
                # Log research summary
                sources = state["data_sources"]
                rag_count = sources.get("rag_database", 0)
                market_count = sources.get("real_time_market", 0)
                news_count = sources.get("real_time_news", 0)
                
                print(f"   ✅ Research completed using {state['research_method']} method")
                print(f"      - RAG insights: {rag_count}")
                print(f"      - Market data: {market_count} sources")
                print(f"      - News articles: {news_count}")
                print(f"      - Confidence: {state['confidence_score']:.2f}")
            else:
                error_msg = result.get("error", "Research failed")
                state["error"] = error_msg
                print(f"   ❌ Research error: {error_msg}")
            
            return state
        except Exception as e:
            error_msg = f"Research agent error: {str(e)}"
            state["error"] = error_msg
            print(f"❌ {error_msg}")
            return state
    
    def contradiction_node(state: TradeSageState) -> TradeSageState:
        """Identify contradictions using hybrid approach."""
        try:
            print("🎯 Identifying contradictions...")
            result = contradiction_agent.process(state)
            
            if result.get("status") in ["success", "error_fallback"]:
                contradictions = result.get("contradictions", [])
                state["contradictions"] = contradictions
                
                # Log contradiction summary
                evidence_sources = result.get("evidence_sources", {})
                rag_evidence = evidence_sources.get("rag_database", 0)
                ai_generated = evidence_sources.get("ai_generated", 0)
                
                print(f"   ✅ Found {len(contradictions)} contradictions")
                print(f"      - From RAG database: {rag_evidence}")
                print(f"      - AI generated: {ai_generated}")
                
                # Count by strength
                strong_count = sum(1 for c in contradictions if c.get("strength", "").lower() == "strong")
                medium_count = sum(1 for c in contradictions if c.get("strength", "").lower() == "medium")
                print(f"      - Strong: {strong_count}, Medium: {medium_count}")
                
            else:
                error_msg = result.get("error", "Contradiction analysis failed")
                state["error"] = error_msg
                print(f"   ❌ Contradiction error: {error_msg}")
            
            return state
        except Exception as e:
            error_msg = f"Contradiction agent error: {str(e)}"
            state["error"] = error_msg
            print(f"❌ {error_msg}")
            return state
    
    def synthesis_node(state: TradeSageState) -> TradeSageState:
        """Synthesize findings with enhanced confidence scoring."""
        try:
            print("🔬 Synthesizing analysis...")
            
            # Enhanced input for synthesis including confidence data
            enhanced_input = {
                **state,
                "data_quality": {
                    "research_method": state.get("research_method", "unknown"),
                    "data_sources": state.get("data_sources", {}),
                    "base_confidence": state.get("confidence_score", 0.5)
                }
            }
            
            result = synthesis_agent.process(enhanced_input)
            
            if result.get("status") == "success":
                state["synthesis"] = result.get("synthesis", "")
                
                # Extract confirmations if available
                confirmations = result.get("confirmations", [])
                state["confirmations"] = confirmations
                
                # Update confidence based on synthesis
                assessment = result.get("assessment", {})
                if "confidence" in assessment:
                    state["confidence_score"] = assessment["confidence"]
                
                print(f"   ✅ Synthesis completed")
                print(f"      - Confirmations: {len(confirmations)}")
                print(f"      - Final confidence: {state['confidence_score']:.2f}")
            else:
                error_msg = result.get("error", "Synthesis failed")
                state["error"] = error_msg
                print(f"   ❌ Synthesis error: {error_msg}")
            
            return state
        except Exception as e:
            error_msg = f"Synthesis agent error: {str(e)}"
            state["error"] = error_msg
            print(f"❌ {error_msg}")
            return state
    
    def alert_node(state: TradeSageState) -> TradeSageState:
        """Generate alerts with enhanced context."""
        try:
            print("🚨 Generating alerts...")
            
            # Enhanced input including all context
            enhanced_input = {
                **state,
                "analysis_context": {
                    "research_method": state.get("research_method", "unknown"),
                    "confidence_score": state.get("confidence_score", 0.5),
                    "contradiction_count": len(state.get("contradictions", [])),
                    "confirmation_count": len(state.get("confirmations", [])),
                    "data_sources": state.get("data_sources", {})
                }
            }
            
            result = alert_agent.process(enhanced_input)
            
            if result.get("status") == "success":
                alerts = result.get("alerts", [])
                state["alerts"] = alerts
                state["final_response"] = result.get("recommendations", "")
                
                print(f"   ✅ Generated {len(alerts)} alerts")
                
                # Log alert priorities
                high_priority = sum(1 for a in alerts if a.get("priority", "").lower() == "high")
                medium_priority = sum(1 for a in alerts if a.get("priority", "").lower() == "medium")
                print(f"      - High priority: {high_priority}")
                print(f"      - Medium priority: {medium_priority}")
                
            else:
                error_msg = result.get("error", "Alert generation failed")
                state["error"] = error_msg
                print(f"   ❌ Alert error: {error_msg}")
            
            return state
        except Exception as e:
            error_msg = f"Alert agent error: {str(e)}"
            state["error"] = error_msg
            print(f"❌ {error_msg}")
            return state

    # Create the workflow graph
    workflow = StateGraph(TradeSageState)
   
    # Add nodes
    workflow.add_node("hypothesis_agent", hypothesis_node)
    workflow.add_node("context_agent", context_node)    
    workflow.add_node("research_agent", research_node)
    workflow.add_node("contradiction_agent", contradiction_node)
    workflow.add_node("synthesis_agent", synthesis_node)
    workflow.add_node("alert_agent", alert_node)
   
    # Add edges (define the flow)
    workflow.add_edge("hypothesis_agent", "context_agent")
    workflow.add_edge("context_agent", "research_agent")    
    workflow.add_edge("research_agent", "contradiction_agent")
    workflow.add_edge("contradiction_agent", "synthesis_agent")
    workflow.add_edge("synthesis_agent", "alert_agent")
   
    # Set entry point
    workflow.set_entry_point("hypothesis_agent")
   
    # Compile and return the graph
    compiled_graph = workflow.compile()
    
    print("✅ Hybrid TradeSage Graph compiled successfully")
    return compiled_graph

# Create the graph (this will be the new main graph)
def create_graph():
    """Main function to create the graph (for backward compatibility)"""
    return create_hybrid_graph()
