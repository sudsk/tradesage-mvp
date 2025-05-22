# query_vertex.py
import argparse
import json
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
import vertexai

def load_corpus_metadata(metadata_path="processed_corpus/corpus_metadata.json"):
    """Load corpus metadata with Vertex AI configuration"""
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    return metadata

def initialize_vertex_ai(metadata):
    """Initialize Vertex AI with the configuration from metadata"""
    project_id = metadata["vertex_ai"]["project"]
    location = metadata["vertex_ai"]["location"]
    
    vertexai.init(project=project_id, location=location)
    return project_id, location

def generate_embedding(text):
    """Generate embedding for query text using Vertex AI text embedding model"""
    embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
    embeddings = embedding_model.get_embeddings([text])
    return embeddings[0].values

def query_corpus(query_text, metadata, num_results=5):
    """Query the Vertex AI Vector Search index"""
    project_id, location = initialize_vertex_ai(metadata)
    
    # Get the index endpoint
    endpoint_name = metadata["vertex_ai"]["endpoint_name"]
    endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoint_name)
    
    # Generate embedding for the query
    query_embedding = generate_embedding(query_text)
    
    # Query the index
    response = endpoint.find_neighbors(
        deployed_index_id="tradesage-deployed",
        queries=[query_embedding],
        num_neighbors=num_results
    )
    
    # Process results
    matches = []
    for neighbor in response[0]:
        # Retrieve the document data
        matches.append({
            "id": neighbor.id,
            "distance": neighbor.distance,
            "metadata": neighbor.metadata
        })
    
    return matches

def main():
    parser = argparse.ArgumentParser(description="Query the TradeSage corpus")
    parser.add_argument("query", help="Query text to search for")
    parser.add_argument("--results", type=int, default=5, help="Number of results to return")
    parser.add_argument("--metadata", default="processed_corpus/corpus_metadata.json", 
                      help="Path to corpus metadata")
    args = parser.parse_args()
    
    # Load corpus metadata
    metadata = load_corpus_metadata(args.metadata)
    
    # Query the corpus
    results = query_corpus(args.query, metadata, args.results)
    
    # Display results
    print(f"Results for query: '{args.query}'")
    print("=" * 80)
    
    for i, result in enumerate(results):
        print(f"Result {i+1} (Distance: {result['distance']:.4f}):")
        print(f"ID: {result['id']}")
        print(f"Metadata: {json.dumps(result['metadata'], indent=2)}")
        print("-" * 80)

if __name__ == "__main__":
    main()
