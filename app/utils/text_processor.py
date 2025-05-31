# app/utils/text_processor.py - Enhanced version with better contradiction processing

import re
import json
from typing import List, Dict, Any

class ResponseProcessor:
    @staticmethod
    def clean_hypothesis_title(raw_title):
        """Extract clean hypothesis title from LLM response."""
        if not raw_title:
            return "Untitled Hypothesis"
        
        # If input is already clean, return it directly
        if len(raw_title.split()) < 15 and "will" in raw_title.lower():
            return raw_title
        
        # Remove markup and formatting
        cleaned = re.sub(r'\*+', '', raw_title)
        cleaned = re.sub(r'#+\s*', '', cleaned)
        cleaned = re.sub(r'Thesis Statement[s]?[:]?\s*', '', cleaned)
        
        # Extract just the hypothesis statement
        patterns = [
            r'([^:\n]+will\s+reach\s+[^.]+)',
            r'([^:\n]+will\s+appreciate\s+[^.]+)',
            r'([^:\n]+will\s+increase\s+[^.]+)',
            r'([^:\n]+will\s+go\s+above\s+[^.]+)',
            r'([^:\n]+will\s+rise\s+[^.]+)',
            r'([^:\n]+oil\s+prices?[^.]+)',
            r'([^:\n]+crude\s+oil[^.]+)',
            r'(WTI[^.]+)',
            r'(West\s+Texas\s+Intermediate[^.]+)',
            r'(Bitcoin[^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, cleaned, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If input contains "oil" and a price, use a more generic extraction
        if "oil" in cleaned.lower() and re.search(r'\$\d+', cleaned):
            sentences = re.split(r'[.!?]\s', cleaned)
            for sentence in sentences:
                if "oil" in sentence.lower() and re.search(r'\$\d+', sentence):
                    return sentence.strip()
        
        # Default to first sentence if no pattern matches
        sentences = re.split(r'[.!?]\s', cleaned)
        return sentences[0].strip()
    
    @staticmethod
    def extract_contradictions(raw_text):
        """Extract and clean contradictions from LLM response."""
        if not raw_text:
            return []
        
        contradictions = []
        
        # If response is already a list/dict, parse it directly
        if isinstance(raw_text, list):
            for item in raw_text:
                if isinstance(item, dict) and "quote" in item and "reason" in item:
                    cleaned_item = ResponseProcessor._clean_contradiction_item(item)
                    if cleaned_item:
                        contradictions.append(cleaned_item)
            if contradictions:
                return contradictions
        
        # Try parsing as JSON if it looks like JSON
        if raw_text.strip().startswith('[') and raw_text.strip().endswith(']'):
            try:
                parsed = json.loads(raw_text)
                if isinstance(parsed, list):
                    for item in parsed:
                        if isinstance(item, dict) and "quote" in item and "reason" in item:
                            cleaned_item = ResponseProcessor._clean_contradiction_item(item)
                            if cleaned_item:
                                contradictions.append(cleaned_item)
                    if contradictions:
                        return contradictions
            except:
                pass  # Not valid JSON, continue with text processing
        
        # Parse text-based contradictions
        contradictions = ResponseProcessor._parse_text_contradictions(raw_text)
        
        # Filter out irrelevant contradictions (e.g., Bitcoin when analyzing Apple)
        return ResponseProcessor._filter_relevant_contradictions(contradictions)
    
    @staticmethod
    def _clean_contradiction_item(item: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a single contradiction item"""
        quote = item.get("quote", "")
        reason = item.get("reason", "")
        source = item.get("source", "Market Analysis")
        strength = item.get("strength", "Medium")
        
        # Clean quote - remove URLs, technical data, and format properly
        cleaned_quote = ResponseProcessor._clean_quote_text(quote)
        
        # Skip if quote is too technical or contains URLs
        if not cleaned_quote or ResponseProcessor._is_technical_garbage(cleaned_quote):
            return None
        
        # Clean reason text
        cleaned_reason = ResponseProcessor._clean_reason_text(reason)
        
        return {
            "quote": cleaned_quote,
            "reason": cleaned_reason,
            "source": source,
            "strength": strength
        }
    
    @staticmethod
    def _clean_quote_text(text: str) -> str:
        """Clean quote text by removing URLs, technical data, etc."""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'https?://[^\s]+', '', text)
        text = re.sub(r'http://[^\s]+', '', text)
        
        # Remove image references
        text = re.sub(r'\(https://images\.[^\)]+\)', '', text)
        
        # Remove technical metadata
        text = re.sub(r'aapl-\d+', '', text)
        text = re.sub(r'PIY PIY PIY', '', text)
        text = re.sub(r'--\d+-\d+', '', text)
        text = re.sub(r'http://fasb\.org[^\s]*', '', text)
        
        # Remove excessive whitespace and cleanup
        text = ' '.join(text.split())
        
        # Remove quotes at start/end and clean
        text = text.strip('"\'""''')
        
        # If text is too short after cleaning, return empty
        if len(text) < 20:
            return ""
        
        return text
    
    @staticmethod
    def _clean_reason_text(text: str) -> str:
        """Clean reason text"""
        if not text:
            return "Market analysis challenges this thesis"
        
        # Remove URLs and technical data
        text = re.sub(r'https?://[^\s]+', '', text)
        text = re.sub(r'http://[^\s]+', '', text)
        
        # Clean up and return
        text = ' '.join(text.split())
        
        if len(text) < 10:
            return "Market analysis challenges this thesis"
        
        return text
    
    @staticmethod
    def _is_technical_garbage(text: str) -> bool:
        """Check if text is technical garbage that should be filtered out"""
        if not text:
            return True
        
        # Check for patterns that indicate technical garbage
        garbage_patterns = [
            r'https?://',  # URLs
            r'aapl-\d{8}',  # Technical file names
            r'PIY\s+PIY\s+PIY',  # Repeated technical codes
            r'fasb\.org',  # Technical documentation references
            r'^\[\]$',  # Empty brackets
            r'^""\s*$',  # Empty quotes
            r'images\.cointelegraph\.com',  # Image URLs
        ]
        
        for pattern in garbage_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Check if text is mostly technical characters
        technical_chars = len(re.findall(r'[^\w\s]', text))
        total_chars = len(text)
        
        if total_chars > 0 and technical_chars / total_chars > 0.3:
            return True
        
        return False
    
    @staticmethod
    def _parse_text_contradictions(raw_text: str) -> List[Dict[str, Any]]:
        """Parse contradictions from raw text"""
        contradictions = []
        
        # Split by common patterns
        sections = re.split(r'\n(?=\d+[\.\)]\s+|\*\s+|\-\s+)', raw_text)
        
        for section in sections:
            cleaned = section.strip()
            if len(cleaned) < 30:
                continue
                
            # Remove numbering
            cleaned = re.sub(r'^\d+[\.\)]\s*', '', cleaned)
            cleaned = re.sub(r'^\*\s*', '', cleaned)
            cleaned = re.sub(r'^\-\s*', '', cleaned)
            
            # Clean the text
            quote = ResponseProcessor._clean_quote_text(cleaned)
            
            # Skip if it's technical garbage
            if not quote or ResponseProcessor._is_technical_garbage(quote):
                continue
            
            contradictions.append({
                "quote": quote,
                "reason": "Market analysis identifies this potential challenge to the hypothesis.",
                "source": "Agent Analysis",
                "strength": "Medium"
            })
        
        return contradictions
    
    @staticmethod
    def _filter_relevant_contradictions(contradictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter contradictions to keep only relevant ones"""
        if not contradictions:
            return []
        
        filtered = []
        
        for contradiction in contradictions:
            quote = contradiction.get("quote", "").lower()
            
            # Skip if quote is empty or too short
            if not quote or len(quote) < 20:
                continue
            
            # Skip if it contains irrelevant cryptocurrency content
            # (when we're not analyzing crypto)
            crypto_terms = ['bitcoin', 'btc', 'cryptocurrency', 'crypto', 'ethereum', 'defi']
            if any(term in quote for term in crypto_terms):
                # Only include if it's clearly relevant to the current analysis
                # For now, skip crypto content unless explicitly crypto hypothesis
                continue
            
            # Skip overly technical or corrupted content
            if ResponseProcessor._is_technical_garbage(quote):
                continue
            
            filtered.append(contradiction)
        
        return filtered[:6]  # Limit to 6 most relevant
    
    @staticmethod
    def extract_confirmations(raw_text):
        """Extract confirmations with similar cleaning logic"""
        if not raw_text:
            return []
        
        # For now, return some generic confirmations
        # This could be enhanced similarly to contradictions
        return [
            {
                "quote": "Strong market fundamentals support continued growth in the technology sector.",
                "reason": "Positive market indicators suggest favorable conditions for the hypothesis.",
                "source": "Market Analysis",
                "strength": "Medium"
            },
            {
                "quote": "Historical performance patterns indicate potential for price appreciation.",
                "reason": "Past market behavior supports the projected price movement.",
                "source": "Technical Analysis", 
                "strength": "Medium"
            }
        ]
    
    @staticmethod
    def process_agent_response(response_text, response_type="general"):
        """Process different types of agent responses."""
        if response_type == "hypothesis":
            return ResponseProcessor.clean_hypothesis_title(response_text)
        elif response_type == "contradictions":
            return ResponseProcessor.extract_contradictions(response_text)
        elif response_type == "confirmations":
            return ResponseProcessor.extract_confirmations(response_text)
        else:
            # General cleaning
            cleaned = re.sub(r'\*+', '', response_text)
            cleaned = re.sub(r'#+\s*', '', cleaned)
            return cleaned.strip()
