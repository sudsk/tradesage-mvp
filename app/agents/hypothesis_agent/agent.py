# app/agents/hypothesis_agent/agent.py - Intelligent, no hardcoding
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
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
        """Process any hypothesis using intelligent AI analysis - no hardcoding"""
        if not self.model:
            return {"error": "Model not initialized"}
        
        mode = input_data.get("mode", "analyze")
        
        if mode == "generate":
            prompt = self._create_generation_prompt(input_data)
        elif mode == "refine":
            prompt = self._create_refinement_prompt(input_data)
        else:
            # Intelligent analysis mode - works for ANY hypothesis
            prompt = self._create_intelligent_analysis_prompt(input_data)
        
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
    
    def _create_intelligent_analysis_prompt(self, input_data):
        """Create intelligent prompt that works for ANY financial hypothesis"""
        hypothesis = input_data.get("hypothesis", "")
        
        return f"""
        You are an expert financial analyst. Clean and structure this trading hypothesis intelligently:
        
        Original Input: "{hypothesis}"
        
        Your task - analyze and structure this hypothesis for ANY financial instrument:
        
        1. **Identify the Financial Instrument:**
           - What asset is being discussed? (stock, crypto, commodity, currency, bond, etc.)
           - What is the official name and trading symbol?
           - What market does it trade on?
        
        2. **Extract the Prediction:**
           - What is the directional prediction? (bullish/bearish/neutral)
           - What specific price target or percentage move is mentioned?
           - What timeframe is specified?
        
        3. **Structure the Title:**
           - Create a clear, concise hypothesis title
           - Include asset name and symbol if determinable
           - Include price target and timeframe
           - Maximum 2 sentences
           - Format: "[Asset] ([Symbol]) will [direction] [target] by [timeframe]"
        
        **Important Guidelines:**
        - Work with ANY financial instrument globally
        - Do not use hardcoded patterns or assumptions
        - Derive everything from the content and your knowledge
        - If information is unclear, make intelligent inferences
        - Keep the output clean and professional
        
        **Examples of good outputs:**
        - "Tesla (TSLA) will reach $300 by Q3 2025"
        - "Bitcoin (BTC-USD) will appreciate to $120,000 by year-end"
        - "West Texas Intermediate crude oil will exceed $95/barrel by summer 2025"
        - "Euro (EUR/USD) will strengthen to 1.15 by Q2 2025"
        
        Provide ONLY the structured hypothesis title, nothing else.
        """
    
    def _create_generation_prompt(self, input_data):
        """Generate new hypothesis based on intelligent market analysis"""
        context = input_data.get("context", {})
        
        return f"""
        Generate a new, intelligent trading hypothesis based on current market analysis.
        
        Context Provided: {json.dumps(context, indent=2)}
        
        Create a hypothesis that:
        1. Is based on realistic market conditions and trends
        2. Specifies a clear asset, direction, target, and timeframe
        3. Is actionable and measurable
        4. Considers current market dynamics
        5. Works for any asset class (stocks, crypto, commodities, currencies, etc.)
        
        Structure your response with:
        - **Hypothesis Statement**: Clear, specific prediction
        - **Rationale**: Why this prediction makes sense
        - **Key Factors**: What would drive this outcome
        - **Risks**: What could prevent this outcome
        - **Timeline**: Specific timeframe and milestones
        
        Make it professional and well-reasoned for any financial instrument.
        """
    
    def _create_refinement_prompt(self, input_data):
        """Refine any trading idea into a structured hypothesis"""
        idea = input_data.get("idea", "")
        
        return f"""
        Refine this trading idea into a professional, structured hypothesis:
        
        Original Idea: "{idea}"
        
        Transform this into a complete investment hypothesis by:
        
        1. **Clarifying the Asset**: What specific instrument is being discussed?
        2. **Defining the Thesis**: What is the core investment argument?
        3. **Setting Targets**: What specific price or performance target?
        4. **Establishing Timeline**: What is the investment timeframe?
        5. **Identifying Catalysts**: What events could drive this outcome?
        6. **Assessing Confidence**: What is the initial confidence level?
        
        Structure the output as:
        - **Refined Hypothesis**: "[Asset] will [outcome] by [timeframe]"
        - **Investment Thesis**: Core reasoning (2-3 sentences)
        - **Success Criteria**: Specific measurable outcomes
        - **Key Catalysts**: Events that would drive success
        - **Initial Confidence**: High/Medium/Low with brief reasoning
        
        Work intelligently with any asset class or market.
        """

def create():
    """Create and return an intelligent hypothesis agent instance"""
    return HypothesisAgent()
