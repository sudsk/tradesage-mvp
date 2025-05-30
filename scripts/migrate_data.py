# scripts/migrate_data.py
"""
Migrate data from SQLite to Cloud SQL PostgreSQL
"""
import sys
import os
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def migrate_sqlite_to_cloudsql():
    """Migrate data from SQLite to Cloud SQL."""
    
    print("🔄 Migrating data from SQLite to Cloud SQL...")
    
    # Check if SQLite file exists
    sqlite_path = "./tradesage.db"
    if not os.path.exists(sqlite_path):
        print("❌ SQLite database file not found at ./tradesage.db")
        print("   Nothing to migrate")
        return
    
    # Create SQLite connection
    print("📱 Connecting to SQLite database...")
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
    SqliteSession = sessionmaker(bind=sqlite_engine)
    sqlite_db = SqliteSession()
    
    # Import models and database after setting up connections
    from app.database.models import (
        TradingHypothesis, Contradiction, Confirmation, 
        ResearchData, Alert, PriceHistory
    )
    
    # Set environment to use Cloud SQL
    os.environ["USE_CLOUD_SQL"] = "true"
    from app.database.database import SessionLocal
    
    print("🐘 Connecting to Cloud SQL database...")
    cloudsql_db = SessionLocal()
    
    try:
        # Check if Cloud SQL already has data
        existing_hyp = cloudsql_db.query(TradingHypothesis).first()
        if existing_hyp:
            confirm = input("⚠️ Cloud SQL already contains data. Continue? (y/N): ")
            if confirm.lower() != 'y':
                print("Migration cancelled")
                return
        
        # Migrate hypotheses
        print("📊 Migrating hypotheses...")
        sqlite_hypotheses = sqlite_db.query(TradingHypothesis).all()
        
        for sqlite_hyp in sqlite_hypotheses:
            # Create new hypothesis in Cloud SQL
            cloudsql_hyp = TradingHypothesis(
                title=sqlite_hyp.title,
                description=sqlite_hyp.description,
                thesis=sqlite_hyp.thesis,
                confidence_score=sqlite_hyp.confidence_score,
                status=sqlite_hyp.status,
                target_price=sqlite_hyp.target_price,
                current_price=sqlite_hyp.current_price,
                instruments=sqlite_hyp.instruments,
                timeframe=sqlite_hyp.timeframe,
                success_criteria=sqlite_hyp.success_criteria,
                risk_factors=sqlite_hyp.risk_factors,
                created_at=sqlite_hyp.created_at,
                updated_at=sqlite_hyp.updated_at,
                last_analysis_at=sqlite_hyp.last_analysis_at
            )
            
            cloudsql_db.add(cloudsql_hyp)
            cloudsql_db.flush()  # Get the ID
            
            print(f"   ✅ Migrated hypothesis: {cloudsql_hyp.title}")
            
            # Migrate contradictions
            sqlite_contradictions = sqlite_db.query(Contradiction).filter(
                Contradiction.hypothesis_id == sqlite_hyp.id
            ).all()
            
            for sqlite_con in sqlite_contradictions:
                cloudsql_con = Contradiction(
                    hypothesis_id=cloudsql_hyp.id,
                    quote=sqlite_con.quote,
                    reason=sqlite_con.reason,
                    source=sqlite_con.source,
                    strength=sqlite_con.strength,
                    url=sqlite_con.url,
                    sentiment_score=sqlite_con.sentiment_score,
                    created_at=sqlite_con.created_at
                )
                cloudsql_db.add(cloudsql_con)
            
            # Migrate confirmations
            sqlite_confirmations = sqlite_db.query(Confirmation).filter(
                Confirmation.hypothesis_id == sqlite_hyp.id
            ).all()
            
            for sqlite_conf in sqlite_confirmations:
                cloudsql_conf = Confirmation(
                    hypothesis_id=cloudsql_hyp.id,
                    quote=sqlite_conf.quote,
                    reason=sqlite_conf.reason,
                    source=sqlite_conf.source,
                    strength=sqlite_conf.strength,
                    url=sqlite_conf.url,
                    sentiment_score=sqlite_conf.sentiment_score,
                    created_at=sqlite_conf.created_at
                )
                cloudsql_db.add(cloudsql_conf)
            
            # Migrate research data
            sqlite_research = sqlite_db.query(ResearchData).filter(
                ResearchData.hypothesis_id == sqlite_hyp.id
            ).all()
            
            for sqlite_res in sqlite_research:
                cloudsql_res = ResearchData(
                    hypothesis_id=cloudsql_hyp.id,
                    summary=sqlite_res.summary,
                    market_data=sqlite_res.market_data,
                    news_data=sqlite_res.news_data,
                    analysis_type=sqlite_res.analysis_type,
                    created_at=sqlite_res.created_at
                )
                cloudsql_db.add(cloudsql_res)
            
            # Migrate alerts
            sqlite_alerts = sqlite_db.query(Alert).filter(
                Alert.hypothesis_id == sqlite_hyp.id
            ).all()
            
            for sqlite_alert in sqlite_alerts:
                cloudsql_alert = Alert(
                    hypothesis_id=cloudsql_hyp.id,
                    alert_type=sqlite_alert.alert_type,
                    message=sqlite_alert.message,
                    priority=sqlite_alert.priority,
                    is_read=sqlite_alert.is_read,
                    created_at=sqlite_alert.created_at
                )
                cloudsql_db.add(cloudsql_alert)
            
            # Migrate price history
            sqlite_prices = sqlite_db.query(PriceHistory).filter(
                PriceHistory.hypothesis_id == sqlite_hyp.id
            ).all()
            
            for sqlite_price in sqlite_prices:
                cloudsql_price = PriceHistory(
                    hypothesis_id=cloudsql_hyp.id,
                    symbol=sqlite_price.symbol,
                    price=sqlite_price.price,
                    volume=sqlite_price.volume,
                    timestamp=sqlite_price.timestamp
                )
                cloudsql_db.add(cloudsql_price)
            
            print(f"      - {len(sqlite_contradictions)} contradictions")
            print(f"      - {len(sqlite_confirmations)} confirmations")
            print(f"      - {len(sqlite_research)} research data")
            print(f"      - {len(sqlite_alerts)} alerts")
            print(f"      - {len(sqlite_prices)} price history")
        
        # Commit all changes
        cloudsql_db.commit()
        
        # Verify migration
        print("\n🔍 Verifying migration...")
        migrated_hyp = cloudsql_db.query(TradingHypothesis).count()
        migrated_con = cloudsql_db.query(Contradiction).count()
        migrated_conf = cloudsql_db.query(Confirmation).count()
        
        print(f"✅ Migrated {migrated_hyp} hypotheses")
        print(f"✅ Migrated {migrated_con} contradictions")
        print(f"✅ Migrated {migrated_conf} confirmations")
        
        # Create backup of SQLite file
        backup_name = f"tradesage_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        import shutil
        shutil.copy2(sqlite_path, backup_name)
        print(f"📦 SQLite backup created: {backup_name}")
        
        print("\n" + "="*50)
        print("🎉 Migration completed successfully!")
        print("Your data is now in Cloud SQL PostgreSQL")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        cloudsql_db.rollback()
        raise
    finally:
        sqlite_db.close()
        cloudsql_db.close()

