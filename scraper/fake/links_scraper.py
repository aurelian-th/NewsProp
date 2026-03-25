import json
import time
from DrissionPage import SessionPage

def load_dataset(filename="stopfals_fake_news_dataset.json"):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return []

def guess_source(body_text, external_links):
    """Infers the original platform of the fake news."""
    content_pool = (body_text + " " + " ".join(external_links)).lower()
    
    sources = set()
    
    # Platform signatures
    if 't.me' in content_pool or 'telegram' in content_pool: sources.add('Telegram')
    if 'facebook.com' in content_pool or 'facebook' in content_pool: sources.add('Facebook')
    if 'tiktok.com' in content_pool or 'tiktok' in content_pool: sources.add('TikTok')
    if 'instagram.com' in content_pool or 'instagram' in content_pool: sources.add('Instagram')
    if 'youtube.com' in content_pool or 'youtu.be' in content_pool: sources.add('YouTube')
    if 'vk.com' in content_pool or 'vkontakte' in content_pool: sources.add('VKontakte')
    if 'ok.ru' in content_pool or 'odnoklassniki' in content_pool: sources.add('Odnoklassniki')
    
    # Notorious domains (based on your stopfals.md screenshots)
    if 'kp.md' in content_pool or 'komsomoliskaia pravda' in content_pool: sources.add('kp.md')
    if 'sputnik' in content_pool: sources.add('Sputnik')
    if 'publika.md' in content_pool or 'publika tv' in content_pool: sources.add('Publika')
    if 'noi.md' in content_pool: sources.add('Noi.md')
    
    return list(sources) if sources else ["Unknown"]

def enrich_article(page, article):
    url = article.get('url') # We need to ensure your Phase 2 saved the URL, or construct it from the ID
    if not url:
        url = f"https://stopfals.md/ro/article/{article.get('article_id')}"
        
    try:
        page.get(url)
        
        images = []
        videos = []
        external_links = []
        
        # 1. Extract Images
        for img in page.eles('tag:img'):
            src = img.attr('src')
            # Filter out UI icons and tiny logos
            if src and 'stopfals.md/dashboard/uploads' in src:
                images.append(src)
                
        # 2. Extract Embedded Videos (iFrames)
        for iframe in page.eles('tag:iframe'):
            src = iframe.attr('src')
            if src:
                videos.append(src)
                
        # 3. Extract External Links & Fix the "Relevant" noise issue
        # We will scan paragraphs to find links, but STOP if we hit the "Relevant" section
        for p in page.eles('tag:p'):
            if p.text and p.text.strip().lower() == "relevant":
                break # Hard stop! Don't process anything below this.
                
            for a in p.eles('tag:a'):
                href = a.attr('href')
                # Only keep external links (ignore internal stopfals.md routing)
                if href and href.startswith('http') and 'stopfals.md' not in href:
                    external_links.append(href)
                    
        # Clean up duplicates
        images = list(set(images))
        videos = list(set(videos))
        external_links = list(set(external_links))
        
        # 4. Infer the Source
        inferred_sources = guess_source(article.get('body_text', ''), external_links)
        
        # 5. Update the Article Dictionary
        article['source_domain'] = inferred_sources[0] if inferred_sources else "stopfals.md"
        article['inferred_sources'] = inferred_sources
        article['media_and_links'] = {
            "images": images,
            "videos": videos,
            "external_links": external_links
        }
        
        return article
        
    except Exception as e:
        print(f"  -> Error enriching {url}: {e}")
        return article

def run_phase_3():
    dataset = load_dataset()
    if not dataset:
        return
        
    print(f"Loaded {len(dataset)} articles. Starting Phase 3 Enrichment...")
    page = SessionPage()
    enriched_dataset = []
    
    for index, article in enumerate(dataset, start=1):
        print(f"[{index}/{len(dataset)}] Enriching ID: {article.get('article_id')}")
        enriched_article = enrich_article(page, article)
        enriched_dataset.append(enriched_article)
        time.sleep(1)
        
    # Save the final masterpiece
    output_filename = 'stopfals_final_dataset.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(enriched_dataset, f, indent=4, ensure_ascii=False)
        
    print(f"\n✅ Phase 3 Complete! Final dataset saved to {output_filename}.")

if __name__ == "__main__":
    run_phase_3()