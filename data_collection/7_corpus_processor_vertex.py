# corpus_processor_vertex.py
import os
import json
import html2text
from bs4 import BeautifulSoup
import pandas as pd
import glob
import uuid
from datetime import datetime
from tqdm import tqdm
import argparse
from google.cloud import aiplatform
from typing import List, Dict, Any, Optional

# Google Cloud imports
from google.cloud import storage
from google.cloud import aiplatform_v1

# Set up environment
PROJECT_ID = "your-gcp-project-id"  # Update with your Google Cloud project ID
LOCATION = "us-central1"             # Choose appropriate region
CORPUS_NAME = "tradesage-corpus"     # Name for your vector database

# Initialize Google Cloud clients
aiplatform.init(project=PROJECT_ID, location=LOCATION)
storage_client = storage.Client(project=PROJECT_ID)

# Create a directory for processed documents
OUTPUT_DIR = "processed_corpus"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def preprocess_text(text):
    """Clean and normalize text content"""
    # Convert HTML to plain text if it contains HTML tags
    if "<" in text and ">" in text:
        h = html2text.HTML2Text()
        h.ignore_links = False
        text = h.handle(text)
    
    # Basic cleaning
    text = text.replace("\n\n", " ").replace("\t", " ").strip()
    
    # Remove excessive whitespace
    text = " ".join(text.split())
    
    return text

def convert_html_to_text(html_content):
    """Convert HTML content to plain text"""
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text(separator="\n")

