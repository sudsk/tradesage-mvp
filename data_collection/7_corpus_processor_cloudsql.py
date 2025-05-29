# corpus_processor_cloudsql.py
import os
import json
import html2text
from bs4 import BeautifulSoup
import glob
import uuid
from datetime import datetime
from tqdm import tqdm
import time
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np

# Google Cloud and Vertex AI imports
from google.cloud.sql.connector import Connector
import vertexai
from vertexai.language_models import TextEmbeddingModel

# Configuration
PROJECT_ID = "your-gcp-project-id"
REGION = "us-central1"
INSTANCE_NAME = "tradesage-postgres"  # Your Cloud SQL instance name
DATABASE_NAME = "tradesage_db"
DB_USER = "postgres"
DB_PASSWORD = "your-secure-password"  # Set a secure password

# Initialize Vertex AI for embeddings
vertexai.init(project=PROJECT_ID, location=REGION)

# Create output directory
OUTPUT_DIR = "processed_corpus"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class CloudSQLVectorDB:
    """Cloud SQL PostgreSQL with pgvector for document storage and search"""
    
    def __init__(self, project_id, region, instance_name, database_name, user, password):
        self.project_id = project_id
        self.region = region
        self.instance_name = instance_name
        self.database_name = database_name
        self.user = user
        self.password = password
        self.connector = None
        self.connection = None
        
    def connect(self):
        """Connect to Cloud SQL using the Cloud SQL Python Connector"""
        try:
            # Initialize connector
            self.connector = Connector()
            
            # Create connection
            self.connection = self.connector.connect(
                f"{self.project_id}:{self.region}:{self.instance_name}",
                "pg8000",
                user=self.user,
                password=self.password,
                db=self.database_name
            )
            
            print(f"✅ Connected to Cloud SQL instance: {self.instance_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error connecting to Cloud SQL: {str(e)}")
            print(f"💡 Make sure your Cloud SQL instance is running and accessible")
            return False
    
    def setup_database(self):
        """Create the database schema with pgvector extension"""
        try:
            # Use cursor without context manager for pg8000/Cloud SQL Connector
            cursor = self.connection.cursor()
            
            try:
                # Enable pgvector extension
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                print("✅ pgvector extension enabled")
                
                # Create documents table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id UUID PRIMARY KEY,
                        title TEXT,
                        content TEXT,
                        instrument VARCHAR(50),
                        source_type VARCHAR(50),
                        file_path TEXT,
                        date_published DATE,
                        embedding vector(768),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                print("✅ Documents table created")
                
                # Create indexes for better performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_documents_instrument 
                    ON documents(instrument);
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_documents_source_type 
                    ON documents(source_type);
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_documents_date 
                    ON documents(date_published);
                """)
                print("✅ Basic indexes created")
                
                # Try to create vector index (may fail if data doesn't exist yet)
                try:
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_documents_embedding 
                        ON documents USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100);
                    """)
                    print("✅ Vector index created")
                except Exception as idx_error:
                    print(f"⚠️  Vector index creation deferred: {str(idx_error)}")
                    print("   (Will create after inserting data)")
                
                self.connection.commit()
                print("✅ Database schema setup completed successfully")
                
            finally:
                cursor.close()
                
        except Exception as e:
            print(f"❌ Error setting up database: {str(e)}")
            try:
                self.connection.rollback()
            except:
                pass
            raise
    
    def insert_document(self, doc_id, title, content, instrument, source_type, 
                       file_path, date_published, embedding, metadata):
        """Insert a single document with its embedding"""
        try:
            cursor = self.connection.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO documents 
                    (id, title, content, instrument, source_type, file_path, 
                     date_published, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        updated_at = CURRENT_TIMESTAMP;
                """, (
                    doc_id, title, content, instrument, source_type, 
                    file_path, date_published, embedding, json.dumps(metadata)
                ))
                
                self.connection.commit()
                return True
                
            finally:
                cursor.close()
            
        except Exception as e:
            print(f"❌ Error inserting document {doc_id}: {str(e)}")
            try:
                self.connection.rollback()
            except:
                pass
            return False
    
    def batch_insert_documents(self, documents, batch_size=50):
        """Insert multiple documents in batches with proper vector formatting"""
        total_inserted = 0
        failed_inserts = 0
        
        for i in tqdm(range(0, len(documents), batch_size), desc="Inserting documents"):
            batch = documents[i:i + batch_size]
            
            try:
                cursor = self.connection.cursor()
                
                try:
                    for doc in batch:
                        # Convert embedding list to PostgreSQL vector format
                        embedding_str = '[' + ','.join(map(str, doc['embedding'])) + ']'
                        
                        cursor.execute("""
                            INSERT INTO documents 
                            (id, title, content, instrument, source_type, file_path, 
                             date_published, embedding, metadata)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                title = EXCLUDED.title,
                                content = EXCLUDED.content,
                                embedding = EXCLUDED.embedding,
                                updated_at = CURRENT_TIMESTAMP;
                        """, (
                            doc['id'], doc['title'], doc['content'], 
                            doc['instrument'], doc['source_type'], doc['file_path'],
                            doc['date_published'], embedding_str,  # Use string format for vector
                            json.dumps(doc['metadata'])
                        ))
                    
                    self.connection.commit()
                    total_inserted += len(batch)
                    
                finally:
                    cursor.close()
                
            except Exception as e:
                print(f"❌ Error inserting batch: {str(e)}")
                try:
                    self.connection.rollback()
                except:
                    pass
                failed_inserts += len(batch)
        
        # Try to create vector index after data is inserted
        if total_inserted > 0:
            self._create_vector_index()
        
        print(f"✅ Inserted {total_inserted} documents, {failed_inserts} failed")
        return total_inserted
    
    def _create_vector_index(self):
        """Create vector index after data is inserted"""
        try:
            cursor = self.connection.cursor()
            
            try:
                print("🔍 Creating vector index for better search performance...")
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_documents_embedding 
                    ON documents USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                """)
                self.connection.commit()
                print("✅ Vector index created successfully")
                
            finally:
                cursor.close()
                
        except Exception as e:
            print(f"⚠️  Could not create vector index: {str(e)}")
            print("   Search will still work, but may be slower")
    
    def semantic_search(self, query_embedding, limit=10, instrument_filter=None, 
                       source_filter=None, similarity_threshold=0.7):
        """Perform semantic search using cosine similarity with proper vector formatting"""
        try:
            cursor = self.connection.cursor()
            
            try:
                # Convert query embedding to PostgreSQL vector format
                query_embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
                
                # Build query with optional filters
                where_conditions = []
                params = []
                
                if instrument_filter:
                    where_conditions.append("instrument = %s")
                    params.append(instrument_filter)
                
                if source_filter:
                    where_conditions.append("source_type = %s")
                    params.append(source_filter)
                
                if similarity_threshold:
                    where_conditions.append("1 - (embedding <=> %s) >= %s")
                    params.extend([query_embedding_str, similarity_threshold])
                
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                
                query = f"""
                    SELECT 
                        id,
                        title,
                        content,
                        instrument,
                        source_type,
                        file_path,
                        date_published,
                        metadata,
                        1 - (embedding <=> %s) AS similarity
                    FROM documents
                    {where_clause}
                    ORDER BY embedding <=> %s
                    LIMIT %s;
                """
                
                # Build final params list
                final_params = [query_embedding_str] + params + [query_embedding_str, limit]
                
                cursor.execute(query, final_params)
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in results]
                
            finally:
                cursor.close()
                
        except Exception as e:
            print(f"❌ Error performing semantic search: {str(e)}")
            return []
    
    def get_stats(self):
        """Get database statistics"""
        try:
            cursor = self.connection.cursor()
            
            try:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_documents,
                        COUNT(DISTINCT instrument) as unique_instruments,
                        COUNT(DISTINCT source_type) as unique_sources,
                        MIN(created_at) as earliest_document,
                        MAX(created_at) as latest_document
                    FROM documents;
                """)
                
                stats_row = cursor.fetchone()
                
                # Convert to dictionary
                stats_columns = [desc[0] for desc in cursor.description]
                stats = dict(zip(stats_columns, stats_row))
                
                cursor.execute("""
                    SELECT instrument, COUNT(*) as count
                    FROM documents
                    GROUP BY instrument
                    ORDER BY count DESC;
                """)
                
                instrument_rows = cursor.fetchall()
                instrument_counts = [{"instrument": row[0], "count": row[1]} for row in instrument_rows]
                
                return {
                    "stats": stats,
                    "instrument_distribution": instrument_counts
                }
                
            finally:
                cursor.close()
                
        except Exception as e:
            print(f"❌ Error getting stats: {str(e)}")
            return None
    
    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
        if self.connector:
            self.connector.close()

def preprocess_text(text):
    """Clean and normalize text content"""
    if "<" in text and ">" in text:
        h = html2text.HTML2Text()
        h.ignore_links = False
        text = h.handle(text)
    
    text = text.replace("\n\n", " ").replace("\t", " ").strip()
    text = " ".join(text.split())
    return text

def extract_text_from_item(item, instrument, source_type, file_path):
    """Extract text content from a JSON item"""
    title_fields = ["title", "headline", "name", "symbol"]
    content_fields = ["text", "content", "summary", "description", "analysis_text", "article"]
    
    # Find title
    title = None
    for field in title_fields:
        if field in item and item[field]:
            title = item[field]
            break
    
    # Find content
    content = None
    for field in content_fields:
        if field in item and item[field]:
            content = item[field]
            break
    
    # Look deeper for nested content
    if not content and isinstance(item, dict):
        for key, value in item.items():
            if isinstance(value, dict):
                for field in content_fields:
                    if field in value and value[field]:
                        content = value[field]
                        break
    
    if not content or len(content) < 50:
        return None
    
    content = preprocess_text(content)
    
    # Enhanced date extraction and parsing
    date = None
    date_fields = ["date", "publish_date", "published", "publishedAt", "timestamp", "created_at", "date_published"]
    
    for field in date_fields:
        if field in item and item[field]:
            date_str = item[field]
            break
    else:
        date_str = None
    
    # Parse date with multiple formats
    parsed_date = None
    if date_str and isinstance(date_str, str):
        try:
            from datetime import datetime
            
            # Try multiple date formats
            date_formats = [
                "%Y-%m-%d",  # 2025-05-21
                "%Y-%m-%dT%H:%M:%S",  # 2025-05-21T19:35:38
                "%Y-%m-%dT%H:%M:%SZ",  # 2025-05-21T19:35:38Z
                "%Y-%m-%dT%H:%M:%S.%f",  # 2025-05-21T19:35:38.123456
                "%Y-%m-%dT%H:%M:%S.%fZ",  # 2025-05-21T19:35:38.123456Z
                "%a, %d %b %Y %H:%M:%S %Z",  # Wed, 21 May 2025 19:35:38 GMT
                "%a, %d %b %Y %H:%M:%S",  # Wed, 21 May 2025 19:35:38
                "%d %b %Y",  # 21 May 2025
                "%B %d, %Y",  # May 21, 2025
                "%m/%d/%Y",  # 05/21/2025
                "%d/%m/%Y",  # 21/05/2025
            ]
            
            # Clean up the date string
            date_str = date_str.strip()
            
            # Handle timezone abbreviations that Python doesn't recognize
            if date_str.endswith(' GM'):
                date_str = date_str.replace(' GM', ' GMT')
            elif date_str.endswith(' UTC'):
                date_str = date_str.replace(' UTC', '+0000')
            
            # Try parsing with different formats
            for fmt in date_formats:
                try:
                    if fmt == "%a, %d %b %Y %H:%M:%S %Z":
                        # Special handling for timezone
                        if ' GMT' in date_str or ' UTC' in date_str:
                            parsed_date = datetime.strptime(date_str.replace(' GMT', '').replace(' UTC', ''), 
                                                           "%a, %d %b %Y %H:%M:%S")
                        else:
                            parsed_date = datetime.strptime(date_str, fmt)
                    else:
                        parsed_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            
            # If no format worked, try parsing just the date part
            if not parsed_date and 'T' in date_str:
                try:
                    date_part = date_str.split('T')[0]
                    parsed_date = datetime.strptime(date_part, "%Y-%m-%d")
                except ValueError:
                    pass
            
            # If still no luck, try extracting year-month-day with regex
            if not parsed_date:
                import re
                date_match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
                if date_match:
                    try:
                        year, month, day = date_match.groups()
                        parsed_date = datetime(int(year), int(month), int(day))
                    except ValueError:
                        pass
                        
        except Exception as e:
            print(f"⚠️  Could not parse date '{date_str}': {str(e)}")
    
    return {
        "id": str(uuid.uuid4()),
        "title": title if title else "Untitled Document",
        "content": content,
        "instrument": instrument,
        "source_type": source_type,
        "file_path": file_path,
        "date": parsed_date.strftime("%Y-%m-%d") if parsed_date else None,
        "metadata": {
            "instrument": instrument,
            "source_type": source_type,
            "has_title": bool(title),
            "content_length": len(content),
            "original_date_string": date_str if date_str else None
        }
    }

def process_json_files(directory):
    """Process JSON files and extract text content"""
    processed_documents = []
    json_files = glob.glob(f"{directory}/**/*.json", recursive=True)
    
    for file_path in tqdm(json_files, desc=f"Processing JSON files in {directory}"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            parts = file_path.split(os.path.sep)
            instrument = parts[-2] if len(parts) >= 2 else "unknown"
            source_type = parts[-3] if len(parts) >= 3 else "unknown"
            
            if isinstance(data, list):
                for item in data:
                    doc = extract_text_from_item(item, instrument, source_type, file_path)
                    if doc:
                        processed_documents.append(doc)
            else:
                doc = extract_text_from_item(data, instrument, source_type, file_path)
                if doc:
                    processed_documents.append(doc)
                    
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    return processed_documents

def process_html_files(directory):
    """Process HTML files"""
    processed_documents = []
    html_files = glob.glob(f"{directory}/**/*.html", recursive=True)
    
    for file_path in tqdm(html_files, desc=f"Processing HTML files in {directory}"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            parts = file_path.split(os.path.sep)
            instrument = parts[-2] if len(parts) >= 2 else "unknown"
            source_type = parts[-3] if len(parts) >= 3 else "unknown"
            
            # Convert HTML to text
            soup = BeautifulSoup(html_content, 'html.parser')
            content = soup.get_text(separator="\n")
            content = preprocess_text(content)
            
            if len(content) < 100:
                continue
            
            filename = os.path.basename(file_path)
            title = filename.replace('.html', '').replace('_', ' ')
            
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
                    "has_title": True,
                    "content_length": len(content)
                }
            }
            
            processed_documents.append(doc)
                    
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    return processed_documents

def chunk_document(doc, chunk_size=512):
    """Split document into chunks with proper UUID generation"""
    content = doc["content"]
    paragraphs = content.split("\n\n")
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunk_doc = doc.copy()
                # Generate new UUID for each chunk instead of appending to existing UUID
                chunk_doc["id"] = str(uuid.uuid4())
                chunk_doc["content"] = current_chunk.strip()
                chunk_doc["metadata"]["chunk_index"] = len(chunks)
                chunk_doc["metadata"]["parent_id"] = doc["id"]
                chunks.append(chunk_doc)
            
            current_chunk = para + "\n\n"
    
    if current_chunk:
        chunk_doc = doc.copy()
        # Generate new UUID for each chunk instead of appending to existing UUID  
        chunk_doc["id"] = str(uuid.uuid4())
        chunk_doc["content"] = current_chunk.strip()
        chunk_doc["metadata"]["chunk_index"] = len(chunks)
        chunk_doc["metadata"]["parent_id"] = doc["id"]
        chunks.append(chunk_doc)
    
    return chunks

def generate_embeddings(documents, batch_size=5):
    """Generate embeddings for documents"""
    print("🔮 Generating embeddings...")
    
    # Initialize embedding model
    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    
    documents_with_embeddings = []
    failed_count = 0
    
    for i in tqdm(range(0, len(documents), batch_size), desc="Generating embeddings"):
        batch = documents[i:i + batch_size]
        batch_texts = [doc["content"] for doc in batch]
        
        try:
            # Generate embeddings for batch
            embeddings_response = embedding_model.get_embeddings(batch_texts)
            
            # Process each embedding in the batch
            for doc, embedding_obj in zip(batch, embeddings_response):
                try:
                    embedding_values = embedding_obj.values
                    
                    # Convert to list for PostgreSQL
                    if hasattr(embedding_values, 'tolist'):
                        embedding_list = embedding_values.tolist()
                    else:
                        embedding_list = list(embedding_values)
                    
                    # Add embedding to document
                    doc_with_embedding = doc.copy()
                    doc_with_embedding['embedding'] = embedding_list
                    
                    # Fix date_published field - handle None values properly
                    if doc['date'] and doc['date'] != "Unknown":
                        doc_with_embedding['date_published'] = doc['date']
                    else:
                        doc_with_embedding['date_published'] = None
                    
                    documents_with_embeddings.append(doc_with_embedding)
                    
                except Exception as e:
                    print(f"❌ Error processing embedding: {str(e)}")
                    failed_count += 1
                    continue
            
            # Rate limiting
            time.sleep(0.2)
            
        except Exception as e:
            print(f"❌ Error generating embeddings for batch: {str(e)}")
            failed_count += len(batch)
            continue
    
    success_rate = len(documents_with_embeddings) / len(documents) * 100
    print(f"✅ Generated {len(documents_with_embeddings)}/{len(documents)} embeddings ({success_rate:.1f}% success rate)")
    
    return documents_with_embeddings

def create_query_function(db):
    """Create a query function for the CloudSQL vector database"""
    
    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    
    def query_documents(query_text, num_results=5, instrument_filter=None, 
                       source_filter=None, similarity_threshold=0.6):
        """Query documents using semantic search"""
        try:
            # Generate embedding for query
            query_embedding = embedding_model.get_embeddings([query_text])[0].values
            
            # Convert to list (not needed for string conversion, but keep for consistency)
            if hasattr(query_embedding, 'tolist'):
                embedding_list = query_embedding.tolist()
            else:
                embedding_list = list(query_embedding)
            
            # Perform search (embedding_list will be converted to string format in semantic_search)
            results = db.semantic_search(
                query_embedding=embedding_list,
                limit=num_results,
                instrument_filter=instrument_filter,
                source_filter=source_filter,
                similarity_threshold=similarity_threshold
            )
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results):
                formatted_result = {
                    "rank": i + 1,
                    "id": result["id"],
                    "similarity": float(result["similarity"]) if result["similarity"] else 0.0,
                    "title": result["title"] or "Untitled",
                    "content_preview": result["content"][:300] + "..." if result["content"] and len(result["content"]) > 300 else result["content"] or "",
                    "instrument": result["instrument"] or "Unknown",
                    "source_type": result["source_type"] or "Unknown",
                    "date": str(result["date_published"]) if result["date_published"] else "Unknown",
                    "file_path": result["file_path"] or "Unknown"
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error querying documents: {str(e)}")
            return []
    
    return query_documents

def main():
    """Main function for Cloud SQL vector processing"""
    print("🚀 TradeSage Cloud SQL + pgvector Corpus Processor")
    print("=" * 60)
    print(f"Project: {PROJECT_ID}")
    print(f"Instance: {INSTANCE_NAME}")
    print(f"Database: {DATABASE_NAME}")
    print("=" * 60)
    
    # Step 1: Connect to Cloud SQL
    print("\n🔌 Step 1: Connecting to Cloud SQL...")
    db = CloudSQLVectorDB(PROJECT_ID, REGION, INSTANCE_NAME, DATABASE_NAME, DB_USER, DB_PASSWORD)
    
    if not db.connect():
        print("❌ Failed to connect to Cloud SQL. Please check your configuration.")
        return
    
    # Step 2: Setup database schema
    print("\n🏗️  Step 2: Setting up database schema...")
    db.setup_database()
    
    # Step 3: Process documents
    print("\n📚 Step 3: Processing documents...")
    all_documents = []
    
    directories = ["news", "analyst_reports", "technical_analysis"]
    for directory in directories:
        if os.path.exists(directory):
            docs = process_json_files(directory)
            all_documents.extend(docs)
            print(f"  - {directory}: {len(docs)} documents")
    
    if os.path.exists("earnings"):
        html_docs = process_html_files("earnings")
        all_documents.extend(html_docs)
        print(f"  - earnings: {len(html_docs)} documents")
    
    if not all_documents:
        print("❌ No documents found!")
        db.close()
        return
    
    print(f"📄 Total documents: {len(all_documents)}")
    
    # Step 4: Chunk documents
    print("\n✂️  Step 4: Chunking documents...")
    chunked_documents = []
    for doc in tqdm(all_documents, desc="Chunking"):
        chunks = chunk_document(doc)
        chunked_documents.extend(chunks)
    
    print(f"📝 Total chunks: {len(chunked_documents)}")
    
    # Step 5: Generate embeddings
    print("\n🔮 Step 5: Generating embeddings...")
    documents_with_embeddings = generate_embeddings(chunked_documents)
    
    if not documents_with_embeddings:
        print("❌ No embeddings generated!")
        db.close()
        return
    
    # Step 6: Insert into database
    print("\n💾 Step 6: Inserting documents into Cloud SQL...")
    inserted_count = db.batch_insert_documents(documents_with_embeddings)
    
    # Step 7: Get database stats
    print("\n📊 Step 7: Database statistics...")
    stats = db.get_stats()
    if stats:
        print(f"   Total documents: {stats['stats']['total_documents']}")
        print(f"   Unique instruments: {stats['stats']['unique_instruments']}")
        print(f"   Unique sources: {stats['stats']['unique_sources']}")
        
        print("\n   Top instruments by document count:")
        for item in stats['instrument_distribution'][:5]:
            print(f"     - {item['instrument']}: {item['count']} documents")
    
    # Step 8: Create query function and test
    print("\n🔍 Step 8: Testing search functionality...")
    query_func = create_query_function(db)
    
    # Test queries
    test_queries = [
        "Bitcoin price analysis",
        "Apple quarterly earnings",
        "market volatility trends"
    ]
    
    for query in test_queries:
        print(f"\n📊 Testing query: '{query}'")
        results = query_func(query, num_results=3)
        
        if results:
            for result in results:
                print(f"  {result['rank']}. {result['title'][:60]}...")
                print(f"     Similarity: {result['similarity']:.3f}, "
                      f"Instrument: {result['instrument']}, "
                      f"Source: {result['source_type']}")
        else:
            print("  No results found")
    
    # Save metadata
    metadata = {
        "project_id": PROJECT_ID,
        "region": REGION,
        "instance_name": INSTANCE_NAME,
        "database_name": DATABASE_NAME,
        "total_documents": inserted_count,
        "original_documents": len(all_documents),
        "chunked_documents": len(chunked_documents),
        "instruments": list(set(doc["instrument"] for doc in all_documents)),
        "source_types": list(set(doc["source_type"] for doc in all_documents)),
        "created_at": datetime.now().isoformat(),
        "database_type": "cloud_sql_postgresql_pgvector"
    }
    
    with open(f"{OUTPUT_DIR}/cloudsql_metadata_{datetime.now().strftime('%Y%m%d%H%M%S')}.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ Cloud SQL vector database setup complete!")
    print(f"📊 Summary:")
    print(f"   - Database: {DATABASE_NAME} on {INSTANCE_NAME}")
    print(f"   - Documents inserted: {inserted_count}")
    print(f"   - Search function ready for use")
    
    # Keep connection open for interactive use
    print(f"\n🔍 Ready for interactive search!")
    return query_func, db

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        PROJECT_ID = sys.argv[1]
        if len(sys.argv) > 2:
            INSTANCE_NAME = sys.argv[2]
        print(f"Using project ID: {PROJECT_ID}")
        print(f"Using instance name: {INSTANCE_NAME}")
    
    query_function, database = main()
