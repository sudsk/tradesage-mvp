# app/utils/database_cleaner.py - Clean and truncate data for database storage

import re
from typing import Dict, Any, List

class DatabaseDataCleaner:
    """Clean and truncate data to fit database schema constraints"""
    
    # Database column limits (from your schema)
    COLUMN_LIMITS = {
        'source': 500,        # source column limit
        'strength': 50,       # strength column limit  
        'quote': 2000,        # assuming TEXT field, but let's be safe
        'reason': 2000,       # assuming TEXT field, but let's be safe
        'url': 1000,          # url column limit
        'title': 500,         # hypothesis title limit
        'description': 5000,  # description limit
        'thesis': 5000,       # thesis limit
        'message': 2000,      # alert message limit
        'alert_type': 50,     # alert type limit
        'priority': 50        # priority limit
    }
    
    @classmethod
    def clean_contradiction(cls, contradiction: Dict[str, Any]) -> Dict[str, Any]:
        """Clean contradiction data for database storage"""
        
        cleaned = {}
        
        # Clean quote - remove markdown and formatting
        quote = contradiction.get("quote", "")
        cleaned["quote"] = cls._clean_and_truncate_text(quote, cls.COLUMN_LIMITS['quote'])
        
        # Clean reason
        reason = contradiction.get("reason", "")
        cleaned["reason"] = cls._clean_and_truncate_text(reason, cls.COLUMN_LIMITS['reason'])
        
        # Clean source - remove long descriptions
        source = contradiction.get("source", "Market Analysis")
        cleaned["source"] = cls._clean_and_truncate_text(source, cls.COLUMN_LIMITS['source'])
        
        # Clean strength - standardize values
        strength = contradiction.get("strength", "Medium")
        cleaned["strength"] = cls._standardize_strength(strength)
        
        # Handle URL if present
        url = contradiction.get("url", "")
        if url:
            cleaned["url"] = cls._clean_and_truncate_text(url, cls.COLUMN_LIMITS['url'])
        else:
            cleaned["url"] = None
            
        # Sentiment score
        cleaned["sentiment_score"] = contradiction.get("sentiment_score", None)
        
        return cleaned
    
    @classmethod
    def clean_confirmation(cls, confirmation: Dict[str, Any]) -> Dict[str, Any]:
        """Clean confirmation data for database storage"""
        
        cleaned = {}
        
        # Clean quote - remove markdown and formatting
        quote = confirmation.get("quote", "")
        cleaned["quote"] = cls._clean_and_truncate_text(quote, cls.COLUMN_LIMITS['quote'])
        
        # Clean reason
        reason = confirmation.get("reason", "")
        cleaned["reason"] = cls._clean_and_truncate_text(reason, cls.COLUMN_LIMITS['reason'])
        
        # Clean source
        source = confirmation.get("source", "Market Analysis")
        cleaned["source"] = cls._clean_and_truncate_text(source, cls.COLUMN_LIMITS['source'])
        
        # Clean strength
        strength = confirmation.get("strength", "Medium")
        cleaned["strength"] = cls._standardize_strength(strength)
        
        # Handle URL if present
        url = confirmation.get("url", "")
        if url:
            cleaned["url"] = cls._clean_and_truncate_text(url, cls.COLUMN_LIMITS['url'])
        else:
            cleaned["url"] = None
            
        # Sentiment score
        cleaned["sentiment_score"] = confirmation.get("sentiment_score", None)
        
        return cleaned
    
    @classmethod
    def clean_hypothesis_data(cls, hypothesis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean hypothesis data for database storage"""
        
        cleaned = {}
        
        # Clean title
        title = hypothesis_data.get("title", "")
        cleaned["title"] = cls._clean_and_truncate_text(title, cls.COLUMN_LIMITS['title'])
        
        # Clean description
        description = hypothesis_data.get("description", "")
        cleaned["description"] = cls._clean_and_truncate_text(description, cls.COLUMN_LIMITS['description'])
        
        # Clean thesis
        thesis = hypothesis_data.get("thesis", "")
        cleaned["thesis"] = cls._clean_and_truncate_text(thesis, cls.COLUMN_LIMITS['thesis'])
        
        # Copy other fields as-is
        for field in ['confidence_score', 'status', 'target_price', 'current_price', 'instruments', 'timeframe', 'success_criteria', 'risk_factors', 'created_at']:
            if field in hypothesis_data:
                cleaned[field] = hypothesis_data[field]
        
        return cleaned
    
    @classmethod
    def clean_alert_data(cls, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean alert data for database storage"""
        
        cleaned = {}
        
        # Clean message
        message = alert_data.get("message", "")
        cleaned["message"] = cls._clean_and_truncate_text(message, cls.COLUMN_LIMITS['message'])
        
        # Clean alert type
        alert_type = alert_data.get("alert_type", "recommendation")
        cleaned["alert_type"] = cls._clean_and_truncate_text(alert_type, cls.COLUMN_LIMITS['alert_type'])
        
        # Clean priority
        priority = alert_data.get("priority", "medium")
        cleaned["priority"] = cls._standardize_priority(priority)
        
        # Copy other fields
        for field in ['hypothesis_id', 'is_read']:
            if field in alert_data:
                cleaned[field] = alert_data[field]
        
        return cleaned
    
    @classmethod
    def _clean_and_truncate_text(cls, text: str, max_length: int) -> str:
        """Clean and truncate text to fit database constraints"""
        
        if not text:
            return ""
        
        # Remove markdown formatting
        cleaned = cls._remove_markdown_formatting(text)
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove special characters that might cause issues
        cleaned = re.sub(r'[^\w\s\-\.\,\(\)\[\]\!\?\:\;\'\"\/\%\$\&\+\=]', '', cleaned)
        
        # Truncate to max length
        if len(cleaned) > max_length:
            # Truncate at word boundary if possible
            truncated = cleaned[:max_length-3]
            last_space = truncated.rfind(' ')
            if last_space > max_length * 0.8:  # If we can save most of the text
                truncated = truncated[:last_space]
            cleaned = truncated + "..."
        
        return cleaned.strip()
    
    @classmethod
    def _remove_markdown_formatting(cls, text: str) -> str:
        """Remove markdown formatting from text"""
        
        # Remove markdown headers
        text = re.sub(r'#+\s*', '', text)
        
        # Remove markdown bold/italic
        text = re.sub(r'\*+([^*]+)\*+', r'\1', text)
        text = re.sub(r'_+([^_]+)_+', r'\1', text)
        
        # Remove markdown links
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Remove markdown code blocks
        text = re.sub(r'```[^`]*```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Remove markdown lists
        text = re.sub(r'^\s*[\-\*\+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Remove leading/trailing quotes and asterisks
        text = re.sub(r'^[\*\"\'\s]+', '', text)
        text = re.sub(r'[\*\"\'\s]+$', '', text)
        
        return text
    
    @classmethod
    def _standardize_strength(cls, strength: str) -> str:
        """Standardize strength values to fit database constraints"""
        
        if not strength:
            return "Medium"
        
        strength_lower = strength.lower().strip()
        
        # Handle various formats
        if any(word in strength_lower for word in ['strong', 'high']):
            return "Strong"
        elif any(word in strength_lower for word in ['weak', 'low']):
            return "Weak"
        else:
            return "Medium"
    
    @classmethod
    def _standardize_priority(cls, priority: str) -> str:
        """Standardize priority values"""
        
        if not priority:
            return "medium"
        
        priority_lower = priority.lower().strip()
        
        if 'high' in priority_lower:
            return "high"
        elif 'low' in priority_lower:
            return "low"
        else:
            return "medium"
    
    @classmethod
    def clean_contradictions_list(cls, contradictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean a list of contradictions"""
        return [cls.clean_contradiction(c) for c in contradictions if c]
    
    @classmethod
    def clean_confirmations_list(cls, confirmations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean a list of confirmations"""
        return [cls.clean_confirmation(c) for c in confirmations if c]
    
    @classmethod
    def clean_alerts_list(cls, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean a list of alerts"""
        cleaned_alerts = []
        for alert in alerts:
            if isinstance(alert, dict):
                cleaned_alerts.append(cls.clean_alert_data(alert))
            elif isinstance(alert, str):
                # Convert string alerts to proper format
                cleaned_alerts.append({
                    "message": cls._clean_and_truncate_text(alert, cls.COLUMN_LIMITS['message']),
                    "alert_type": "recommendation",
                    "priority": "medium"
                })
        return cleaned_alerts
