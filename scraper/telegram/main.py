"""
Moldova Telegram News Scraper
==============================
Scrapes Telegram posts from Moldovan channels and balances fake/true classes.

Requirements:
    pip install telethon python-dotenv tqdm

Setup:
    Create a .env file:
        TG_API_ID=12345678
        TG_API_HASH=abcdef1234567890abcdef1234567890
        TG_PHONE=+37369000000
        POSTS_PER_CHANNEL=120
        TARGET_FAKE=200
        TARGET_TRUE=200
"""

import asyncio
import json
import logging
import os
import random
import re
import sys
import uuid
from datetime import timezone
from typing import Dict, List, Optional

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import Message
from tqdm import tqdm

print(f"Python {sys.version}")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv()
API_ID       = int(os.getenv("TG_API_ID", "0"))
API_HASH     = os.getenv("TG_API_HASH", "")
PHONE        = os.getenv("TG_PHONE", "")
SESSION_NAME = "moldova_scraper_session"
POSTS_PER_CHANNEL = int(os.getenv("POSTS_PER_CHANNEL", "120"))
TARGET_FAKE  = int(os.getenv("TARGET_FAKE", "200"))
TARGET_TRUE  = int(os.getenv("TARGET_TRUE", "200"))
OUTPUT_FILE  = os.path.join(os.path.dirname(__file__), "moldova_news_telegram.json")

# ---------------------------------------------------------------------------
# Verified channel list  (checked March 2026)
# ---------------------------------------------------------------------------

CHANNELS = [
    # ── CREDIBLE ────────────────────────────────────────────────────────────
    {
        "handle": "Jurnal_TV",           # https://t.me/JurnalTV
        "name": "Jurnal TV",
        "is_propaganda": False,
    },
    {
        "handle": "zdgmd",              # https://t.me/zdgmd
        "name": "Ziarul de Garda",
        "is_propaganda": False,
    },
    {
        "handle": "tv8md",              # https://t.me/tv8md
        "name": "TV8 Moldova",
        "is_propaganda": False,
    },
    {
        "handle": "newsmakerlive",      # https://t.me/newsmakerlive
        "name": "NewsMaker Moldova",
        "is_propaganda": False,
    },
    {
        "handle": "agoramd",           # https://t.me/agora_md
        "name": "Agora.md",
        "is_propaganda": False,
    },
    {
        "handle": "protvchisinauofficial",      # https://t.me/protvchisinau
        "name": "PRO TV Chisinau",
        "is_propaganda": False,
    },
    {
        "handle": "unimedia_info",           # https://t.me/unimedia
        "name": "UNIMEDIA",
        "is_propaganda": False,
    },
    {
        "handle": "realitateamd",      # https://t.me/realitatea_md
        "name": "Realitatea",
        "is_propaganda": False,
    },
    {
        "handle": "deschide_md",        # https://t.me/deschide_md
        "name": "Deschide.MD",
        "is_propaganda": False,
    },
    {
        "handle": "radiomoldova",       # https://t.me/radiomoldova
        "name": "Radio Moldova",
        "is_propaganda": False,
    },
    # ── PROPAGANDA / PRO-RUSSIAN ────────────────────────────────────────────

    {
        "handle": "KpMoldova",          # https://t.me/KpMoldova
        "name": "KP Moldova",
        "is_propaganda": True,
    },
    {
        "handle": "nokta_md",           # https://t.me/nokta_md  (pro-Russian populist)
        "name": "Nokta.md",
        "is_propaganda": True,
    },
    {
        "handle": "gagauzinfo",         # https://t.me/gagauzinfo
        "name": "Gagauz Info",
        "is_propaganda": True,
    },
    {
        "handle": "canal5_md",           # https://t.me/canal5md
        "name": "Canal 5",
        "is_propaganda": True,
    },
    {
        "handle": "newsmd24",    # https://t.me/moldova24online
        "name": "Moldova24",
        "is_propaganda": True,
    },
    {
        "handle": "rusputnikmd_2",        # https://t.me/rusputnikmd
        "name": "Sputnik Moldova",
        "is_propaganda": True,
    },
]

# ---------------------------------------------------------------------------
# Fake-news heuristics
# ---------------------------------------------------------------------------

