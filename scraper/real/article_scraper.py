import json
import time
import uuid
import os
import re
from datetime import datetime
from DrissionPage import WebPage, ChromiumOptions

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


    TARGET_PER_CATEGORY = 250
    for cat_url in categories:
        print(f"\n📂 Pregătim categoria: {cat_url}")
        page.get(cat_url)
        time.sleep(2)

        print("⏳ Se încarcă mai multe știri (Scroll)...")
        last_count = 0
        attempts = 0
        max_scrolls = 40
        while attempts < 10 and max_scrolls > 0:
            current_articles = page.eles('css:div[class*="NewsList__Wrapper"] a[href*="/article/"], div[class*="NewsList__Wrapper"] a[href*="/story/"]')
            count = len(current_articles)
            print(f"   🔎 Găsite momentan: {count} articole")
            if count >= TARGET_PER_CATEGORY:
                break
            if count == last_count:
                attempts += 1
            else:
                attempts = 0
            last_count = count
            page.scroll.down(2000)
            time.sleep(1.5)
            max_scrolls -= 1

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
            views_count = 0
            v_ele = a.ele('css:span[class*="FeedArticle__Counter"]', timeout=0.1)
            if v_ele:
                clean_v = re.sub(r'[^\d]', '', v_ele.text.strip())
                views_count = int(clean_v) if clean_v else 0
            temp_queue.append({"url": full_url, "views": views_count})
            processed_urls.add(full_url)

        # Limităm la 250 articole/categorie
        temp_queue = temp_queue[:TARGET_PER_CATEGORY]
        print(f"🎯 Procesăm {len(temp_queue)} știri unice din această categorie...")

        # --- FAZA DE EXTRACȚIE CONȚINUT ---
        for item in temp_queue:
            try:
                page.get(item['url'])
                time.sleep(0.5)
                h1 = page.ele('tag:h1')
                headline = h1.text if h1 else "Fără Titlu"
                paragraphs = [p.text.strip() for p in page.eles('tag:p') if len(p.text) > 65]
                body_text = "\n\n".join(paragraphs)

                # --- Extract images ---
                images = []
                # for img in page.eles('css:.ArticleContent__Thumbnail-sc-d85a0339-7.dltfKW img'):
                #     src = img.attr('src')
                #     if src:
                #         images.append(src)

                # --- Extract videos ---
                videos = []
                # for vid in page.eles('css:.fr-video.fr-fvl.fr-dvb.fr-draggable iframe'):
                #     src = vid.attr('src')
                #     if src:
                #         videos.append(src)

                # --- Extract external links from article body ---
                external_links = []
                body_ele = page.ele('css:.ArticleContent__Body-sc-d85a0339-13.fPSood')
                if body_ele:
                    for a in body_ele.eles('css:a[href]'):
                        href = a.attr('href')
                        if href and href.startswith('http'):
                            external_links.append(href)
                if len(body_text) > 350:
                    # Extrage data articolului din clasa specificată
                    date_ele = page.ele('css:.PostedDate__Date-sc-6dcf552f-0.kKfVwj', timeout=0.5)
                    pub_date_raw = None
                    if date_ele:
                        pub_date_raw = date_ele.text.strip()
                    else:
                        # fallback la <time> sau data curentă
                        t_ele = page.ele('tag:time')
                        pub_date_raw = t_ele.attr('datetime') if t_ele else datetime.now().isoformat()

                    # Încercăm să convertim pub_date_raw la formatul cerut
                    pub_date = None
                    try:
                        dt = None
                        import locale
                        locale.setlocale(locale.LC_TIME, 'ro_RO.UTF-8')
                        # Suportă: 6 Aprilie 2026, 15:16
                        try:
                            dt = datetime.strptime(pub_date_raw, '%d %B %Y, %H:%M')
                        except Exception:
                            try:
                                dt = datetime.strptime(pub_date_raw, '%d %B %Y')
                            except Exception:
                                try:
                                    dt = datetime.strptime(pub_date_raw, '%d.%m.%Y')
                                except Exception:
                                    try:
                                        dt = datetime.fromisoformat(pub_date_raw.replace('Z', '+00:00'))
                                    except Exception:
                                        dt = None
                        if dt:
                            # Dacă stringul original conține oră și minut, folosește-le
                            if re.search(r'\d{1,2}:\d{2}', pub_date_raw):
                                pub_date = dt.strftime('%Y-%m-%dT%H:%M:00.000Z')
                            else:
                                pub_date = dt.strftime('%Y-%m-%dT00:00:00.000Z')
                        else:
                            pub_date = pub_date_raw
                    except Exception:
                        pub_date = pub_date_raw

                    article_obj = {
                        "article_id": str(uuid.uuid4()),
                        "source": "StiriMD",
                        "source_domain": "stiri.md",
                        "is_fake": False,
                        "topic_category": "TBD",
                        "publication_date": pub_date,
                        "headline": headline,
                        "body_text": body_text,
                        "metrics": {
                            "views": item['views'],
                            "likes": 0,
                            "forwards_or_shares": 0,
                            "comments": 0
                        },
                        "top_comments": [],
                        "debunk_context": None,
                        "inferred_sources": [],
                        "media_and_links": {
                            "images": images,
                            "videos": videos,
                            "external_links": external_links
                        }
                    }
                    final_dataset.append(article_obj)
                    print(f"  ✅ [{item['views']} views] - {headline[:45]}... | raw date: {pub_date_raw} | formatted: {pub_date}")
            except Exception as e:
                print(f"  ❌ Eroare la {item['url'][-15:]}")

    # Salvare
    if final_dataset:
        filename = "stirimd_dataset_final.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(final_dataset, f, indent=4, ensure_ascii=False)
        print(f"\n🏁 FINALIZAT! Total articole unice: {len(final_dataset)} (salvate în {filename})")

    page.quit()

if __name__ == "__main__":
    scrape_stiri_full_scroll()
