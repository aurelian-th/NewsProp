import json
import time
from DrissionPage import SessionPage

def load_index(filename="stopfals_index.json"):
    """Loads the metadata generated in Phase 1."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {filename}. Make sure Phase 1 finished successfully.")
        return []

def scrape_article_text(page, url):
    """Fetches the article and extracts the paragraph text while filtering out noise."""
    try:
        page.get(url)
        
        # Extragem toate paragrafele brute
        raw_paragraphs = [p.text.strip() for p in page.eles('tag:p') if p.text.strip()]
        
        # Lista neagră cu textele din antet, meniul lateral și subsol
        noise_signatures = [
            "Am găsit {resultsCount} rezultate",
            "Am găsit",
            "Nu am găsit nimic",
            "Selectați limba Dvs.",
            "Falsuri recente",
            "Relevant",
            "Asociația Presei Independente",
            "Str. Armenească",
            "mun. Chișinău",
            "Republica Moldova",
            "MD-2012",
            "Tel: +373",
            "Fax: +373",
            "Email: stopfals",
            "Web: www.stopfals.md",
            "Navigare",
            "Abonează-te",
            "Toate drepturile de autor",
            "Designed & Developed",
            "Urmărește-ne",
            "Ai depistat un fals",
            "#NuDezinformării",
            "#StopFals",
            "#API",
            "Следи за нами",
            "Ты oбнаружил",
            "Сообщи об этом",
            "A contribuit:"
        ]
        
        clean_paragraphs = []
        for p in raw_paragraphs:
            # Dacă paragraful conține oricare dintre semnăturile de zgomot, îl sărim
            is_noise = any(noise.lower() in p.lower() for noise in noise_signatures)
            
            # Condiție extra pentru a sări caractere sau cuvinte singuratice din UI
            if len(p) < 3 or p.lower() == "rezultate":
                is_noise = True
                
            if not is_noise:
                clean_paragraphs.append(p)
                
        if not clean_paragraphs:
            return "", ""
            
        # Împărțim conținutul curățat
        midpoint = len(clean_paragraphs) // 2
        body_text = "\n\n".join(clean_paragraphs[:midpoint])
        debunk_context = "\n\n".join(clean_paragraphs[midpoint:])
        
        return body_text, debunk_context
        
    except Exception as e:
        print(f"  -> Error parsing DOM for {url}: {e}")
        return "", ""

def build_final_dataset():
    articles_metadata = load_index()
    if not articles_metadata:
        return
        
    total_articles = len(articles_metadata)
    print(f"Loaded {total_articles} articles from index. Starting text extraction...")
    
    final_dataset = []
    
    # Initialize the fast SessionPage
    page = SessionPage()
    
    for index, item in enumerate(articles_metadata, start=1):
        url = item.get('url')
        print(f"[{index}/{total_articles}] Scraping: {url}")
        
        body_text, debunk_context = scrape_article_text(page, url)
        
        # Construct the final schema exactly as defined in your Scraper.md
        article_data = {
            "article_id": str(item.get('id')), 
            "source_domain": "stopfals.md",
            "is_fake": True,
            "topic_category": "TBD", # Left for the NLP clustering phase
            "publication_date": item.get('publication_date'),
            "headline": item.get('headline'),
            "body_text": body_text,
            "metrics": {
                "views": item.get('views', 0),
                "likes": 0,
                "forwards_or_shares": 0,
                "comments": 0
            },
            "top_comments": [],
            "debunk_context": debunk_context
        }
        
        final_dataset.append(article_data)
        
        # A short sleep to prevent the server from blocking your IP
        time.sleep(1)
        
    # Save the finalized data
    output_filename = 'stopfals_fake_news_dataset.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, indent=4, ensure_ascii=False)
        
    print(f"\n✅ Phase 2 Complete! Saved {len(final_dataset)} fully formatted articles to {output_filename}.")

if __name__ == "__main__":
    build_final_dataset()