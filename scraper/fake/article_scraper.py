import json
import re
import time
from urllib.parse import urlparse
from DrissionPage import SessionPage

DEBUNK_MARKERS = [
    "nu corespunde adevărului",
    "nu corespunde realității",
    "este fals",
    "afirmația este falsă",
    "afirmațiile sunt false",
    "în realitate",
    "de fapt",
    "datele arată",
    "potrivit datelor",
    "ce spune",
    "concluzie",
]

CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")

SOURCE_HINT_MARKERS = {
    "Telegram": ["telegram", "t.me"],
    "Facebook": ["facebook", "facebook.com"],
    "TikTok": ["tiktok", "tiktok.com"],
    "Instagram": ["instagram", "instagram.com"],
    "YouTube": ["youtube", "youtu.be", "youtube.com"],
    "VKontakte": ["vk.com", "vkontakte"],
    "Odnoklassniki": ["ok.ru", "odnoklassniki"],
    "Sputnik": ["sputnik"],
    "kp.md": ["kp.md", "komsomoliskaia pravda"],
    "Publika": ["publika"],
    "Noi.md": ["noi.md"],
}

DOMAIN_TO_SOURCE = {
    "facebook.com": "Facebook",
    "m.facebook.com": "Facebook",
    "t.me": "Telegram",
    "telegram.me": "Telegram",
    "tiktok.com": "TikTok",
    "www.tiktok.com": "TikTok",
    "instagram.com": "Instagram",
    "www.instagram.com": "Instagram",
    "youtube.com": "YouTube",
    "www.youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "vk.com": "VKontakte",
    "ok.ru": "Odnoklassniki",
    "sputnik.md": "Sputnik",
    "sputniknews.com": "Sputnik",
    "kp.md": "kp.md",
    "noi.md": "Noi.md",
    "publika.md": "Publika",
}

SOURCE_DOMAIN_MAP = {
    "YouTube": "youtube.com",
    "Facebook": "facebook.com",
    "TikTok": "tiktok.com",
    "Instagram": "instagram.com",
    "Telegram": "t.me",
    "VKontakte": "vk.com",
    "Odnoklassniki": "ok.ru",
    "kp.md": "kp.md",
    "Sputnik": "sputniknews.com",
    "Publika": "publika.md",
    "Noi.md": "noi.md",
    "Unknown": "unknown",
}

NOISE_SUBSTRINGS = [
    "am găsit {resultscount} rezultate",
    "am găsit",
    "nu am găsit nimic",
    "selectați limba dvs.",
    "falsuri recente",
    "relevant",
    "asociația presei independente",
    "str. armenească",
    "mun. chișinău",
    "republica moldova",
    "md-2012",
    "tel: +373",
    "fax: +373",
    "email: stopfals",
    "web: www.stopfals.md",
    "navigare",
    "abonează-te",
    "toate drepturile de autor",
    "designed & developed",
    "urmărește-ne",
    "ai depistat un fals",
    "#nudezinformării",
    "#stopfals",
    "#api",
    "следи за нами",
    "ты oбнаружил",
    "сообщи об этом",
    "a contribuit:",
    "найдены {resultscount} результаты",
    "ничего не найдено",
    "выберите свой язык",
    "свежие фейки",
    "релевантно",
    "ассоциация независимой прессы",
    "эл. адрес: stopfals@stopfals.md",
    "веб: www.stopfals.md",
    "навигация",
    "оформи подписку",
    "все авторские права на дизайн онлайновой платформы",
]

NOISE_REGEXES = [
    re.compile(r"^найдены\s*\{?resultscount\}?\s*результаты$", re.IGNORECASE),
    re.compile(r"^ничего не найдено$", re.IGNORECASE),
    re.compile(r"^выберите\s+свой\s+язык$", re.IGNORECASE),
    re.compile(r"^свежие\s+фейки$", re.IGNORECASE),
    re.compile(r"^релевантно$", re.IGNORECASE),
    re.compile(r"^ассоциация\s+независимой\s+прессы$", re.IGNORECASE),
    re.compile(r"^тел\s*:\s*\+?\d+", re.IGNORECASE),
    re.compile(r"^факс\s*:\s*\+?\d+", re.IGNORECASE),
    re.compile(r"^эл\.?\s*адрес\s*:", re.IGNORECASE),
    re.compile(r"^веб\s*:", re.IGNORECASE),
]

DENY_EXTERNAL_HOSTS = {
    "ebs-integrator.com",
    "www.ebs-integrator.com",
}

