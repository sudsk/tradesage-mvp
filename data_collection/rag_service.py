# rag_service.py
import os
import json
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
import vertexai

class VertexRAGService:
    """Service for RAG using Vertex AI Vector Search"""
    
    def __init__(self, metadata_path="processed_corpus/corpus_metadata.json"):
        """Initialize the RAG service"""
        self.metadata = self._load_metadata(metadata_path)
        self.project_id, self.location = self._initialize_vertex_ai()
        self.embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
        
        # Get the endpoint
        self.endpoint = aiplatform.MatchingEngineIndexEndpoint(
            self.metadata["vertex_ai"]["endpoint_name"]
        )
    
    def _load_metadata(self, metadata_path):
        """Load corpus metadata"""
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    def _initialize_vertex_ai(self):
        """Initialize Vertex AI"""
        project_id = self.metadata["vertex_ai"]["project"]
        location = self.metadata["vertex_ai"]["location"]
        
        vertexai.init(project=project_id, location=location)
        return project_id, location
    
    def _generate_embedding(self, text):
        """Generate embedding for text"""
        embeddings = self.embedding_model.get_embeddings([text])
        return embeddings[0].values
    
    def query(self, query_text, filter_options=None, num_results=5):
        """Query the Vector Search index with optional filters"""
        # Generate embedding for the query
        query_embedding = self._generate_embedding(query_text)
        
        # Construct filter string if provided
        filter_string = None
        if filter_options:
            filters = []
            if "instrument" in filter_options:
                filters.append(f'instrument = "{filter_options["instrument"]}"')
            if "source_type" in filter_options:
                filters.append(f'source_type = "{filter_options["source_type"]}"')
            
            if filters:
                filter_string = " AND ".join(filters)
        
        # Query the index
        response = self.endpoint.find_neighbors(
            deployed_index_id="tradesage-deployed",
            queries=[query_embedding],
            num_neighbors=num_results,
            filter=filter_string
        )
        
        # Process results
        return response[0]
    
    def search_by_instrument(self, query_text, instrument, num_results=5):
        """Convenience method to search specifically for an instrument"""
        return self.query(
            query_text,
            filter_options={"instrument": instrument},
            num_results=num_results
        )
    
    def search_by_source_type(self, query_text, source_type, num_results=5):
        """Convenience method to search by source type"""
        return self.query(
            query_text,
            filter_options={"source_type": source_type},
            num_results=num_results
        )

# Example usage in an agent
def use_rag_in_agent():
    # Initialize the RAG service
    rag_service = VertexRAGService()
    
    # Example: Research Agent using RAG
    def research_agent_with_rag(hypothesis, instruments):
        research_data = {}
        
        for instrument in instruments:
            # Query the RAG for instrument-specific research
            results = rag_service.search_by_instrument(
                f"Latest analysis and news about {instrument} related to {hypothesis}",
                instrument,
                num_results=3
            )
            
            # Process results
            instrument_data = {
                "relevant_documents": [
                    {
                        "id": match.id,
                        "distance": match.distance,
                        "metadata": match.metadata
                    }
                    for match in results
                ]
            }
            
            research_data[instrument] = instrument_data
        
        return research_data
    
    # Example: Contradiction Agent using RAG
    def contradiction_agent_with_rag(hypothesis, instruments):
        contradiction_data = []
        
        for instrument in instruments:
            # Query for contradictory information
            results = rag_service.search_by_instrument(
                f"Evidence against {hypothesis} related to {instrument}",
                instrument,
                num_results=5
            )
            
            # Process results into contradictions
            for match in results:
                contradiction = {
                    "quote": match.id,  # This would actually come from document content
                    "source": match.metadata.get("source_type", "Unknown"),
                    "instrument": match.metadata.get("instrument", "Unknown"),
                    "relevance_score": 1.0 - match.distance  # Convert distance to similarity
                }
                contradiction_data.append(contradiction)
        
        return contradiction_data
    
    # Test the agents
    hypothesis = "Oil prices will rise due to OPEC+ production cuts"
    instruments = ["Brent Crude", "AAPL", "NVDA"]
    
    research = research_agent_with_rag(hypothesis, instruments)
    contradictions = contradiction_agent_with_rag(hypothesis, instruments)
    
    print(json.dumps(research, indent=2))
    print(json.dumps(contradictions, indent=2))

if __name__ == "__main__":
    use_rag_in_agent()
