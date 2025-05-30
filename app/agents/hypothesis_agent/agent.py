# app/agents/hypothesis_agent/agent.py - Fixed to keep titles simple
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
from app.tools.market_data_tool import market_data_tool
from app.tools.news_data_tool import news_data_tool
import json

class HypothesisAgent:
    def __init__(self):
        try:
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            self.model = GenerativeModel(
                model_name=MODEL_NAME,
                generation_config=GENERATION_CONFIG,
                system_instruction=SYSTEM_INSTRUCTION
            )
        except Exception as e:
            print(f"Error initializing Hypothesis Agent: {e}")
            self.model = None
    
    def process(self, input_data):
        """Process the input and generate a response."""
        if not self.model:
            return {"error": "Model not initialized"}
        
        # Determine the type of request
        mode = input_data.get("mode", "analyze")
        
        if mode == "generate":
            prompt = self._create_generation_prompt(input_data)
        elif mode == "refine":
            prompt = self._create_refinement_prompt(input_data)
        else:
            # For analyze mode, keep it SIMPLE - just clean the input
            prompt = self._create_simple_analysis_prompt(input_data)
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "output": response.text,
                "status": "success",
                "mode": mode
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    def _create_simple_analysis_prompt(self, input_data):
        """Create a SIMPLE prompt that just cleans the hypothesis without over-processing"""
        hypothesis = input_data.get("hypothesis", "")
        
        return f"""
        Clean and structure this trading hypothesis into a clear, concise title:
        
        Original: "{hypothesis}"
        
        Rules:
        1. Keep it simple and direct
        2. Include the company name and ticker if mentioned
        3. Include the price target and timeframe
        4. NO analysis, NO bullet points, NO explanations
        5. Maximum 2 sentences
        6. Format: "[Company] ([TICKER]) will reach $[PRICE] by [TIMEFRAME]"
        
        Examples of GOOD outputs:
        - "Apple (AAPL) will reach $220 by end of Q2 2025"
        - "Bitcoin (BTC) will reach $100,000 by June 2025"
        - "Oil prices will exceed $85/barrel by March 2025"
        
        Provide ONLY the cleaned hypothesis title, nothing else.
        """
    
    def _create_generation_prompt(self, input_data):
        context = input_data.get("context", {})
        return f"""
        Generate a new trading hypothesis based on current market conditions.
        
        Context: {json.dumps(context, indent=2)}
        
        Please provide:
        1. A specific, actionable trading hypothesis
        2. Rationale based on market analysis
        3. Structured components (thesis, instruments, timeframe, etc.)
        4. Initial confidence assessment (0-1)
        
        Format your response with clear sections.
        """
    
    def _create_refinement_prompt(self, input_data):
        idea = input_data.get("idea", "")
        return f"""
        Refine this trading idea into a formal hypothesis:
        
        Original Idea: "{idea}"
        
        Please:
        1. Extract the core investment thesis
        2. Add specific structure and components
        3. Provide timeframe and success metrics
        4. Assess initial confidence (0-1)
        
        Format as a structured hypothesis.
        """

def create():
    """Create and return a hypothesis agent instance."""
    return HypothesisAgent()