def export_sqlite_to_json():
    """Export SQLite data to JSON as backup before migration."""
    print("📤 Exporting SQLite data to JSON backup...")
    
    sqlite_path = "./tradesage.db"
    if not os.path.exists(sqlite_path):
        print("❌ SQLite database not found")
        return
    
    # Connect to SQLite
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
    SqliteSession = sessionmaker(bind=sqlite_engine)
    sqlite_db = SqliteSession()
    
    try:
        from app.database.models import TradingHypothesis, Contradiction, Confirmation
        
        # Export all data
        export_data = []
        hypotheses = sqlite_db.query(TradingHypothesis).all()
        
        for hyp in hypotheses:
            hyp_data = {
                "hypothesis": {
                    "id": hyp.id,
                    "title": hyp.title,
                    "description": hyp.description,
                    "thesis": hyp.thesis,
                    "confidence_score": hyp.confidence_score,
                    "status": hyp.status,
                    "target_price": hyp.target_price,
                    "current_price": hyp.current_price,
                    "instruments": hyp.instruments,
                    "timeframe": hyp.timeframe,
                    "success_criteria": hyp.success_criteria,
                    "risk_factors": hyp.risk_factors,
                    "created_at": hyp.created_at.isoformat() if hyp.created_at else None,
                    "updated_at": hyp.updated_at.isoformat() if hyp.updated_at else None
                },
                "contradictions": [],
                "confirmations": []
            }
            
            # Get contradictions
            contradictions = sqlite_db.query(Contradiction).filter(
                Contradiction.hypothesis_id == hyp.id
            ).all()
            
            for con in contradictions:
                hyp_data["contradictions"].append({
                    "quote": con.quote,
                    "reason": con.reason,
                    "source": con.source,
                    "strength": con.strength,
                    "sentiment_score": con.sentiment_score,
                    "created_at": con.created_at.isoformat() if con.created_at else None
                })
            
            # Get confirmations
            confirmations = sqlite_db.query(Confirmation).filter(
                Confirmation.hypothesis_id == hyp.id
            ).all()
            
            for conf in confirmations:
                hyp_data["confirmations"].append({
                    "quote": conf.quote,
                    "reason": conf.reason,
                    "source": conf.source,
                    "strength": conf.strength,
                    "sentiment_score": conf.sentiment_score,
                    "created_at": conf.created_at.isoformat() if conf.created_at else None
                })
            
            export_data.append(hyp_data)
        
        # Save to JSON
        backup_filename = f"sqlite_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✅ SQLite data exported to {backup_filename}")
        print(f"   Exported {len(export_data)} hypotheses")
        
        return backup_filename
        
    except Exception as e:
        print(f"❌ Export error: {e}")
        raise
    finally:
        sqlite_db.close()

