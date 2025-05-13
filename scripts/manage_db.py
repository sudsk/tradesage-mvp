# scripts/manage_db.py
"""
Database management script for TradeSage
"""
import sys
import os
from sqlalchemy.orm import Session
from app.database.database import SessionLocal, create_tables, engine
from app.database.models import Base
from app.database.crud import DashboardCRUD, HypothesisCRUD
import json

def reset_database():
    """Reset the database by dropping and recreating all tables."""
    print("🗃️ Resetting database...")
    Base.metadata.drop_all(bind=engine)
    create_tables()
    print("✅ Database reset complete!")

def view_hypotheses():
    """View all hypotheses in the database."""
    db = SessionLocal()
    try:
        print("📊 Current hypotheses in database:")
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
            print("No hypotheses found. Run 'python scripts/init_db.py' to add sample data.")
    finally:
        db.close()

def export_data(filename):
    """Export database data to JSON file."""
    db = SessionLocal()
    try:
        print(f"📤 Exporting data to {filename}...")
        
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
    finally:
        db.close()

def show_help():
    """Show available commands."""
    print("""
🔧 TradeSage Database Management

Available commands:
  reset          - Reset the database (drop and recreate tables)
  view           - View all hypotheses in the database
  export <file>  - Export data to JSON file
  help           - Show this help message

Examples:
  python scripts/manage_db.py reset
  python scripts/manage_db.py view
  python scripts/manage_db.py export data_backup.json
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
    
    elif command == "export":
        if len(sys.argv) < 3:
            print("❌ Please specify output filename")
            return
        export_data(sys.argv[2])
    
    elif command == "help":
        show_help()
    
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main()
