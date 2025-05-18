# app/tools/market_data_tool.py
from app.services.market_data_service import MultiApiMarketData

# Initialize the service once
_market_data_service = MultiApiMarketData()

def market_data_tool(instrument, source="auto", project_id="tradesage-mvp"):
    """Tool for retrieving market data using the multi-API service."""
    return _market_data_service.get_stock_data(instrument)

# Keep the get_secret function for backward compatibility
def get_secret(secret_name, project_id):
    """Retrieve secret from Secret Manager."""
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error retrieving secret {secret_name}: {e}")
        return None