FAKE_PATTERNS = [
    r"\bFALS\b", r"\bmanipulare\b", r"\bpropaganda\b", r"\bdezminit\b",
    r"\bregimul de la Chisinau\b", r"\bnazis\b", r"\bNATO\b.*\bagresiune\b",
    r"\bMaia Sandu\b.*\bpapusa\b", r"LOZH", r"provokacia", r"feik",
    r"\boccident.*\bimperiali", r"\bsanctiunile ucid\b",
]

CRED_PATTERNS = [
    r"\bpotrivit\b", r"\bconform\b", r"\bdeclarat\b", r"\bconfirmat\b",
    r"\bdate oficiale\b", r"\bguvernul\b", r"\bparlamentul\b",
]

URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)


def classify(text: str, is_propaganda_source: bool) -> bool:
    fake_hits = sum(1 for p in FAKE_PATTERNS if re.search(p, text, re.IGNORECASE))
    cred_hits = sum(1 for p in CRED_PATTERNS if re.search(p, text, re.IGNORECASE))
    if re.search(r"\bFALS\b", text, re.IGNORECASE):
        return True
    if is_propaganda_source and fake_hits >= 1:
        return True
    if not is_propaganda_source and cred_hits >= 1 and fake_hits == 0:
        return False
    return is_propaganda_source  # default: trust the source label


# ---------------------------------------------------------------------------
# Engagement extraction
# ---------------------------------------------------------------------------

def get_engagement(msg: Message) -> Dict:
    views    = getattr(msg, "views", 0) or 0
    forwards = getattr(msg, "forwards", 0) or 0
    replies  = 0
    if hasattr(msg, "replies") and msg.replies:
        replies = msg.replies.replies or 0
    likes = 0
    reactions_map: Dict[str, int] = {}
    if hasattr(msg, "reactions") and msg.reactions:
        for r in (msg.reactions.results or []):
            emoji = getattr(r.reaction, "emoticon", "?")
            reactions_map[emoji] = r.count
            likes += r.count
    return {
        "views": views, "likes": likes,
        "shares": forwards, "comments": replies,
        "reactions": reactions_map,
    }


def infer_sources(text: str) -> List[str]:
    lowered = text.lower()
    sources: List[str] = ["Telegram"]
    source_rules = [
        ("YouTube", ["youtube.com", "youtu.be", "youtube"]),
        ("TikTok", ["tiktok.com", "tiktok"]),
        ("Instagram", ["instagram.com", "instagram"]),
        ("Facebook", ["facebook.com", "fb.com", "facebook"]),
    ]

    for source_name, hints in source_rules:
        if any(hint in lowered for hint in hints):
            sources.append(source_name)

    # Keep insertion order and uniqueness
    seen = set()
    unique_sources: List[str] = []
    for src in sources:
        if src not in seen:
            unique_sources.append(src)
            seen.add(src)
    return unique_sources


def extract_media_and_links(text: str) -> Dict[str, Optional[List[str]]]:
    image_links: List[str] = []
    video_links: List[str] = []
    external_links: List[str] = []

    raw_links = [u.rstrip(")].,;!?\"'") for u in URL_RE.findall(text)]
    for url in raw_links:
        low = url.lower()
        if re.search(r"\.(jpg|jpeg|png|gif|webp|bmp)(\?.*)?$", low):
            image_links.append(url)
            continue
        if any(site in low for site in ["youtube.com", "youtu.be", "vimeo.com", "rutube", "tiktok.com"]):
            video_links.append(url)
            continue
        external_links.append(url)

    def uniq(values: List[str]) -> Optional[List[str]]:
        if not values:
            return None
        return list(dict.fromkeys(values))

    return {
        "images": uniq(image_links),
        "videos": uniq(video_links),
        "external_links": uniq(external_links),
    }


# ---------------------------------------------------------------------------
# Scrape one channel
# ---------------------------------------------------------------------------

async def scrape_channel(client: TelegramClient, cfg: Dict, limit: int) -> List[Dict]:
    handle  = cfg["handle"]
    records: List[Dict] = []

    try:
        entity = await client.get_entity(handle)
    except Exception as e:
        log.error(f"@{handle} — could not resolve: {e}")
        return records

    log.info(f"Scraping @{handle} ...")
    count = 0

    async for msg in client.iter_messages(entity, limit=limit):
        if not isinstance(msg, Message):
            continue

        # msg.message holds text for plain posts AND captions for media posts
        text = (msg.message or "").strip()
        if len(text) < 15:
            continue

        # Skip posts that are just URLs / invite links with no real content
        text_no_urls = re.sub(r'https?://\S+', '', text).strip()
        if len(text_no_urls) < 15:
            continue

        is_fake = classify(text, cfg["is_propaganda"])

        records.append({
            "article_id":         str(uuid.uuid4()),
            "source":             handle,
            "source_name":        cfg["name"],
            "is_fake":            is_fake,
            "classification":     "heuristic+source_label",
            "publication_date":   msg.date.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "headline":           text.split("\n")[0][:200],
            "body_text":          text,
            "telegram_url":       f"https://t.me/{handle}/{msg.id}",
            "engagement_metrics": get_engagement(msg),
            "top_comments":       [],
            "debunk_context":     None,
        })
        count += 1

    log.info(f"  -> {count} posts from @{handle}")
    return records


