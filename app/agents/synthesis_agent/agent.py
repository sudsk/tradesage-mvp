# app/agents/synthesis_agent/agent.py - Updated _generate_context_aware_confirmations method

def _ai_generate_context_confirmations(self, asset_info: Dict, asset_type: str, 
                                     asset_name: str, sector: str, business_model: str, 
                                     hypothesis: str) -> List[Dict]:
    """Use AI to generate context-specific confirmations with database constraints"""
    
    prompt = f"""
    Generate specific confirmations that support this investment hypothesis using context:
    
    HYPOTHESIS: "{hypothesis}"
    
    ASSET CONTEXT:
    - Asset: {asset_name}
    - Type: {asset_type}
    - Sector: {sector}
    - Business Model: {business_model}
    
    CRITICAL CONSTRAINTS - Each confirmation must have:
    - Quote: Maximum 400 characters (keep concise!)
    - Reason: Maximum 400 characters (keep concise!)
    - Source: Maximum 40 characters (e.g., "Market Analysis")
    - Strength: ONLY "Strong", "Medium", or "Weak"
    
    Generate 3 specific confirmations that:
    1. Are directly relevant to this asset type and sector
    2. Reference realistic positive factors for this specific asset
    3. Are concise and database-friendly (NO markdown, NO special formatting)
    
    Format each as exactly: quote|reason|source|strength
    
    Example:
    Services revenue growth drives Apple valuation higher|Recurring services provide stable margins and investor confidence|Earnings Analysis|Strong
    
    Keep everything under the character limits. Be specific but concise.
    """
    
    try:
        response = self.model.generate_content(prompt)
        return self._parse_context_confirmations_strict(response.text, asset_name)
    except Exception as e:
        print(f"❌ Context confirmation generation failed: {str(e)}")
        return self._generate_fallback_confirmations_strict(asset_type, asset_name, sector)

def _parse_context_confirmations_strict(self, response_text: str, asset_name: str) -> List[Dict]:
    """Parse AI-generated confirmations with strict database constraints"""
    confirmations = []
    
    # Try structured format first
    lines = response_text.split('\n')
    
    for line in lines:
        if '|' in line and len(line.split('|')) >= 4:
            parts = line.split('|')
            quote = parts[0].strip()[:400]  # Enforce 400 char limit
            reason = parts[1].strip()[:400]  # Enforce 400 char limit  
            source = parts[2].strip()[:40]   # Enforce 40 char limit
            strength = parts[3].strip()
            
            # Validate strength
            if strength not in ["Strong", "Medium", "Weak"]:
                strength = "Medium"
            
            # Only add if meaningful content
            if len(quote) > 20 and len(reason) > 10:
                confirmations.append({
                    "quote": quote,
                    "reason": reason,
                    "source": source,
                    "strength": strength
                })
    
    # Fallback parsing if structured format fails
    if not confirmations:
        sections = response_text.split('\n')
        for section in sections:
            section = section.strip()
            if len(section) > 30 and not section.startswith('#'):
                # Create safe confirmation
                quote = section[:300] + "..." if len(section) > 300 else section
                confirmations.append({
                    "quote": quote,
                    "reason": f"This factor supports {asset_name} positive outlook.",
                    "source": "AI Analysis",
                    "strength": "Medium"
                })
                if len(confirmations) >= 3:
                    break
    
    return confirmations[:3]  # Limit to 3

def _generate_fallback_confirmations_strict(self, asset_type: str, asset_name: str, sector: str) -> List[Dict]:
    """Generate intelligent fallback confirmations with strict database constraints"""
    
    fallback_confirmations = []
    
    if asset_type == "stock":
        fallback_confirmations.extend([
            {
                "quote": f"{asset_name} operates in {sector} with strong market fundamentals.",
                "reason": f"{sector} industry trends support {asset_name} business growth.",
                "source": "Sector Analysis",
                "strength": "Medium"
            },
            {
                "quote": f"Institutional investment in {sector} companies continues growing.",
                "reason": "Growing institutional interest provides capital and validation.",
                "source": "Institutional Data",
                "strength": "Medium"
            }
        ])
    
    elif asset_type in ["crypto", "cryptocurrency"]:
        fallback_confirmations.extend([
            {
                "quote": f"{asset_name} benefits from increasing institutional adoption.",
                "reason": "Institutional acceptance drives demand and legitimacy.",
                "source": "Adoption Analysis",
                "strength": "Strong"
            },
            {
                "quote": f"Network effects of {asset_name} create value propositions.",
                "reason": "Strong network effects support long-term appreciation.",
                "source": "Technology Analysis",
                "strength": "Medium"
            }
        ])
    
    else:
        # Generic but safe confirmations
        fallback_confirmations.extend([
            {
                "quote": f"Market fundamentals support positive outlook for {asset_name}.",
                "reason": f"Current conditions favor {asset_type} assets.",
                "source": "Market Analysis",
                "strength": "Medium"
            }
        ])
    
    return fallback_confirmations
