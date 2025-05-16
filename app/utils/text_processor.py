# app/utils/text_processor.py
import re
import json

class ResponseProcessor:
    @staticmethod
    def clean_hypothesis_title(raw_title):
        """Extract clean hypothesis title from LLM response."""
        if not raw_title:
            return "Untitled Hypothesis"
        
        # Remove markdown formatting
        cleaned = re.sub(r'\*+', '', raw_title)
        
        # Extract just the hypothesis statement, not the meta-description
        # Look for patterns like "Hypothesis:", "Initial Hypothesis:", etc.
        patterns = [
            r'(?:initial\s+)?hypothesis[:]\s*["\']?([^"\']+)["\']?',
            r'hypothesis\s+validation.*?initial\s+hypothesis[:]\s*["\']?([^"\']+)["\']?',
            r'^([^#*]+?)(?:\s+will\s+|\s+should\s+|\s+is\s+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, cleaned, re.IGNORECASE | re.DOTALL)
            if match:
                hypothesis = match.group(1).strip()
                # Take only the first sentence/line
                hypothesis = hypothesis.split('\n')[0]
                hypothesis = hypothesis.split('.')[0]
                if len(hypothesis) > 10:  # Valid hypothesis
                    return hypothesis
        
        # Fallback: take first meaningful line
        lines = cleaned.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 10 and not line.startswith('#') and 'breakdown' not in line.lower():
                return line
        
        return raw_title[:100] + "..." if len(raw_title) > 100 else raw_title
    
    @staticmethod
    def extract_contradictions(raw_text):
        """Extract clean contradictions from LLM response."""
        if not raw_text:
            return []
        
        contradictions = []
        
        # Split by common patterns
        sections = re.split(r'\n(?=\d+\.|\*|\-)', raw_text)
        
        for section in sections:
            # Clean up the section
            cleaned = re.sub(r'\*+', '', section).strip()
            
            # Skip meta-text and headers
            skip_patterns = [
                r'^alright,.*hypothesis',
                r'^here are.*contradictions',
                r'^major counter-arguments',
                r'^potential data that contradicts',
                r'^\d+\.\s*major counter-arguments',
                r'^\d+\.\s*potential data',
                r'^let\'s dissect',
                r'^i\'ll challenge'
            ]
            
            if any(re.match(pattern, cleaned, re.IGNORECASE) for pattern in skip_patterns):
                continue
                
            # Extract actual contradiction content
            if len(cleaned) > 30:  # Valid contradiction
                # Remove numbering
                cleaned = re.sub(r'^\d+\.\s*', '', cleaned)
                
                # Extract quote and reasoning
                quote_match = re.search(r'["\'""]([^"\'""]+)["\'""]', cleaned)
                if quote_match:
                    quote = quote_match.group(1).strip()
                    reasoning = re.sub(r'["\'""]([^"\'""]+)["\'""]', '', cleaned).strip()
                    reasoning = reasoning.split('Analysis:')[-1].split('Reason:')[-1].strip()
                    
                    contradictions.append({
                        "quote": quote,
                        "reason": reasoning or "Market analysis challenges this thesis",
                        "source": "Agent Analysis",
                        "strength": "Medium"
                    })
                else:
                    # No explicit quote, use the whole text as reasoning
                    contradictions.append({
                        "quote": cleaned[:100] + "..." if len(cleaned) > 100 else cleaned,
                        "reason": cleaned,
                        "source": "Agent Analysis", 
                        "strength": "Medium"
                    })
        
        return contradictions
    
    @staticmethod
    def extract_confirmations(raw_text):
        """Extract clean confirmations from LLM response."""
        # Similar to contradictions but for supporting evidence
        if not raw_text:
            return []
            
        confirmations = []
        
        # Split by common patterns
        sections = re.split(r'\n(?=\d+\.|\*|\-)', raw_text)
        
        for section in sections:
            cleaned = re.sub(r'\*+', '', section).strip()
            
            # Skip headers and meta-text
            skip_patterns = [
                r'^here.*confirmations',
                r'^supporting evidence',
                r'^data that supports',
                r'^\d+\.\s*supporting evidence'
            ]
            
            if any(re.match(pattern, cleaned, re.IGNORECASE) for pattern in skip_patterns):
                continue
                
            if len(cleaned) > 30:
                cleaned = re.sub(r'^\d+\.\s*', '', cleaned)
                
                quote_match = re.search(r'["\'""]([^"\'""]+)["\'""]', cleaned)
                if quote_match:
                    quote = quote_match.group(1).strip()
                    reasoning = re.sub(r'["\'""]([^"\'""]+)["\'""]', '', cleaned).strip()
                    reasoning = reasoning.split('Analysis:')[-1].split('Reason:')[-1].strip()
                    
                    confirmations.append({
                        "quote": quote,
                        "reason": reasoning or "Market data supports this thesis",
                        "source": "Agent Analysis",
                        "strength": "Strong"
                    })
                else:
                    confirmations.append({
                        "quote": cleaned[:100] + "..." if len(cleaned) > 100 else cleaned,
                        "reason": cleaned,
                        "source": "Agent Analysis",
                        "strength": "Strong"
                    })
        
        return confirmations
    
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