# ---------------------------------------------------------------------------
# Fetch comments (best-effort, many channels have them disabled)
# ---------------------------------------------------------------------------

async def add_comments(client: TelegramClient, records: List[Dict]) -> None:
    for rec in records:
        try:
            handle = rec["source"]
            msg_id = int(rec["telegram_url"].split("/")[-1])
            comments: List[str] = []
            async for reply in client.iter_messages(handle, reply_to=msg_id, limit=3):
                if isinstance(reply, Message) and reply.message:
                    comments.append(reply.message[:200])
            rec["top_comments"] = comments
        except Exception:
            pass
        await asyncio.sleep(0.5)


# ---------------------------------------------------------------------------
# Balance to 25 fake + 25 true
# ---------------------------------------------------------------------------

def balance(all_records: List[Dict], n_fake: int, n_true: int) -> List[Dict]:
    fakes = [r for r in all_records if     r["is_fake"]]
    trues = [r for r in all_records if not r["is_fake"]]
    random.shuffle(fakes)
    random.shuffle(trues)
    if len(fakes) < n_fake:
        log.warning(f"Only {len(fakes)} fake posts available (wanted {n_fake})")
    if len(trues) < n_true:
        log.warning(f"Only {len(trues)} true posts available (wanted {n_true})")
    selected = fakes[:n_fake] + trues[:n_true]
    random.shuffle(selected)
    return selected


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    if API_ID == 0 or not API_HASH or not PHONE:
        print("\n ERROR: Set TG_API_ID, TG_API_HASH, TG_PHONE in .env\n")
        return

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start(phone=PHONE)
    log.info("Telegram connected")

    all_records: List[Dict] = []

    for cfg in tqdm(CHANNELS, desc="Channels"):
        records = await scrape_channel(client, cfg, POSTS_PER_CHANNEL)
        log.info(f"  Fetching comments for @{cfg['handle']} ...")
        await add_comments(client, records)
        all_records.extend(records)
        await asyncio.sleep(2)

    fake_raw = sum(1 for r in all_records if r["is_fake"])
    true_raw = sum(1 for r in all_records if not r["is_fake"])
    log.info(f"Raw total: {len(all_records)} posts  (fake={fake_raw}, true={true_raw})")

    if len(all_records) > (TARGET_FAKE + TARGET_TRUE):
        log.info(
            f"Keeping all {len(all_records)} scraped posts (above target {TARGET_FAKE + TARGET_TRUE})"
        )
    final = all_records

    output = []
    for r in final:
        media_and_links = extract_media_and_links(r["body_text"])
        inferred_sources = infer_sources(r["body_text"])
        output.append({
            "article_id":         r["article_id"],
            "source":             r["source"],
            "source_domain":      "t.me",
            "is_fake":            r["is_fake"],
            "topic_category":     None,
            "publication_date":   r["publication_date"],
            "headline":           r["headline"],
            "body_text":          r["body_text"],
            "metrics": {
                "views": r["engagement_metrics"].get("views", 0),
                "likes": r["engagement_metrics"].get("likes", 0),
                "forwards_or_shares": r["engagement_metrics"].get("shares", 0),
                "comments": r["engagement_metrics"].get("comments", 0),
            },
            "top_comments":       r["top_comments"],
            "debunk_context":     r["debunk_context"],
            "inferred_sources":   inferred_sources if inferred_sources else None,
            "media_and_links":    media_and_links if any(v is not None for v in media_and_links.values()) else None,
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    await client.disconnect()

    fake_n = sum(1 for r in output if r["is_fake"])
    true_n = sum(1 for r in output if not r["is_fake"])
    print(f"\n{'='*50}")
    print(f"  Saved {len(output)} records -> {OUTPUT_FILE}")
    print(f"  Fake: {fake_n}  |  True: {true_n}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)