DENY_EXTERNAL_URL_PARTS = [
    "facebook.com/stopfals",
    "t.me/stopfals",
    "tiktok.com/@stop.fals.moldova",
    "facebook.com/hashtag/stopfals",
    "facebook.com/hashtag/nudezinform",
    "facebook.com/hashtag/api",
    "facebook.com/share/p/",
    "facebook.com/share/v/",
    "__tn__=*nk-r",
]

STRICT_MIN_BODY_CHARS = 220

CRITICAL_NOISE_IN_TEXT = [
    "найдены {resultscount} результаты",
    "ничего не найдено",
    "выберите свой язык",
    "свежие фейки",
    "релевантно",
    "ассоциация независимой прессы",
    "эл. адрес: stopfals@stopfals.md",
    "веб: www.stopfals.md",
    "навигация",
    "оформи подписку",
    "all rights reserved",
    "am găsit {resultscount} rezultate",
    "nu am găsit nimic",
    "selectați limba dvs.",
    "falsuri recente",
    "asociația presei independente",
    "email: stopfals@stopfals.md",
    "web: www.stopfals.md",
    "abonează-te",
]

def load_index(filename="stopfals_index.json"):
    """Loads the metadata generated in Phase 1."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {filename}. Make sure Phase 1 finished successfully.")
        return []


def _dedupe_keep_order(items):
    seen = set()
    output = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def _compact_text(text):
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _is_noise_paragraph(paragraph):
    p = _compact_text(paragraph)
    if len(p) < 3:
        return True

    p_low = p.lower()
    if p_low == "rezultate":
        return True

    if any(signature in p_low for signature in NOISE_SUBSTRINGS):
        return True

    if any(pattern.match(p) for pattern in NOISE_REGEXES):
        return True

    return False


def _has_cyrillic(text):
    return bool(CYRILLIC_RE.search(text or ""))


def _candidate_urls(url, headline):
    candidates = [url]
    if not url:
        return candidates

    is_cyr = _has_cyrillic(headline)
    if "/ro/" in url:
        ru_url = url.replace("/ro/", "/ru/")
        if is_cyr:
            candidates = [ru_url, url]
        else:
            candidates.append(ru_url)
    elif "/ru/" in url:
        ro_url = url.replace("/ru/", "/ro/")
        if is_cyr:
            candidates.append(ro_url)
        else:
            candidates = [ro_url, url]

    # Also try language-neutral article URL shape.
    if "/ro/article/" in url:
        candidates.append(url.replace("/ro/article/", "/article/"))
    if "/ru/article/" in url:
        candidates.append(url.replace("/ru/article/", "/article/"))

    return _dedupe_keep_order(candidates)


def _clean_paragraphs(page):
    raw_paragraphs = [p.text.strip() for p in page.eles('tag:p') if p.text.strip()]
    clean_paragraphs = []
    for paragraph in raw_paragraphs:
        if _is_noise_paragraph(paragraph):
            continue
        compact = _compact_text(paragraph)
        if compact:
            clean_paragraphs.append(compact)

    return clean_paragraphs


def _contains_critical_noise(text):
    t = (text or "").lower()
    return any(marker in t for marker in CRITICAL_NOISE_IN_TEXT)


def guess_source(body_text, debunk_context, external_links):
    """Infers platforms/domains with weighted confidence, prioritizing real links over text mentions."""
    content_pool = (body_text + " " + (debunk_context or "")).lower()
    scores = {}

    def add_score(src, value):
        scores[src] = scores.get(src, 0) + value

    # Strong signals: domains from external links.
    for link in external_links:
        host = (urlparse(link).netloc or "").lower().removeprefix("www.")
        if not host:
            continue
        mapped = None
        if host in DOMAIN_TO_SOURCE:
            mapped = DOMAIN_TO_SOURCE[host]
        else:
            for d, src in DOMAIN_TO_SOURCE.items():
                if host.endswith(d):
                    mapped = src
                    break
        if mapped:
            add_score(mapped, 3)

    # Weak signals: mention patterns in text.
    for source_name, markers in SOURCE_HINT_MARKERS.items():
        if any(marker in content_pool for marker in markers):
            add_score(source_name, 1)

    if not scores:
        return ["Unknown"]

    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    inferred = [name for name, _ in ranked]
    return inferred


def _choose_source(inferred_sources, videos, external_links):
    if inferred_sources and inferred_sources[0] != "Unknown":
        return inferred_sources[0]

    # Fallback: infer from embedded videos when links are weak.
    for v in videos:
        host = (urlparse(v).netloc or "").lower().removeprefix("www.")
        if host in DOMAIN_TO_SOURCE:
            return DOMAIN_TO_SOURCE[host]

    for link in external_links:
        host = (urlparse(link).netloc or "").lower().removeprefix("www.")
        if host in DOMAIN_TO_SOURCE:
            return DOMAIN_TO_SOURCE[host]

    return "Unknown"


def extract_media_and_links(page):
    images = []
    videos = []
    external_links = []

    try:
        for img in page.eles('tag:img'):
            src = img.attr('src')
            if src and 'stopfals.md/dashboard/uploads' in src:
                images.append(src)

        for iframe in page.eles('tag:iframe'):
            src = iframe.attr('src')
            if src and src.startswith('http'):
                videos.append(src)

        for p in page.eles('tag:p'):
            if p.text and p.text.strip().lower() == "relevant":
                break

            for a in p.eles('tag:a'):
                href = a.attr('href')
                if not href or not href.startswith('http') or 'stopfals.md' in href:
                    continue

                href_low = href.lower()
                host = (urlparse(href).netloc or "").lower()

                if host in DENY_EXTERNAL_HOSTS:
                    continue

                if any(part in href_low for part in DENY_EXTERNAL_URL_PARTS):
                    continue

                external_links.append(href)
    except Exception as e:
        # Stopfals intermittently returns empty documents; skip media parsing for that candidate.
        print(f"  -> Warning: media/link extraction skipped due to parse error: {e}")

    return {
        "images": _dedupe_keep_order(images),
        "videos": _dedupe_keep_order(videos),
        "external_links": _dedupe_keep_order(external_links),
    }


def _find_debunk_start(paragraphs, headline):
    if len(paragraphs) < 3:
        return None

    headline_lower = (headline or "").lower()

    # High confidence: explicit correction markers in paragraph text.
    for idx, paragraph in enumerate(paragraphs):
        if idx == 0:
            continue
        p_lower = paragraph.lower()
        if any(marker in p_lower for marker in DEBUNK_MARKERS):
            return idx

    # Medium confidence: heading-style corrective sections.
    for idx, paragraph in enumerate(paragraphs):
        if idx == 0:
            continue
        p = paragraph.strip()
        is_heading_like = len(p) <= 110 and not p.endswith(".")
        if not is_heading_like:
            continue
        p_lower = p.lower()
        if (
            "fals" in p_lower
            or "dezinform" in p_lower
            or "în realitate" in p_lower
            or "ce spune" in p_lower
            or "concluzie" in p_lower
        ):
            return idx

    # Conservative fallback for classic Stopfals entries.
    # If title indicates fact-check but no marker is found, keep debunk unset.
    if "fals" in headline_lower:
        return None

    return None


def _remove_trailing_signature(text):
    chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
    if not chunks:
        return text

    # Drop short author/signature footer blocks.
    while chunks:
        tail = chunks[-1]
        tail_low = tail.lower()
        if tail_low in {"stopfals.md", "stopfals", "api"}:
            chunks.pop()
            continue
        if len(tail) <= 70 and (
            "stopfals" in tail_low
            or tail.endswith(",")
            or tail_low.startswith("victoria ")
            or tail_low.startswith("dana ")
            or tail_low.startswith("mihai ")
            or tail_low.startswith("elena ")
        ):
            chunks.pop()
            continue
        break

    return "\n\n".join(chunks)

def scrape_article_text(page):
    """Fetches article text and splits body/debunk using debunk markers."""
    try:
        clean_paragraphs = _clean_paragraphs(page)
        if not clean_paragraphs:
            return "", None

        headline_ele = page.ele("tag:h1", timeout=0.5)
        headline = headline_ele.text.strip() if headline_ele and headline_ele.text else ""

        split_index = _find_debunk_start(clean_paragraphs, headline)

        if split_index is None:
            body_text = "\n\n".join(clean_paragraphs)
            debunk_context = None
        else:
            body_text = "\n\n".join(clean_paragraphs[:split_index]).strip()
            debunk_context = "\n\n".join(clean_paragraphs[split_index:]).strip()
            if not debunk_context:
                debunk_context = None

        body_text = _remove_trailing_signature(_compact_text(body_text))
        if debunk_context is not None:
            debunk_context = _remove_trailing_signature(_compact_text(debunk_context)) or None

        return body_text, debunk_context

    except Exception as e:
        print(f"  -> Error parsing article text: {e}")
        return "", None


def _is_good_payload(payload):
    body_len = len(payload.get("body_text", "").strip())
    link_count = len(payload.get("media_and_links", {}).get("external_links", []))
    body = payload.get("body_text", "")

    if _contains_critical_noise(body):
        return False

    if body_len >= STRICT_MIN_BODY_CHARS:
        return True

    # Accept short body only if there is enough evidence links/media.
    video_count = len(payload.get("media_and_links", {}).get("videos", []))
    return (body_len >= 120 and (link_count + video_count) >= 1) or link_count >= 3


def scrape_article_payload(page, url, headline):
    best_payload = {
        "body_text": "",
        "debunk_context": None,
        "source": "Unknown",
        "source_domain": "unknown",
        "inferred_sources": ["Unknown"],
        "media_and_links": {"images": [], "videos": [], "external_links": []},
    }

    for candidate_url in _candidate_urls(url, headline):
        try:
            page.get(candidate_url)
        except Exception:
            continue

        # Guard against transient empty responses.
        try:
            html = page.html or ""
        except Exception:
            html = ""
        if not html.strip():
            continue

        body_text, debunk_context = scrape_article_text(page)
        media_and_links = extract_media_and_links(page)
        inferred_sources = guess_source(body_text, debunk_context, media_and_links["external_links"])

        source = _choose_source(inferred_sources, media_and_links["videos"], media_and_links["external_links"])
        source_domain = SOURCE_DOMAIN_MAP.get(source, source.lower())

        payload = {
            "body_text": body_text,
            "debunk_context": debunk_context,
            "source": source,
            "source_domain": source_domain,
            "inferred_sources": inferred_sources,
            "media_and_links": media_and_links,
        }

        if _is_good_payload(payload):
            return payload

        # Keep best attempt by body length for fallback.
        if len(payload["body_text"]) > len(best_payload["body_text"]):
            best_payload = payload

    return best_payload


def _is_low_quality_record(article_data):
    body = article_data.get("body_text", "")
    source = article_data.get("source", "Unknown")
    headline = article_data.get("headline", "")

    if _contains_critical_noise(body):
        return True
    if len((body or "").strip()) < STRICT_MIN_BODY_CHARS:
        return True
    if source == "Unknown" and _has_cyrillic(headline):
        return True
    return False

def build_final_dataset():
    articles_metadata = load_index()
    if not articles_metadata:
        return
        
    total_articles = len(articles_metadata)
    print(f"Loaded {total_articles} articles from index. Starting unified extraction...")
    
    final_dataset = []
    rejected_dataset = []
    
    # Initialize the fast SessionPage
    page = SessionPage()
    
    for index, item in enumerate(articles_metadata, start=1):
        url = item.get('url')
        print(f"[{index}/{total_articles}] Scraping: {url}")

        payload = scrape_article_payload(page, url, item.get('headline', ''))

        article_data = {
            "article_id": str(item.get('id')), 
            "source": payload["source"],
            "source_domain": payload["source_domain"],
            "is_fake": True,
            "topic_category": "TBD",
            "publication_date": item.get('publication_date'),
            "headline": item.get('headline'),
            "body_text": payload["body_text"],
            "metrics": {
                "views": item.get('views', 0),
                "likes": 0,
                "forwards_or_shares": 0,
                "comments": 0
            },
            "top_comments": [],
            "debunk_context": payload["debunk_context"],
            "inferred_sources": payload["inferred_sources"],
            "media_and_links": payload["media_and_links"],
        }

        if _is_low_quality_record(article_data):
            article_data["_quality_reject_reason"] = "low_quality_or_noise"
            rejected_dataset.append(article_data)
        else:
            final_dataset.append(article_data)
        
        # A short sleep to prevent the server from blocking your IP
        time.sleep(1)
        
    # Save the finalized data
    output_filename = 'stopfals_final_dataset.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, indent=4, ensure_ascii=False)

    reject_filename = 'stopfals_rejected_low_quality.json'
    with open(reject_filename, 'w', encoding='utf-8') as f:
        json.dump(rejected_dataset, f, indent=4, ensure_ascii=False)

    print(
        f"\n✅ Unified fake pipeline complete! Saved {len(final_dataset)} high-quality articles to {output_filename}. "
        f"Rejected {len(rejected_dataset)} low-quality articles to {reject_filename}."
    )

if __name__ == "__main__":
    build_final_dataset()