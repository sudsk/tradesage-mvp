from app.services.market_data_service import get_market_data

def market_data_tool(instrument, source="auto", project_id="tradesage-mvp"):
    """
    Tool for retrieving market data with fallbacks and mock data
    
    Args:
        instrument (str): The stock symbol or instrument to fetch data for
        source (str): Ignored, kept for backward compatibility
        project_id (str): Ignored, kept for backward compatibility
        
    Returns:
        dict: A standardized market data response
    """
    return get_market_data(instrument)
    
def get_secret(secret_name, project_id):
    """
    Retrieve secret from Secret Manager - kept for backward compatibility
    """
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error retrieving secret {secret_name}: {e}")
        return None
