# app/adk/agents/model_integration.py - ADK Model Integration for Enhanced Processing
import asyncio
import json
import re
from typing import Dict, Any, List, Optional
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

class ADKModelIntegrator:
    """Handles actual ADK model calls for enhanced processing logic."""
    
    def __init__(self, agent, session_service: InMemorySessionService):
        self.agent = agent
        self.session_service = session_service
        self.app_name = f"tradesage_processor_{agent.name}"
        self.user_id = "tradesage_processor"
    
    async def generate_content(self, prompt: str, context_id: str = None) -> str:
        """Generate content using the ADK agent model."""
        try:
            # Create unique session for this generation
            session_id = f"gen_{context_id or 'default'}_{id(prompt)}"
            
            # Create session
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=session_id
            )
            
            # Create runner
            runner = Runner(
                agent=self.agent,
                app_name=self.app_name,
                session_service=self.session_service
            )
            
            # Format message
            message = types.Content(
                role='user',
                parts=[types.Part(text=prompt)]
            )
            
            # Run and collect response
            response_parts = []
            
            async for event in runner.run_async(
                user_id=self.user_id,
                session_id=session_id,
                new_message=message
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                response_parts.append(part.text)
            
            return " ".join(response_parts) if response_parts else ""
            
        except Exception as e:
            print(f"❌ ADK model generation failed: {str(e)}")
            return ""
    
    def generate_content_sync(self, prompt: str, context_id: str = None) -> str:
        """Synchronous wrapper for content generation."""
        try:
            # Check if we're in an event loop
            loop = asyncio.get_running_loop()
            # We're in an async context, but we need to run in a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._run_in_new_loop, prompt, context_id)
                return future.result(timeout=30)
        except RuntimeError:
            # No event loop running, we can run directly
            return asyncio.run(self.generate_content(prompt, context_id))
    
    def _run_in_new_loop(self, prompt: str, context_id: str = None) -> str:
        """Run generation in a new event loop."""
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(self.generate_content(prompt, context_id))
        finally:
            new_loop.close()
