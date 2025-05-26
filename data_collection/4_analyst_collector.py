# analyst_collector_fixed.py
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
import random
import html2text
from urllib.parse import urljoin, urlparse

# Publicly available analyst and financial analysis sites
ANALYST_SOURCES = [
    {
        "name": "seeking_alpha",
        "base_url": "https://seekingalpha.com",
        "search_patterns": [
            "/symbol/{symbol}/analysis",
            "/symbol/{symbol}/news"
        ]
    },
    {
        "name": "motley_fool",
        "base_url": "https://www.fool.com",
        "search_url": "https://www.fool.com/search/?q={query}"
    },
    {
        "name": "zacks",
        "base_url": "https://www.zacks.com", 
        "search_patterns": [
            "/stock/research/{symbol}/all-news"
        ]
    },
    {
        "name": "yahoo_analysis",
        "base_url": "https://finance.yahoo.com",
        "search_patterns": [
            "/quote/{symbol}/analysis"
        ]
    }
]

# Enhanced instrument mapping
INSTRUMENTS = {
    "AAPL": {"symbol": "AAPL", "keywords": ["apple", "iphone", "ipad", "mac", "tim cook", "cupertino"]},
    "MSFT": {"symbol": "MSFT", "keywords": ["microsoft", "windows", "azure", "office", "satya nadella"]},
    "GOOGL": {"symbol": "GOOGL", "keywords": ["google", "alphabet", "search", "android", "youtube", "sundar pichai"]},
    "AMZN": {"symbol": "AMZN", "keywords": ["amazon", "aws", "prime", "jeff bezos", "andy jassy"]},
    "NVDA": {"symbol": "NVDA", "keywords": ["nvidia", "gpu", "ai chip", "jensen huang", "graphics"]},
    "TSLA": {"symbol": "TSLA", "keywords": ["tesla", "elon musk", "electric vehicle", "model", "ev"]},
    "Bitcoin": {"symbol": "BTC", "keywords": ["bitcoin", "btc", "cryptocurrency", "crypto", "digital currency"]},
    "Ethereum": {"symbol": "ETH", "keywords": ["ethereum", "eth", "smart contract", "defi", "vitalik"]},
    "Treasury Yields": {"symbol": "TNX", "keywords": ["treasury", "yield", "bond", "interest rate", "fed rate"]},
    "Gold": {"symbol": "GLD", "keywords": ["gold", "precious metal", "bullion", "gold price"]},
    "Brent Crude": {"symbol": "BNO", "keywords": ["oil", "crude", "brent", "petroleum", "opec", "energy"]}
}

