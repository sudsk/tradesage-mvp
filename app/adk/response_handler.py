# app/adk/response_handler.py - Enhanced response handling for ADK agents with function calls
import json
from typing import Dict, Any, List, Optional
from google.genai import types

class ADKResponseHandler:
    """Handle ADK agent responses including function calls and text parts."""
    
    @staticmethod
    def extract_complete_response(events: List[Any]) -> Dict[str, Any]:
        """Extract complete response including both text and function call results."""
        
        response_data = {
            "text_parts": [],
            "function_calls": [],
            "function_responses": [],
            "final_text": "",
            "tool_results": {},
            "errors": []
        }
        
        for event in events:
            try:
                if event.is_final_response():
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            # Handle text parts
                            if hasattr(part, 'text') and part.text:
                                response_data["text_parts"].append(part.text)
                            
                            # Handle function calls
                            elif hasattr(part, 'function_call') and part.function_call:
                                function_call = {
                                    "name": part.function_call.name,
                                    "args": dict(part.function_call.args) if part.function_call.args else {}
                                }
                                response_data["function_calls"].append(function_call)
                            
                            # Handle function responses
                            elif hasattr(part, 'function_response') and part.function_response:
                                function_response = {
                                    "name": part.function_response.name,
                                    "response": part.function_response.response
                                }
                                response_data["function_responses"].append(function_response)
                                
                                # Store tool results for easy access
                                response_data["tool_results"][part.function_response.name] = part.function_response.response
                
                # Handle streaming content events
                elif hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_data["text_parts"].append(part.text)
                
                # Handle errors
                elif hasattr(event, 'error') and event.error:
                    response_data["errors"].append(str(event.error))
                    
            except Exception as e:
                response_data["errors"].append(f"Error processing event: {str(e)}")
        
        # Combine all text parts
        response_data["final_text"] = " ".join(response_data["text_parts"])
        
        return response_data
    
    @staticmethod
    def format_research_response(response_data: Dict[str, Any]) -> str:
        """Format research response combining text and tool results."""
        
        formatted_sections = []
        
        # Add agent's text analysis
        if response_data["final_text"]:
            formatted_sections.append("## Agent Analysis")
            formatted_sections.append(response_data["final_text"])
        
        # Add tool results
        if response_data["tool_results"]:
            formatted_sections.append("\n## Tool Results")
            
            for tool_name, result in response_data["tool_results"].items():
                formatted_sections.append(f"\n### {tool_name}")
                
                try:
                    # Try to parse as JSON if it's structured data
                    if isinstance(result, str) and result.startswith('{'):
                        parsed_result = json.loads(result)
                        formatted_sections.append(f"Status: {parsed_result.get('status', 'unknown')}")
                        
                        # Format market data
                        if 'data' in parsed_result and 'info' in parsed_result['data']:
                            info = parsed_result['data']['info']
                            formatted_sections.append(f"Current Price: ${info.get('currentPrice', 'N/A')}")
                            formatted_sections.append(f"Daily Change: {info.get('dayChangePercent', 0):+.2f}%")
                            formatted_sections.append(f"Volume: {info.get('volume', 'N/A'):,}")
                        
                        # Format news data
                        elif 'articles' in parsed_result:
                            articles = parsed_result['articles'][:3]  # Top 3 articles
                            formatted_sections.append(f"Found {len(parsed_result['articles'])} articles")
                            for i, article in enumerate(articles, 1):
                                formatted_sections.append(f"{i}. {article.get('title', 'No title')}")
                    
                    else:
                        # Handle non-JSON results
                        result_str = str(result)
                        if len(result_str) > 200:
                            formatted_sections.append(result_str[:200] + "...")
                        else:
                            formatted_sections.append(result_str)
                            
                except Exception as e:
                    formatted_sections.append(f"Tool result (parsing failed): {str(result)[:100]}...")
        
        # Add function call summary
        if response_data["function_calls"]:
            formatted_sections.append(f"\n## Tools Used")
            for call in response_data["function_calls"]:
                formatted_sections.append(f"- {call['name']}: {call['args']}")
        
        # Add errors if any
        if response_data["errors"]:
            formatted_sections.append(f"\n## Errors")
            for error in response_data["errors"]:
                formatted_sections.append(f"- {error}")
        
        return "\n".join(formatted_sections)
    
    @staticmethod
    def extract_simple_text(response_data: Dict[str, Any]) -> str:
        """Extract simple text response for non-research agents."""
        return response_data.get("final_text", "")
    
    @staticmethod
    def has_tool_usage(response_data: Dict[str, Any]) -> bool:
        """Check if the response includes tool usage."""
        return bool(response_data.get("function_calls") or response_data.get("tool_results"))
    
    @staticmethod
    def get_tool_summary(response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of tool usage."""
        return {
            "tools_called": len(response_data.get("function_calls", [])),
            "tool_responses": len(response_data.get("function_responses", [])),
            "tool_names": [call["name"] for call in response_data.get("function_calls", [])],
            "has_errors": bool(response_data.get("errors")),
            "text_length": len(response_data.get("final_text", ""))
        }
