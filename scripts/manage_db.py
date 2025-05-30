# scripts/manage_db.py - Updated for Cloud SQL support
"""
Database management script for TradeSage (SQLite + Cloud SQL support)
"""
import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def get_database_info():
    """Get information about current database configuration."""
    from app.database.database import engine, USE_CLOUD_SQL
    
    if USE_CLOUD_SQL:
        db_type = "Cloud SQL PostgreSQL"
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), version();"))
            db_name, version = result.fetchone()
            info = f"{db_type} - Database: {db_name}"
            version_short = version.split(' on ')[0] if ' on ' in version else version[:50]
            info += f"\n   Version: {version_short}"
    else:
        db_type = "SQLite"
        info = f"{db_type} - File: ./tradesage.db"
    
    return info

def reset_database():
    """Reset the database by dropping and recreating all tables."""
    print(f"🗃️ Resetting database...")
    print(f"   Type: {get_database_info()}")
    
    from app.database.database import engine, USE_CLOUD_SQL
    from app.database.models import Base
    
    if USE_CLOUD_SQL:
        # For Cloud SQL, be more careful about dropping tables
        print("⚠️  This will drop all tables in the Cloud SQL database!")
        confirm = input("Are you absolutely sure? Type 'DELETE ALL DATA' to confirm: ")
        if confirm != "DELETE ALL DATA":
            print("Operation cancelled.")
            return
    
    Base.metadata.drop_all(bind=engine)
    
    # Recreate tables
    from app.database.database import create_tables
    create_tables()
    
    print("✅ Database reset complete!")

def view_hypotheses():
    """View all hypotheses in the database."""
    from app.database.database import SessionLocal
    from app.database.crud import DashboardCRUD
    
    db = SessionLocal()
    try:
        print(f"📊 Current hypotheses in database:")
        print(f"   {get_database_info()}")
        print("-" * 50)
        
        summaries = DashboardCRUD.get_all_hypotheses_summary(db)
        for summary in summaries:
            if summary:
                hyp = summary["hypothesis"]
                print(f"ID: {hyp.id}")
                print(f"Title: {hyp.title}")
                print(f"Status: {hyp.status}")
                print(f"Confidence: {hyp.confidence_score * 100:.1f}%")
                print(f"Contradictions: {summary['contradictions_count']}")
                print(f"Confirmations: {summary['confirmations_count']}")
                print(f"Created: {hyp.created_at}")
                print("-" * 50)
        
        if not summaries:
            print("No hypotheses found.")
            print("Run 'python scripts/init_db.py' to add sample data.")
    finally:
        db.close()

def database_stats():
    """Show database statistics."""
    from app.database.database import SessionLocal, engine, USE_CLOUD_SQL
    from app.database.models import (
        TradingHypothesis, Contradiction, Confirmation, 
        ResearchData, Alert, PriceHistory
    )
    
    db = SessionLocal()
    try:
        print(f"📈 Database Statistics:")
        print(f"   {get_database_info()}")
        print("=" * 50)
        
        # Count records in each table
        stats = {
            "Hypotheses": db.query(TradingHypothesis).count(),
            "Contradictions": db.query(Contradiction).count(),
            "Confirmations": db.query(Confirmation).count(),
            "Research Data": db.query(ResearchData).count(),
            "Alerts": db.query(Alert).count(),
            "Price History": db.query(PriceHistory).count(),
        }
        
        total_records = sum(stats.values())
        
        for table, count in stats.items():
            print(f"{table:15}: {count:6,}")
        
        print("-" * 25)
        print(f"{'Total Records':15}: {total_records:6,}")
        
        # Additional Cloud SQL specific stats
        if USE_CLOUD_SQL:
            print("\n📊 Cloud SQL Specific Info:")
            with engine.connect() as conn:
                # Database size
                result = conn.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size;
                """))
                db_size = result.fetchone()[0]
                print(f"Database Size: {db_size}")
                
                # Check for vector extension
                result = conn.execute(text("""
                    SELECT EXISTS(
                        SELECT 1 FROM pg_extension WHERE extname = 'vector'
                    ) as has_vector;
                """))
                has_vector = result.fetchone()[0]
                print(f"Vector Extension: {'✅ Enabled' if has_vector else '❌ Disabled'}")
                
                # Table sizes
                result = conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY size_bytes DESC;
                """))
                
                print("\n📋 Table Sizes:")
                for schema, table, size, size_bytes in result.fetchall():
                    print(f"   {table:20}: {size}")
        
        print("=" * 50)
        
    finally:
        db.close()