def process_json_files(directory):
    """Process JSON files and extract text content"""
    processed_documents = []
    
    # Get all JSON files recursively
    json_files = glob.glob(f"{directory}/**/*.json", recursive=True)
    
    for file_path in tqdm(json_files, desc="Processing JSON files"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract instrument from path
            parts = file_path.split(os.path.sep)
            instrument = parts[-2] if len(parts) >= 2 else "unknown"
            source_type = parts[-3] if len(parts) >= 3 else "unknown"
            
            # Handle different JSON structures
            if isinstance(data, list):
                # List of articles
                for item in data:
                    doc = extract_text_from_item(item, instrument, source_type, file_path)
                    if doc:
                        processed_documents.append(doc)
            else:
                # Single document
                doc = extract_text_from_item(data, instrument, source_type, file_path)
                if doc:
                    processed_documents.append(doc)
                    
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    return processed_documents

def extract_text_from_item(item, instrument, source_type, file_path):
    """Extract text content from a JSON item"""
    
    # Define possible field names for title and content
    title_fields = ["title", "headline", "name", "symbol"]
    content_fields = ["text", "content", "summary", "description", "analysis_text", "article"]
    
    # Find title
    title = None
    for field in title_fields:
        if field in item and item[field]:
            title = item[field]
            break
    
    # Find content text
    content = None
    for field in content_fields:
        if field in item and item[field]:
            content = item[field]
            break
    
    # Extract nested content if necessary
    if not content and isinstance(item, dict):
        # Look one level deeper for content
        for key, value in item.items():
            if isinstance(value, dict):
                for field in content_fields:
                    if field in value and value[field]:
                        content = value[field]
                        break
    
    # Skip if no useful content
    if not content or len(content) < 50:  # Skip very short content
        return None
    
    # Clean text
    content = preprocess_text(content)
    
    # Extract date if available
    date = None
    date_fields = ["date", "publish_date", "published", "timestamp", "created_at"]
    for field in date_fields:
        if field in item and item[field]:
            date = item[field]
            break
    
    # Format date consistently
    if date:
        try:
            # Try to parse date strings to a standard format
            if isinstance(date, str):
                if 'T' in date:  # ISO format
                    date = date.split('T')[0]
                elif '/' in date:  # MM/DD/YYYY
                    parts = date.split('/')
                    if len(parts) == 3:
                        date = f"{parts[2]}-{parts[0]}-{parts[1]}"
        except:
            date = None
    
    # Construct document
    doc = {
        "id": str(uuid.uuid4()),
        "title": title if title else "Untitled Document",
        "content": content,
        "instrument": instrument,
        "source_type": source_type,
        "file_path": file_path,
        "date": date if date else "Unknown",
        "metadata": {
            "instrument": instrument,
            "source_type": source_type,
            "has_title": bool(title)
        }
    }
    
    return doc

def process_html_files(directory):
    """Process HTML files (like SEC filings)"""
    processed_documents = []
    
    # Get all HTML files recursively
    html_files = glob.glob(f"{directory}/**/*.html", recursive=True)
    
    for file_path in tqdm(html_files, desc="Processing HTML files"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract instrument from path
            parts = file_path.split(os.path.sep)
            instrument = parts[-2] if len(parts) >= 2 else "unknown"
            source_type = parts[-3] if len(parts) >= 3 else "unknown"
            
            # Convert to text
            content = convert_html_to_text(html_content)
            
            # Clean content
            content = preprocess_text(content)
            
            # Skip if content is too short
            if len(content) < 100:
                continue
            
            # Extract title from filename
            filename = os.path.basename(file_path)
            title = filename.replace('.html', '').replace('_', ' ')
            
            # Construct document
            doc = {
                "id": str(uuid.uuid4()),
                "title": title,
                "content": content,
                "instrument": instrument,
                "source_type": source_type,
                "file_path": file_path,
                "date": "Unknown",
                "metadata": {
                    "instrument": instrument,
                    "source_type": source_type,
                    "has_title": True
                }
            }
            
            processed_documents.append(doc)
                    
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    return processed_documents

def chunk_document(doc, chunk_size=512, overlap=50):
    """Split document into chunks for embedding"""
    content = doc["content"]
    
    # Simple paragraph-based chunking
    paragraphs = content.split("\n\n")
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += para + "\n\n"
        else:
            # If the chunk is not empty, add it to chunks
            if current_chunk:
                chunk_doc = doc.copy()
                chunk_doc["id"] = f"{doc['id']}_chunk_{len(chunks)}"
                chunk_doc["content"] = current_chunk.strip()
                chunks.append(chunk_doc)
            
            # Start a new chunk
            current_chunk = para + "\n\n"
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunk_doc = doc.copy()
        chunk_doc["id"] = f"{doc['id']}_chunk_{len(chunks)}"
        chunk_doc["content"] = current_chunk.strip()
        chunks.append(chunk_doc)
    
    return chunks

def create_vertex_index():
    """Create a Vector Search index in Vertex AI"""
    
    # Check if index already exists
    indexes = aiplatform.MatchingEngineIndex.list(
        filter=f'display_name="{CORPUS_NAME}"'
    )
    
    if indexes:
        print(f"Index '{CORPUS_NAME}' already exists, using existing index")
        return indexes[0]
    
    # Create a new Vector Search index
    dimensions = 768  # Default for text-embedding-gecko model
    
    index = aiplatform.MatchingEngineIndex.create(
        display_name=CORPUS_NAME,
        dimensions=dimensions,
        description="TradeSage financial document corpus",
        metadata_schema={
            "instrument": "STRING",
            "source_type": "STRING", 
            "has_title": "BOOL"
        }
    )
    
    print(f"Created new Vector Search index: {index.name}")
    
    # Wait for the index to be ready
    index.wait()
    
    return index

def upload_to_gcs(documents, bucket_name):
    """Upload documents to GCS for batch indexing"""
    
    # Create or get the bucket
    try:
        bucket = storage_client.get_bucket(bucket_name)
    except:
        bucket = storage_client.create_bucket(bucket_name, location=LOCATION)
    
    # Create a JSONL file with documents
    jsonl_path = f"{OUTPUT_DIR}/documents.jsonl"
    with open(jsonl_path, 'w') as f:
        for doc in documents:
            f.write(json.dumps(doc) + '\n')
    
    # Upload to GCS
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    blob_name = f"tradesage_corpus/{timestamp}/documents.jsonl"
    blob = bucket.blob(blob_name)
    
    blob.upload_from_filename(jsonl_path)
    print(f"Uploaded documents to gs://{bucket_name}/{blob_name}")
    
    return f"gs://{bucket_name}/{blob_name}"

def embed_and_index_documents(documents, index):
    """Generate embeddings and index documents with Vertex AI"""
    
    # First, upload documents to GCS
    gcs_bucket = f"{PROJECT_ID}-tradesage-corpus"
    gcs_uri = upload_to_gcs(documents, gcs_bucket)
    
    # Create an index endpoint if one doesn't exist
    endpoints = aiplatform.MatchingEngineIndexEndpoint.list(
        filter='display_name="tradesage-endpoint"'
    )
    
    if endpoints:
        endpoint = endpoints[0]
        print(f"Using existing index endpoint: {endpoint.name}")
    else:
        endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
            display_name="tradesage-endpoint",
            description="Endpoint for TradeSage corpus",
        )
        print(f"Created new index endpoint: {endpoint.name}")
    
    # Deploy the index to the endpoint
    endpoint.deploy_index(
        index=index,
        deployed_index_id="tradesage-deployed",
    )
    
    # Create a batch indexing job
    batch_indexing_job = aiplatform.BatchPredictionJob.create(
        job_display_name="tradesage-indexing",
        model=None,  # No model needed for embedding-only job
        generate_explanations=False,
        machine_type="n1-standard-2",
        input_config={
            "instance_config": {
                "gcs_source": {"uri_prefix": gcs_uri},
            },
            "format": "jsonl",
        },
        output_config={
            "gcs_destination": {"output_uri_prefix": f"gs://{gcs_bucket}/embeddings"},
            "format": "jsonl",
        },
        embedding_endpoints={
            "indexing_endpoint": "{}.{}.aiplatform.googleapis.com".format(PROJECT_ID, LOCATION)
        }
    )
    
    print(f"Started batch indexing job: {batch_indexing_job.name}")
    batch_indexing_job.wait()
    
    print("Indexing completed!")
    return endpoint

def main():
    # Process corpus files
    print("Processing documents...")
    json_documents = process_json_files("news") + \
                     process_json_files("analyst_reports") + \
                     process_json_files("technical_analysis")
    html_documents = process_html_files("earnings")
    
    all_documents = json_documents + html_documents
    print(f"Processed {len(all_documents)} documents")
    
    # Chunk documents
    chunked_documents = []
    for doc in tqdm(all_documents, desc="Chunking documents"):
        chunks = chunk_document(doc)
        chunked_documents.extend(chunks)
    
    print(f"Created {len(chunked_documents)} chunks from {len(all_documents)} documents")
    
    # Save processed documents locally as backup
    output_path = f"{OUTPUT_DIR}/processed_documents.jsonl"
    with open(output_path, 'w') as f:
        for doc in chunked_documents:
            f.write(json.dumps(doc) + '\n')
    
    print(f"Saved processed documents to {output_path}")
    
    # Create Vertex AI Vector Search index
    index = create_vertex_index()
    
    # Embed and index documents
    endpoint = embed_and_index_documents(chunked_documents, index)
    
    print("Corpus processing and indexing complete!")
    print(f"Index name: {index.name}")
    print(f"Endpoint: {endpoint.name}")
    
    # Save metadata for reference
    metadata = {
        "corpus_size": len(chunked_documents),
        "original_documents": len(all_documents),
        "instruments": list(set(doc["instrument"] for doc in all_documents)),
        "source_types": list(set(doc["source_type"] for doc in all_documents)),
        "processed_date": datetime.now().isoformat(),
        "vertex_ai": {
            "project": PROJECT_ID,
            "location": LOCATION,
            "index_name": index.name,
            "endpoint_name": endpoint.name
        }
    }
    
    with open(f"{OUTPUT_DIR}/corpus_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Saved corpus metadata to {OUTPUT_DIR}/corpus_metadata.json")

if __name__ == "__main__":
    main()