def main():
    """Main function to handle migration options."""
    if len(sys.argv) < 2:
        print("""
🔄 TradeSage Data Migration

Available commands:
  migrate    - Migrate data from SQLite to Cloud SQL
  export     - Export SQLite data to JSON backup
  help       - Show this help message

Examples:
  python scripts/migrate_data.py export
  python scripts/migrate_data.py migrate
        """)
        return
    
    command = sys.argv[1].lower()
    
    if command == "export":
        export_sqlite_to_json()
    
    elif command == "migrate":
        # First create a backup
        print("📦 Creating backup before migration...")
        export_sqlite_to_json()
        print()
        
        # Then migrate
        migrate_sqlite_to_cloudsql()
    
    elif command == "help":
        print("""
🔄 TradeSage Data Migration

This script helps migrate your data from SQLite to Cloud SQL PostgreSQL.

Commands:
  export     - Export SQLite data to JSON backup file
  migrate    - Full migration from SQLite to Cloud SQL (includes backup)

Prerequisites:
1. Cloud SQL instance must be set up and running
2. Environment variables must be configured for Cloud SQL
3. Tables must be initialized (run init_cloudsql_tables.py first)

Migration Process:
1. Creates JSON backup of existing SQLite data
2. Migrates all hypotheses, contradictions, confirmations, etc.
3. Verifies migration was successful
4. Creates SQLite backup file

Safety Features:
- Creates backups before migration
- Checks for existing data in Cloud SQL
- Transaction rollback on errors
- Verification of migrated data
        """)
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python scripts/migrate_data.py help' for usage")

if __name__ == "__main__":
    main()