def export_data(filename):
    """Export database data to JSON file."""
    from app.database.database import SessionLocal
    from app.database.crud import DashboardCRUD
    
    db = SessionLocal()
    try:
        print(f"📤 Exporting data to {filename}...")
        print(f"   From: {get_database_info()}")
        
        summaries = DashboardCRUD.get_all_hypotheses_summary(db)
        export_data = []
        
        for summary in summaries:
            if summary:
                hyp = summary["hypothesis"]
                export_data.append({
                    "hypothesis": {
                        "id": hyp.id,
                        "title": hyp.title,
                        "description": hyp.description,
                        "thesis": hyp.thesis,
                        "confidence_score": hyp.confidence_score,
                        "status": hyp.status,
                        "created_at": hyp.created_at.isoformat(),
                        "updated_at": hyp.updated_at.isoformat()
                    },
                    "contradictions": [
                        {
                            "quote": c.quote,
                            "reason": c.reason,
                            "source": c.source,
                            "strength": c.strength
                        } for c in summary["contradictions_detail"]
                    ],
                    "confirmations": [
                        {
                            "quote": c.quote,
                            "reason": c.reason,
                            "source": c.source,
                            "strength": c.strength
                        } for c in summary["confirmations_detail"]
                    ]
                })
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Data exported to {filename}")
        print(f"   Exported {len(export_data)} hypotheses")
    finally:
        db.close()

def test_connection():
    """Test database connection."""
    try:
        from app.database.database import engine, USE_CLOUD_SQL
        
        print(f"🔗 Testing database connection...")
        print(f"   {get_database_info()}")
        
        with engine.connect() as conn:
            if USE_CLOUD_SQL:
                result = conn.execute(text("SELECT current_database(), current_user, inet_server_addr(), inet_server_port();"))
                db_name, user, host, port = result.fetchone()
                print(f"✅ Connected to Cloud SQL")
                print(f"   Database: {db_name}")
                print(f"   User: {user}")
                print(f"   Host: {host}:{port}")
            else:
                result = conn.execute(text("SELECT 1;"))
                result.fetchone()
                print("✅ Connected to SQLite")
        
        print("✅ Database connection successful!")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

def show_help():
    """Show available commands."""
    print(f"""
🔧 TradeSage Database Management

Current Database: {get_database_info()}

Available commands:
  reset          - Reset the database (drop and recreate tables)
  view           - View all hypotheses in the database
  stats          - Show database statistics
  export <file>  - Export data to JSON file
  test           - Test database connection
  help           - Show this help message

Examples:
  python scripts/manage_db.py test
  python scripts/manage_db.py view
  python scripts/manage_db.py stats
  python scripts/manage_db.py export data_backup.json
  python scripts/manage_db.py reset

Database Configuration:
- Set USE_CLOUD_SQL=true in environment to use Cloud SQL
- Set USE_CLOUD_SQL=false or unset to use SQLite
- Configure Cloud SQL credentials in environment variables
""")

def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "reset":
        confirm = input("⚠️ This will delete all data. Are you sure? (y/N): ")
        if confirm.lower() == 'y':
            reset_database()
        else:
            print("Operation cancelled.")
    
    elif command == "view":
        view_hypotheses()
    
    elif command == "stats":
        database_stats()
    
    elif command == "export":
        if len(sys.argv) < 3:
            print("❌ Please specify output filename")
            return
        export_data(sys.argv[2])
    
    elif command == "test":
        test_connection()
    
    elif command == "help":
        show_help()
    
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main()
