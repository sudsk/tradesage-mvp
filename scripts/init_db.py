# scripts/init_db.py - Complete database initialization script
"""
Complete script to initialize the database with sample data for testing
"""
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def init_sample_data():
    """Initialize database with sample trading hypotheses and data."""
    
    print("🚀 Initializing TradeSage database with sample data...")
    
    # Import after adding to path
    from app.database.database import SessionLocal, create_tables
    from app.database.crud import (
        HypothesisCRUD, ContradictionCRUD, ConfirmationCRUD,
        ResearchDataCRUD, AlertCRUD, PriceHistoryCRUD
    )
    
    # Ensure tables are created
    create_tables()
    print("✅ Database tables created")
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_hyp = HypothesisCRUD.get_hypotheses(db, limit=1)
        if existing_hyp:
            print("⚠️ Database already contains data. Skipping initialization.")
            print("   Use 'python scripts/manage_db.py reset' to clear existing data.")
            return
        
        # Sample Hypothesis 1: Oil Price Prediction
        hypothesis1_data = {
            "title": "Oil prices to go above $85/barrel by March",
            "description": "Analysis predicting Brent crude oil will exceed $85 per barrel by March 2025",
            "thesis": "Based on supply chain tensions and increased demand, oil prices are expected to rise",
            "confidence_score": 0.65,
            "status": "on_schedule",
            "target_price": 85.0,
            "current_price": 83.9,
            "instruments": ["BRENT", "WTI"],
            "timeframe": "Q1 2025",
            "success_criteria": "Brent crude price above $85/barrel",
            "risk_factors": "Geopolitical tensions, supply disruptions",
            "created_at": datetime.utcnow() - timedelta(days=5)
        }
        hyp1 = HypothesisCRUD.create_hypothesis(db, hypothesis1_data)
        
        # Add contradictions for hypothesis 1
        contradiction1 = {
            "hypothesis_id": hyp1.id,
            "quote": "Oil headed for the first weekly decline this year after Donald Trump raised the prospect of trade wars and said he will ask Saudi Arabia and OPEC to lower prices as his first week as the new US president.",
            "reason": "This quote presents a contradictory perspective, indicating potential downward pressure on oil prices due to geopolitical factors and interventions.",
            "source": "Oil Set for First Weekly Drop This Year as Trump Rattles Market | Bloomberg | 23/01/2025",
            "strength": "Strong",
            "sentiment_score": -0.7
        }
        ContradictionCRUD.create_contradiction(db, contradiction1)
        
        contradiction2 = {
            "hypothesis_id": hyp1.id,
            "quote": "Market volatility expected as new policies unfold",
            "reason": "Uncertainty in energy markets could lead to price fluctuations rather than steady upward trend",
            "source": "Energy Analysis Today | 22/01/2025",
            "strength": "Medium",
            "sentiment_score": -0.4
        }
        ContradictionCRUD.create_contradiction(db, contradiction2)
        
        # Add more contradictions to reach 14 total
        for i in range(3, 15):
            contradiction = {
                "hypothesis_id": hyp1.id,
                "quote": f"Additional market analysis suggests potential downward pressure point {i}",
                "reason": f"Contradiction analysis point {i} challenging the upward price movement",
                "source": f"Market Research {i} | Energy Weekly | 22/01/2025",
                "strength": "Medium" if i % 2 == 0 else "Weak",
                "sentiment_score": -0.3 - (i * 0.02)
            }
            ContradictionCRUD.create_contradiction(db, contradiction)
        
        # Add confirmations for hypothesis 1
        confirmation1 = {
            "hypothesis_id": hyp1.id,
            "quote": "Oil edged higher as US sanctions on Russian crude tighten the market.",
            "reason": "The tightening of the market due to US sanctions on Russian crude could lead to higher Brent prices.",
            "source": "Oil Edges Higher as Sanctions on Russian Crude Tighten Market | Transcripts | 23/01/2025",
            "strength": "Strong",
            "sentiment_score": 0.8
        }
        ConfirmationCRUD.create_confirmation(db, confirmation1)
        
        confirmation2 = {
            "hypothesis_id": hyp1.id,
            "quote": "Supply chain disruptions continue to affect global oil markets",
            "reason": "Ongoing supply issues support upward price pressure in oil markets",
            "source": "Global Energy Report | 21/01/2025",
            "strength": "Medium",
            "sentiment_score": 0.6
        }
        ConfirmationCRUD.create_confirmation(db, confirmation2)
        
        # Add more confirmations to reach 10 total
        for i in range(3, 11):
            confirmation = {
                "hypothesis_id": hyp1.id,
                "quote": f"Supporting evidence point {i} for oil price increase",
                "reason": f"Confirmation analysis {i} supporting the bullish oil outlook",
                "source": f"Oil Analysis {i} | Energy Markets | 21/01/2025",
                "strength": "Strong" if i <= 5 else "Medium",
                "sentiment_score": 0.5 + (i * 0.02)
            }
            ConfirmationCRUD.create_confirmation(db, confirmation)
        
        # Add research data
        research_data1 = {
            "hypothesis_id": hyp1.id,
            "summary": "Market analysis shows mixed signals for oil prices with supply-side pressures supporting higher prices while geopolitical factors create downward pressure.",
            "market_data": {
                "current_price": 83.9,
                "week_high": 84.5,
                "week_low": 82.0,
                "volume": 1000000,
                "indicators": {
                    "rsi": 65.2,
                    "macd": 0.8,
                    "moving_avg_50": 82.5
                }
            },
            "news_data": {
                "sentiment_score": 0.1,
                "article_count": 25,
                "positive_articles": 12,
                "negative_articles": 13,
                "key_topics": ["supply", "geopolitics", "demand"]
            },
            "analysis_type": "research"
        }
        ResearchDataCRUD.create_research_data(db, research_data1)
        
        # Add price history for hypothesis 1
        base_price = 82.0
        for i in range(7):
            price_entry = {
                "hypothesis_id": hyp1.id,
                "symbol": "BRENT",
                "price": base_price + (i * 0.3) + (i % 2 * 0.2),
                "volume": 1000000 + (i * 50000),
                "timestamp": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6-i)
            }
            PriceHistoryCRUD.create_price_entry(db, price_entry)
        
        # Add alerts for hypothesis 1
        alerts_data = [
            {
                "hypothesis_id": hyp1.id,
                "alert_type": "recommendation",
                "message": "Oil prices showing strong resistance at $84. Consider entry points if price breaks above resistance.",
                "priority": "high",
                "is_read": False
            },
            {
                "hypothesis_id": hyp1.id,
                "alert_type": "warning",
                "message": "Monitor geopolitical developments that could impact oil supply chains.",
                "priority": "medium",
                "is_read": False
            }
        ]
        
        for alert_data in alerts_data:
            AlertCRUD.create_alert(db, alert_data)
        
        print(f"✅ Created hypothesis 1: {hyp1.title} (ID: {hyp1.id})")
        
        # Sample Hypothesis 2: US Inflation
        hypothesis2_data = {
            "title": "US inflation rate increase next year",
            "description": "Prediction of inflation rate movements in the coming year",
            "thesis": "Economic indicators suggest potential inflation increases due to fiscal policies",
            "confidence_score": 0.45,
            "status": "on_demand",
            "target_price": 2.5,
            "current_price": 2.3,
            "instruments": ["CPI", "PCE"],
            "timeframe": "2025",
            "success_criteria": "Inflation rate above 2.5%",
            "risk_factors": "Fed policy changes, economic slowdown",
            "created_at": datetime.utcnow() - timedelta(days=3)
        }
        hyp2 = HypothesisCRUD.create_hypothesis(db, hypothesis2_data)
        
        # Add contradictions and confirmations for hypothesis 2
        # 10 contradictions
        for i in range(10):
            contradiction = {
                "hypothesis_id": hyp2.id,
                "quote": f"Economic analysis suggests inflation pressures may be cooling {i+1}",
                "reason": f"Analysis point {i+1} suggesting contradictory evidence",
                "source": f"Economic Review {i+1} | Federal Reserve Analysis | 22/01/2025",
                "strength": "Strong" if i < 3 else ("Medium" if i < 7 else "Weak"),
                "sentiment_score": -0.5 - (i * 0.05)
            }
            ContradictionCRUD.create_contradiction(db, contradiction)
        
        # 4 confirmations
        for i in range(4):
            confirmation = {
                "hypothesis_id": hyp2.id,
                "quote": f"Inflationary pressure indicator {i+1} showing continued strength",
                "reason": f"Confirmation analysis {i+1} supporting inflation increase thesis",
                "source": f"Inflation Watch {i+1} | Economic Research | 21/01/2025",
                "strength": "Strong" if i < 2 else "Medium",
                "sentiment_score": 0.4 + (i * 0.1)
            }
            ConfirmationCRUD.create_confirmation(db, confirmation)
        
        # Add price history for inflation (CPI data)
        base_rate = 2.1
        for i in range(7):
            price_entry = {
                "hypothesis_id": hyp2.id,
                "symbol": "CPI",
                "price": base_rate + (i * 0.03),
                "timestamp": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6-i)
            }
            PriceHistoryCRUD.create_price_entry(db, price_entry)
        
        # Add research data for hypothesis 2
        research_data2 = {
            "hypothesis_id": hyp2.id,
            "summary": "Economic indicators present mixed signals on inflation outlook with some suggesting continued pressure while others indicate cooling trends.",
            "market_data": {
                "current_rate": 2.3,
                "core_cpi": 2.1,
                "pce": 2.0,
                "unemployment": 3.9,
                "fed_funds_rate": 5.25
            },
            "news_data": {
                "sentiment_score": -0.2,
                "article_count": 18,
                "positive_articles": 6,
                "negative_articles": 12,
                "key_topics": ["fed_policy", "employment", "wages"]
            },
            "analysis_type": "research"
        }
        ResearchDataCRUD.create_research_data(db, research_data2)
        
        print(f"✅ Created hypothesis 2: {hyp2.title} (ID: {hyp2.id})")
        
        # Sample Hypothesis 3: TTF (Natural Gas)
        hypothesis3_data = {
            "title": "Long TTF due to inelastic demand and high degree of weather risk",
            "description": "Analysis of TTF natural gas futures based on demand patterns and weather risks",
            "thesis": "Weather volatility and inelastic demand support long positions in TTF",
            "confidence_score": 0.72,
            "status": "on_demand",
            "target_price": 50.0,
            "current_price": 48.9,
            "instruments": ["TTF", "NBP"],
            "timeframe": "Q1 2025",
            "success_criteria": "TTF above €50/MWh",
            "risk_factors": "Mild weather, LNG imports",
            "created_at": datetime.utcnow() - timedelta(days=1)
        }
        hyp3 = HypothesisCRUD.create_hypothesis(db, hypothesis3_data)
        
        # Add 12 confirmations for this hypothesis
        for i in range(12):
            confirmation = {
                "hypothesis_id": hyp3.id,
                "quote": f"Weather forecasts support increased heating demand analysis {i+1}",
                "reason": f"Confirmation point {i+1} supporting the TTF bullish thesis",
                "source": f"Energy Weather Analytics {i+1} | Natural Gas Weekly | 23/01/2025",
                "strength": "Strong" if i < 6 else "Medium",
                "sentiment_score": 0.6 + (i * 0.02)
            }
            ConfirmationCRUD.create_confirmation(db, confirmation)
        
        # Add 8 contradictions
        for i in range(8):
            contradiction = {
                "hypothesis_id": hyp3.id,
                "quote": f"LNG imports may offset demand pressures analysis {i+1}",
                "reason": f"Contradiction point {i+1} challenging the TTF thesis",
                "source": f"LNG Market Report {i+1} | Gas Markets | 22/01/2025",
                "strength": "Medium" if i < 4 else "Weak",
                "sentiment_score": -0.3 - (i * 0.05)
            }
            ContradictionCRUD.create_contradiction(db, contradiction)
        
        # Add price history for TTF
        base_price = 45.2
        for i in range(7):
            price_entry = {
                "hypothesis_id": hyp3.id,
                "symbol": "TTF",
                "price": base_price + (i * 0.5) + (i * 0.1),
                "timestamp": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6-i)
            }
            PriceHistoryCRUD.create_price_entry(db, price_entry)
        
        # Add research data for hypothesis 3
        research_data3 = {
            "hypothesis_id": hyp3.id,
            "summary": "Natural gas market analysis shows strong fundamentals supporting higher prices with weather risk being a key driver.",
            "market_data": {
                "current_price": 48.9,
                "storage_levels": 85.3,
                "demand_forecast": "high",
                "lng_imports": 150.2,
                "temperature_outlook": "below_normal"
            },
            "news_data": {
                "sentiment_score": 0.4,
                "article_count": 15,
                "positive_articles": 10,
                "negative_articles": 5,
                "key_topics": ["weather", "storage", "lng"]
            },
            "analysis_type": "research"
        }
        ResearchDataCRUD.create_research_data(db, research_data3)
        
        print(f"✅ Created hypothesis 3: {hyp3.title} (ID: {hyp3.id})")
        
        # Add some general alerts
        general_alerts = [
            {
                "hypothesis_id": hyp2.id,
                "alert_type": "warning",
                "message": "Federal Reserve meeting scheduled next week - monitor for policy changes affecting inflation outlook.",
                "priority": "medium",
                "is_read": False
            },
            {
                "hypothesis_id": hyp3.id,
                "alert_type": "trigger",
                "message": "TTF prices approaching €49 - consider position adjustments if trend continues.",
                "priority": "high",
                "is_read": False
            },
            {
                "hypothesis_id": hyp1.id,
                "alert_type": "recommendation",
                "message": "Oil market showing increased volatility - monitor key support and resistance levels.",
                "priority": "medium",
                "is_read": False
            }
        ]
        
        for alert_data in general_alerts:
            AlertCRUD.create_alert(db, alert_data)
        
        print("\n" + "="*50)
        print("🎉 Sample data initialized successfully!")
        print(f"Created 3 hypotheses with associated data:")
        print(f"  1. {hyp1.title} (ID: {hyp1.id}) - 14✗ 10✓")
        print(f"  2. {hyp2.title} (ID: {hyp2.id}) - 10✗ 4✓")
        print(f"  3. {hyp3.title} (ID: {hyp3.id}) - 8✗ 12✓")
        print(f"Total alerts created: {len(general_alerts) + 2}")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Error initializing data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_sample_data()
