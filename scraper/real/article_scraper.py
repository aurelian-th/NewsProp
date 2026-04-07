import json
import time
import uuid
import os
import re
import sys
from datetime import datetime
from DrissionPage import WebPage, ChromiumOptions

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scraper.common.schema import enforce_final_schema

def scrape_stiri_full_scroll():
    print("🚀 Pornire Scraper V12 - Scroll Infinit & Colectare Masivă")
    os.system("pkill -9 chrome || true")
    
    co = ChromiumOptions()
    co.set_argument('--no-sandbox')
    page = WebPage(chromium_options=co)

    categories = [
        "https://stiri.md/article/social",
        "https://stiri.md/story/justitie",
        "https://stiri.md/article/economic",
        "https://stiri.md/article/afaceri"
    ]
    
    final_dataset = []
    processed_urls = set() # Previne duplicatele globale

    for cat_url in categories:
        print(f"\n📂 Pregătim categoria: {cat_url}")
        page.get(cat_url)
        time.sleep(2)

        print("⏳ Se încarcă mai multe știri (Scroll)...")
        last_count = 0
        attempts = 0
        
        while attempts < 10: 
            
            current_articles = page.eles('css:div[class*="NewsList__Wrapper"] a[href*="/article/"], div[class*="NewsList__Wrapper"] a[href*="/story/"]')
            count = len(current_articles)
            print(f"   🔎 Găsite momentan: {count} articole")
            
            if count >= 60: 
                break
            
            if count == last_count:
                attempts += 1 
            else:
                attempts = 0 
            
            last_count = count
            page.scroll.down(2000) 
            time.sleep(1.5) 

        # --- FAZA DE COLECTARE LINK-URI & VIEWS ---
        wrapper = page.ele('css:div[class*="NewsList__Wrapper"]')
        articles = wrapper.eles('tag:a')
        
        temp_queue = []
        for a in articles:
            url = a.attr('href')
            if not url or ('/article/' not in url and '/story/' not in url):
                continue
            
            full_url = url if url.startswith('http') else "https://stiri.md" + url
            
            if full_url in processed_urls:
                continue

            # Extragem vizualizările din listă folosind clasa identificată de tine
            views_count = 0
            v_ele = a.ele('css:span[class*="FeedArticle__Counter"]', timeout=0.1)
            if v_ele:
                clean_v = re.sub(r'[^\d]', '', v_ele.text.strip())
                views_count = int(clean_v) if clean_v else 0

            temp_queue.append({"url": full_url, "views": views_count})
            processed_urls.add(full_url)

        print(f"🎯 Procesăm {len(temp_queue)} știri unice din această categorie...")

        # --- FAZA DE EXTRACȚIE CONȚINUT ---
        for item in temp_queue:
            try:
                page.get(item['url'])
                time.sleep(0.7) 

                h1 = page.ele('tag:h1')
                headline = h1.text if h1 else "Fără Titlu"
                
                paragraphs = [p.text.strip() for p in page.eles('tag:p') if len(p.text) > 65]
                body_text = "\n\n".join(paragraphs)

                if len(body_text) > 350:
                    t_ele = page.ele('tag:time')
                    pub_date = t_ele.attr('datetime') if t_ele else datetime.now().isoformat()

                    article_obj = {
                        "article_id": str(uuid.uuid4()),
                        "source": "stiri.md",
                        "is_fake": "fals" in headline.lower() or "stopfals" in item['url'].lower(),
                        "publication_date": pub_date,
                        "headline": headline,
                        "body_text": body_text,
                        "engagement_metrics": {
                            "views": item['views'],
                            "likes": 0,
                            "shares": 0,
                            "comments": 0
                        },
                        "top_comments": [],
                        "debunk_context": paragraphs[-1] if ("fals" in headline.lower()) else None
                    }
                    final_dataset.append(enforce_final_schema(article_obj, default_source="stiri.md"))
                    print(f"  ✅ [{item['views']} views] - {headline[:45]}...")
                
            except Exception as e:
                print(f"  ❌ Eroare la {item['url'][-15:]}")

    # Salvare
    if final_dataset:
        filename = "stirimd_dataset.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(final_dataset, f, indent=4, ensure_ascii=False)
        print(f"\n🏁 FINALIZAT! Total articole unice: {len(final_dataset)}")

    page.quit()

if __name__ == "__main__":
    scrape_stiri_full_scroll()