def get_headers():
    """Get random headers to avoid detection"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
    ]
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }

def extract_text_from_html(html_content, max_length=2000):
    """Extract clean text from HTML content"""
    try:
        # Use html2text for better formatting
        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        h.ignore_emphasis = False
        h.body_width = 0  # Don't wrap lines
        
        text = h.handle(html_content)
        
        # Clean up the text
        text = text.replace('\n\n\n', '\n\n')  # Remove excessive newlines
        text = text.strip()
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length] + "..."
            
        return text
    except Exception as e:
        print(f"    Error extracting text: {str(e)}")
        # Fallback to BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text()[:max_length]

def scrape_seeking_alpha(instrument_data, max_articles=5):
    """Scrape Seeking Alpha for analysis articles"""
    articles = []
    symbol = instrument_data["symbol"]
    
    try:
        # Try the analysis page
        url = f"https://seekingalpha.com/symbol/{symbol}/analysis"
        print(f"    Scraping {url}")
        
        response = requests.get(url, headers=get_headers(), timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for article links (Seeking Alpha structure)
            article_links = soup.find_all('a', {'data-test-id': 'post-list-item-title'})
            
            if not article_links:
                # Alternative selector
                article_links = soup.find_all('a', href=True)
                article_links = [link for link in article_links if '/article/' in link.get('href', '')]
            
            for link in article_links[:max_articles]:
                try:
                    title = link.get_text().strip()
                    href = link.get('href')
                    
                    if not title or not href:
                        continue
                    
                    # Make URL absolute
                    if href.startswith('/'):
                        href = f"https://seekingalpha.com{href}"
                    
                    articles.append({
                        'title': title,
                        'url': href,
                        'source': 'seeking_alpha',
                        'text': f"Analysis article: {title}",  # Placeholder
                        'collected_at': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    print(f"      Error processing link: {str(e)}")
                    continue
                    
        else:
            print(f"    HTTP {response.status_code} for Seeking Alpha")
            
    except Exception as e:
        print(f"    Error scraping Seeking Alpha: {str(e)}")
    
    return articles

def scrape_yahoo_analysis(instrument_data, max_articles=3):
    """Scrape Yahoo Finance analysis section"""
    articles = []
    symbol = instrument_data["symbol"]
    
    try:
        url = f"https://finance.yahoo.com/quote/{symbol}/analysis"
        print(f"    Scraping {url}")
        
        response = requests.get(url, headers=get_headers(), timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract analyst recommendations and key statistics
            analyst_recommendations = soup.find('section', {'data-test': 'rec-rating-table'})
            earnings_estimate = soup.find('section', {'data-test': 'earnings-estimate-table'})
            
            if analyst_recommendations:
                rec_html = str(analyst_recommendations)
                rec_text = extract_text_from_html(rec_html, 1000)
                
                articles.append({
                    'title': f"{symbol} - Analyst Recommendations",
                    'url': url,
                    'source': 'yahoo_analysis',
                    'text': rec_text,
                    'collected_at': datetime.now().isoformat()
                })
            
            if earnings_estimate:
                earnings_html = str(earnings_estimate)
                earnings_text = extract_text_from_html(earnings_html, 1000)
                
                articles.append({
                    'title': f"{symbol} - Earnings Estimates",
                    'url': url,
                    'source': 'yahoo_analysis', 
                    'text': earnings_text,
                    'collected_at': datetime.now().isoformat()
                })
                
        else:
            print(f"    HTTP {response.status_code} for Yahoo Analysis")
            
    except Exception as e:
        print(f"    Error scraping Yahoo Analysis: {str(e)}")
    
    return articles

def scrape_generic_financial_sites(instrument_data, max_articles=5):
    """Scrape generic financial news sites for analysis"""
    articles = []
    keywords = instrument_data["keywords"]
    symbol = instrument_data["symbol"]
    
    # List of sites to try
    sites_to_scrape = [
        f"https://www.marketwatch.com/investing/stock/{symbol.lower()}",
        f"https://www.fool.com/quote/{symbol.lower()}", 
        f"https://finance.yahoo.com/quote/{symbol}/news"
    ]
    
    for site_url in sites_to_scrape:
        try:
            print(f"    Trying {site_url}")
            response = requests.get(site_url, headers=get_headers(), timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for article headlines that contain our keywords
                all_links = soup.find_all('a', href=True)
                
                relevant_links = []
                for link in all_links:
                    link_text = link.get_text().strip().lower()
                    if any(keyword in link_text for keyword in keywords):
                        relevant_links.append(link)
                
                # Process relevant links
                for link in relevant_links[:3]:  # Limit per site
                    try:
                        title = link.get_text().strip()
                        href = link.get('href')
                        
                        if len(title) < 10:  # Skip very short titles
                            continue
                        
                        # Make URL absolute
                        if href.startswith('/'):
                            base_url = f"{urlparse(site_url).scheme}://{urlparse(site_url).netloc}"
                            href = urljoin(base_url, href)
                        
                        articles.append({
                            'title': title,
                            'url': href,
                            'source': urlparse(site_url).netloc,
                            'text': f"Financial analysis: {title}",
                            'collected_at': datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        continue
                        
            time.sleep(random.uniform(1, 3))  # Be respectful
            
        except Exception as e:
            print(f"    Error with {site_url}: {str(e)}")
            continue
    
    return articles

def collect_analyst_reports_for_instrument(instrument_name, instrument_data):
    """Collect analyst reports for a specific instrument"""
    print(f"\nCollecting analyst reports for {instrument_name} ({instrument_data['symbol']})...")
    
    all_articles = []
    
    # Try Seeking Alpha
    print("  Trying Seeking Alpha...")
    seeking_alpha_articles = scrape_seeking_alpha(instrument_data, max_articles=5)
    all_articles.extend(seeking_alpha_articles)
    print(f"    Found {len(seeking_alpha_articles)} articles")
    
    time.sleep(random.uniform(2, 4))
    
    # Try Yahoo Analysis
    print("  Trying Yahoo Finance Analysis...")
    yahoo_articles = scrape_yahoo_analysis(instrument_data, max_articles=3)
    all_articles.extend(yahoo_articles)
    print(f"    Found {len(yahoo_articles)} articles")
    
    time.sleep(random.uniform(2, 4))
    
    # Try generic sites
    print("  Trying generic financial sites...")
    generic_articles = scrape_generic_financial_sites(instrument_data, max_articles=5)
    all_articles.extend(generic_articles)
    print(f"    Found {len(generic_articles)} articles")
    
    # Save articles if any found
    if all_articles:
        save_analyst_reports(all_articles, instrument_name, "combined_sources")
        print(f"  Total saved: {len(all_articles)} articles")
    else:
        print(f"  No articles found for {instrument_name}")
    
    return len(all_articles)

def save_analyst_reports(reports, instrument, source_name):
    """Save analyst reports to JSON file"""
    # Create directory if it doesn't exist
    output_dir = f"analyst_reports/{instrument}"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/{source_name}_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(reports, f, indent=2)
    
    print(f"    Saved to {filename}")

def main():
    """Main collection function"""
    print("Enhanced Analyst Report Collector for TradeSage")
    print("=" * 60)
    
    total_articles = 0
    
    for instrument_name, instrument_data in INSTRUMENTS.items():
        collected = collect_analyst_reports_for_instrument(instrument_name, instrument_data)
        total_articles += collected
        
        # Longer pause between instruments to be respectful
        time.sleep(random.uniform(5, 10))
    
    print(f"\nCollection complete!")
    print(f"Total analyst reports collected: {total_articles}")

if __name__ == "__main__":
    main()
