# scripts/init_cloudsql_tables.py
"""
Initialize Cloud SQL tables and extensions for TradeSage
"""
import sys
import os
from sqlalchemy import text

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def init_cloudsql_tables():
    """Initialize Cloud SQL with required extensions and tables."""
    
    print("🐘 Initializing Cloud SQL for TradeSage...")
    
    # Set environment to use Cloud SQL
    os.environ["USE_CLOUD_SQL"] = "true"
    
    # Import after setting environment
    from app.database.database import engine, create_tables
    from app.database.models import Base
    
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version[:50]}...")
        
        # Create pgvector extension if not exists
        print("🔌 Setting up pgvector extension...")
        with engine.connect() as conn:
            # Check if extension exists
            result = conn.execute(text("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                );
            """))
            
            if not result.fetchone()[0]:
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()
                    print("✅ pgvector extension created")
                except Exception as e:
                    print(f"⚠️ Could not create vector extension: {e}")
                    print("   This may require superuser privileges")
            else:
                print("✅ pgvector extension already exists")
        
        # Create application tables
        print("📋 Creating application tables...")
        create_tables()
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Created {len(tables)} tables:")
            for table in tables:
                print(f"   - {table}")
        
        # Create indexes for better performance
        print("🚀 Creating performance indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_hypotheses_status ON hypotheses(status);",
            "CREATE INDEX IF NOT EXISTS idx_hypotheses_confidence ON hypotheses(confidence_score);",
            "CREATE INDEX IF NOT EXISTS idx_contradictions_strength ON contradictions(strength);",
            "CREATE INDEX IF NOT EXISTS idx_confirmations_strength ON confirmations(strength);",
            "CREATE INDEX IF NOT EXISTS idx_alerts_priority ON alerts(priority);",
            "CREATE INDEX IF NOT EXISTS idx_alerts_unread ON alerts(is_read) WHERE is_read = false;",
            "CREATE INDEX IF NOT EXISTS idx_price_history_symbol_time ON price_history(symbol, timestamp);",
        ]
        
        with engine.connect() as conn:
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    conn.commit()
                except Exception as e:
                    print(f"⚠️ Index creation warning: {e}")
        
        print("✅ Performance indexes created")
        
        # Create a function to check if RAG tables exist (for integration)
        print("🔍 Checking for RAG tables...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'documents' AND table_schema = 'public'
                );
            """))
            
            if result.fetchone()[0]:
                print("✅ RAG documents table found - ready for integration")
                
                # Check vector column
                result = conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'documents' 
                    AND column_name = 'embedding';
                """))
                
                if result.fetchone():
                    print("✅ Vector embeddings column found")
                else:
                    print("⚠️ No embedding column found in documents table")
            else:
                print("⚠️ RAG documents table not found")
                print("   Run RAG setup scripts to create the documents table")
        
        print("\n" + "="*50)
        print("🎉 Cloud SQL initialization complete!")
        print("Tables created and ready for TradeSage application")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Error initializing Cloud SQL: {e}")
        raise

if __name__ == "__main__":
    init_cloudsql_tables()
