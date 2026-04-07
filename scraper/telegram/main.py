"""
Moldova Telegram News Scraper
==============================
Scrapes 50 posts (25 real + 25 fake) from verified Moldovan Telegram channels.

Requirements:
    pip install telethon python-dotenv tqdm

Setup:
    Create a .env file:
        TG_API_ID=12345678
        TG_API_HASH=abcdef1234567890abcdef1234567890
        TG_PHONE=+37369000000
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

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scraper.common.schema import enforce_final_schema

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
POSTS_PER_CHANNEL = 30
TARGET_FAKE  = 25
TARGET_TRUE  = 25
OUTPUT_FILE  = "moldova_news_50.json"

# ---------------------------------------------------------------------------
# Verified channel list  (checked March 2026)
# ---------------------------------------------------------------------------

CHANNELS = [
    # ── CREDIBLE ────────────────────────────────────────────────────────────
    {
        "handle": "JurnalTV",           # https://t.me/JurnalTV
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
        "handle": "moldovanews",        # https://t.me/moldovanews
        "name": "Moldova News",
        "is_propaganda": False,
    },
    {
        "handle": "agora_md",           # https://t.me/agora_md
        "name": "Agora.md",
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
        "handle": "prime_moldova",      # https://t.me/prime_moldova
        "name": "Prime Moldova",
        "is_propaganda": True,
    },
    {
        "handle": "gagauzinfo",         # https://t.me/gagauzinfo
        "name": "Gagauz Info",
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
            "publication_date":   msg.date.astimezone(timezone.utc).isoformat(),
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

    final = balance(all_records, TARGET_FAKE, TARGET_TRUE)

    output = []
    for r in final:
        raw = {
            "article_id":         r["article_id"],
            "source":             r["source"],
            "is_fake":            r["is_fake"],
            "publication_date":   r["publication_date"],
            "headline":           r["headline"],
            "body_text":          r["body_text"],
            "engagement_metrics": r["engagement_metrics"],
            "top_comments":       r["top_comments"],
            "debunk_context":     r["debunk_context"],
            "_meta": {
                "source_name":    r["source_name"],
                "classification": r["classification"],
                "telegram_url":   r["telegram_url"],
            },
        }
        output.append(enforce_final_schema(raw, default_source=r["source"]))

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