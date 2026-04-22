import requests
import json
import time
import datetime
import calendar

API_ENDPOINT = "https://stopfals.md/archive/filter"
BASE_DOMAIN = "https://stopfals.md"
TARGET_ARTICLES = 1000

def get_previous_month(current_date):
    """Subtracts one month from the current date object."""
    if current_date.month == 1:
        return datetime.date(current_date.year - 1, 12, 1)
    else:
        return datetime.date(current_date.year, current_date.month - 1, 1)

def scrape_until_target():
    articles_metadata = []
    # Start at current month: April 2026
    current_date = datetime.date(2026, 4, 6) 
    
    print(f"Starting historical extraction. Target: {TARGET_ARTICLES} articles.")
    
    while len(articles_metadata) < TARGET_ARTICLES:
        year = current_date.year
        month = current_date.month
        # calendar.monthrange returns (weekday, number_of_days)
        last_day = calendar.monthrange(year, month)[1] 
        date_param = f"{year}-{month:02d}-{last_day}"
        
        print(f"\n--- Scanning Month: {year}-{month:02d} ---")
        page = 1
        
        # Inner loop to handle pagination for the specific month
        while True:
            params = {
                "page": page,
                "order": "desc",
                "date": date_param, 
                "lang": "ro"
            }
            
            headers = {
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json"
            }
            
            try:
                response = requests.get(API_ENDPOINT, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                items = data.get('results', []) 
                
                if not items:
                    print(f"  Reached end of {year}-{month:02d} at page {page-1}.")
                    break
                    
                for item in items:
                    # Construct matching schema from your successful output
                    views_str = str(item.get('views', '0'))
                    views_int = int(views_str) if views_str.isdigit() else 0
                    
                    article_info = {
                        "id": item.get('id'),
                        "url": BASE_DOMAIN + item.get('url', ''),
                        "headline": item.get('title'),
                        "publication_date": item.get('created_at'),
                        "views": views_int
                    }
                    articles_metadata.append(article_info)
                    
                    # Stop processing if we hit the exact target
                    if len(articles_metadata) == TARGET_ARTICLES:
                        print(f"\n🎯 Target of {TARGET_ARTICLES} articles reached!")
                        return articles_metadata
                    
                print(f"  Scraped page {page} - Added {len(items)} articles. (Total: {len(articles_metadata)}/{TARGET_ARTICLES})")
                page += 1
                time.sleep(1) # Rate limiting protection
                
            except Exception as e:
                print(f"  Error on page {page}: {e}")
                break # Break out of pagination loop on error, move to previous month
                
        # Move back one month for the next iteration of the outer loop
        current_date = get_previous_month(current_date)
        
    return articles_metadata

# Execute the scraper
final_dataset = scrape_until_target()

# Save the dataset
with open('stopfals_index.json', 'w', encoding='utf-8') as f:
    json.dump(final_dataset, f, indent=4, ensure_ascii=False)
    
print(f"\n✅ Phase 1 Complete! Saved exactly {len(final_dataset)} article URLs to stopfals_index.json.")