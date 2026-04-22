import argparse
import hashlib
import json
import math
import random
import re
import statistics
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Optional imports. The script can still run with graceful fallbacks.
try:
    from deep_translator import GoogleTranslator  # type: ignore
except Exception:
    GoogleTranslator = None

try:
    from langdetect import detect as detect_lang  # type: ignore
except Exception:
    detect_lang = None

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:
    SentenceTransformer = None

try:
    import requests  # type: ignore
except Exception:
    requests = None

try:
    from tqdm import tqdm  # type: ignore
except Exception:
    tqdm = None

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore
except Exception:
    SentimentIntensityAnalyzer = None


SUPPORTED_TRANSLATION_LANGS = {"ro", "ru", "uk", "fr", "de", "it", "es"}
DEFAULT_TRANSLATION_MAX_CHARS = 1800
DEFAULT_TRANSLATION_RETRIES = 1
DEFAULT_TRANSLATION_TIMEOUT = 15

_REQUEST_TIMEOUT_PATCHED = False


@dataclass
class Paths:
    fake: Path
    real: Path
    telegram: Path


def resolve_existing_path(candidates: List[Path]) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def progress_iter(items: List[Any], desc: str, fallback_every: int = 50):
    total = len(items)
    if tqdm is not None:
        yield from tqdm(items, total=total, desc=desc)
        return

    for idx, item in enumerate(items, start=1):
        if idx == 1 or idx % max(1, fallback_every) == 0 or idx == total:
            print(f"[{desc}] {idx}/{total}")
        yield item


def load_json_list(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected list JSON in {path}, got {type(data).__name__}")
    return [x for x in data if isinstance(x, dict)]


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[\t ]+", " ", text)
    return text.strip()


def normalize_date(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
        except Exception:
            return None
    if not isinstance(value, str):
        return None

    raw = value.strip()
    if not raw:
        return None

    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass

    formats = [
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            continue

    return None


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def detect_language(text: str) -> str:
    if not text.strip():
        return "unknown"

    # Simple Cyrillic fallback when langdetect is unavailable.
    if re.search(r"[\u0400-\u04FF]", text):
        if detect_lang is None:
            return "ru"

    if detect_lang is None:
        return "unknown"

    try:
        return detect_lang(text)
    except Exception:
        return "unknown"


def build_translator(enable_translation: bool, request_timeout: int):
    global _REQUEST_TIMEOUT_PATCHED

    if not enable_translation:
        return None
    if GoogleTranslator is None:
        return None

    if requests is not None and not _REQUEST_TIMEOUT_PATCHED:
        original_get = requests.get

        def _timeout_get(*args, **kwargs):
            kwargs.setdefault("timeout", request_timeout)
            return original_get(*args, **kwargs)

        requests.get = _timeout_get  # type: ignore[assignment]
        _REQUEST_TIMEOUT_PATCHED = True

    try:
        return GoogleTranslator(source="auto", target="en")
    except Exception:
        return None


def _truncate_for_translation(text: str, max_chars: int) -> Tuple[str, bool]:
    if max_chars <= 0 or len(text) <= max_chars:
        return text, False

    truncated = text[:max_chars]
    # Avoid cutting words mid-token when possible.
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return truncated, True


def translate_to_english(
    text: str,
    src_lang: str,
    translator,
    cache: Dict[str, str],
    max_chars: int,
    retries: int,
) -> Tuple[str, bool, bool]:
    if not text.strip():
        return "", False, False

    if src_lang in {"en", "unknown"}:
        return text, False, False

    if src_lang not in SUPPORTED_TRANSLATION_LANGS and not re.search(r"[\u0400-\u04FF]", text):
        return text, False, False

    if translator is None:
        return text, False, False

    text_for_translation, was_truncated = _truncate_for_translation(text, max_chars=max_chars)
    cache_key = hashlib.sha1(f"{src_lang}|{text_for_translation}".encode("utf-8", errors="ignore")).hexdigest()
    if cache_key in cache:
        return cache[cache_key], True, was_truncated

    attempts = max(1, retries + 1)
    for attempt in range(attempts):
        try:
            translated = translator.translate(text_for_translation)
            translated_norm = normalize_whitespace(translated)
            cache[cache_key] = translated_norm
            return translated_norm, True, was_truncated
        except Exception:
            if attempt < attempts - 1:
                time.sleep(0.4 * (attempt + 1))

    return text_for_translation, False, was_truncated


def extract_metrics(raw: Dict[str, Any]) -> Dict[str, int]:
    metrics = raw.get("engagement_metrics") or raw.get("metrics") or {}
    views = safe_int(metrics.get("views", 0))
    likes = safe_int(metrics.get("likes", 0))
    shares = safe_int(metrics.get("shares", metrics.get("forwards_or_shares", 0)))
    comments = safe_int(metrics.get("comments", 0))

    reactions = metrics.get("reactions", {})
    if isinstance(reactions, dict):
        likes += sum(safe_int(v) for v in reactions.values())

    return {
        "views": max(views, 0),
        "likes": max(likes, 0),
        "shares": max(shares, 0),
        "comments": max(comments, 0),
    }


def normalize_record(raw: Dict[str, Any], default_is_fake: Optional[bool]) -> Dict[str, Any]:
    article_id = str(raw.get("article_id") or uuid.uuid4())
    source = str(
        raw.get("source")
        or raw.get("source_domain")
        or (raw.get("_meta") or {}).get("source_name")
        or "unknown"
    ).strip()

    headline = normalize_whitespace(str(raw.get("headline") or ""))
    body_text = normalize_whitespace(str(raw.get("body_text") or ""))

    top_comments = raw.get("top_comments")
    if not isinstance(top_comments, list):
        top_comments = []
    top_comments = [normalize_whitespace(str(x)) for x in top_comments if str(x).strip()]

    debunk = raw.get("debunk_context")
    debunk_context = normalize_whitespace(str(debunk)) if debunk else None

    engagement_metrics = extract_metrics(raw)

    publication_date = normalize_date(raw.get("publication_date"))

    raw_is_fake = raw.get("is_fake")
    if isinstance(raw_is_fake, bool):
        is_fake = raw_is_fake
    elif raw_is_fake in {0, 1}:
        is_fake = bool(raw_is_fake)
    elif default_is_fake is not None:
        is_fake = default_is_fake
    else:
        is_fake = False

    return {
        "article_id": article_id,
        "source": source,
        "source_domain": str(raw.get("source_domain") or "").strip() or None,
        "is_fake": is_fake,
        "publication_date": publication_date,
        "headline": headline,
        "body_text": body_text,
        "engagement_metrics": engagement_metrics,
        "top_comments": top_comments,
        "debunk_context": debunk_context,
    }


def quality_flags(record: Dict[str, Any], min_text_chars: int) -> List[str]:
    flags: List[str] = []
    source = (record.get("source") or "").strip().lower()
    source_domain = (record.get("source_domain") or "").strip().lower()
    headline = (record.get("headline") or "").strip()
    body = (record.get("body_text") or "").strip()
    combined = normalize_whitespace(f"{headline}\n\n{body}")

    if not headline:
        flags.append("missing_headline")
    if not body:
        flags.append("missing_body")
    if len(combined) < min_text_chars:
        flags.append("short_text")
    if source in {"unknown", ""}:
        flags.append("unknown_source")
    if source_domain in {"unknown", ""}:
        flags.append("unknown_source_domain")

    return flags


def sentence_chunks(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", text) if x.strip()]


def compute_emotion_features(analyzer: Any, text_en: str) -> Dict[str, float]:
    if not text_en.strip():
        return {
            "vader_neg": 0.0,
            "vader_neu": 1.0,
            "vader_pos": 0.0,
            "emotional_score": 0.0,
            "emotional_intensity": 0.0,
            "emotional_density": 0.0,
        }

    doc_scores = analyzer.polarity_scores(text_en)
    compound = float(doc_scores["compound"])

    sentences = sentence_chunks(text_en)
    if not sentences:
        return {
            "vader_neg": float(doc_scores["neg"]),
            "vader_neu": float(doc_scores["neu"]),
            "vader_pos": float(doc_scores["pos"]),
            "emotional_score": compound,
            "emotional_intensity": abs(compound),
            "emotional_density": 0.0,
        }

    sentence_compounds = [analyzer.polarity_scores(s)["compound"] for s in sentences]
    density = sum(1 for s in sentence_compounds if abs(s) >= 0.5) / len(sentence_compounds)

    return {
        "vader_neg": float(doc_scores["neg"]),
        "vader_neu": float(doc_scores["neu"]),
        "vader_pos": float(doc_scores["pos"]),
        "emotional_score": compound,
        "emotional_intensity": abs(compound),
        "emotional_density": float(density),
    }


def bootstrap_mean_ci(values: List[float], n_boot: int = 1000, ci: float = 0.95) -> Dict[str, Optional[float]]:
    vals = [v for v in values if isinstance(v, (int, float))]
    if not vals:
        return {"mean": None, "ci_low": None, "ci_high": None, "n": 0}

    mean = float(statistics.fmean(vals))
    if len(vals) == 1:
        return {"mean": mean, "ci_low": mean, "ci_high": mean, "n": 1}

    boot_means: List[float] = []
    for _ in range(n_boot):
        sample = [random.choice(vals) for _ in range(len(vals))]
        boot_means.append(float(statistics.fmean(sample)))

    boot_means.sort()
    alpha = (1.0 - ci) / 2.0
    lo_idx = int(alpha * (len(boot_means) - 1))
    hi_idx = int((1.0 - alpha) * (len(boot_means) - 1))

    return {
        "mean": mean,
        "ci_low": boot_means[lo_idx],
        "ci_high": boot_means[hi_idx],
        "n": len(vals),
    }


def cohen_d(a: List[float], b: List[float]) -> Optional[float]:
    if len(a) < 2 or len(b) < 2:
        return None

    mean_a = statistics.fmean(a)
    mean_b = statistics.fmean(b)
    var_a = statistics.variance(a)
    var_b = statistics.variance(b)

    pooled = ((len(a) - 1) * var_a + (len(b) - 1) * var_b) / (len(a) + len(b) - 2)
    if pooled <= 0:
        return None

    return float((mean_a - mean_b) / math.sqrt(pooled))


def assign_reference_bin(value_abs: float) -> str:
    if value_abs < 0.2:
        return "very_low"
    if value_abs < 0.4:
        return "low"
    if value_abs < 0.6:
        return "medium"
    if value_abs < 0.8:
        return "high"
    return "very_high"


def run_pipeline(
    paths: Paths,
    output_dir: Path,
    enable_translation: bool,
    min_text_chars: int,
    translation_max_chars: int,
    translation_retries: int,
    translation_timeout: int,
    enable_embeddings: bool,
) -> None:
    if SentimentIntensityAnalyzer is None:
        raise RuntimeError(
            "Missing dependency: vaderSentiment. Install with: pip install -r phase2/requirements.txt"
        )

    analyzer = SentimentIntensityAnalyzer()
    translator = build_translator(enable_translation=enable_translation, request_timeout=translation_timeout)
    translation_cache: Dict[str, str] = {}

    t0 = time.perf_counter()
    print("[Phase2] Loading datasets...")

    fake_rows_raw = [normalize_record(x, default_is_fake=True) for x in load_json_list(paths.fake)]
    real_rows_raw = [normalize_record(x, default_is_fake=False) for x in load_json_list(paths.real)]
    tg_rows_raw = [normalize_record(x, default_is_fake=None) for x in load_json_list(paths.telegram)]

    all_rows = fake_rows_raw + real_rows_raw + tg_rows_raw

    records: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    quality_counter: Dict[str, int] = {}

    print("[Phase2] Running quality filtering...")
    for row in progress_iter(all_rows, desc="Quality"):
        flags = quality_flags(row, min_text_chars=min_text_chars)
        if flags:
            for flag in flags:
                quality_counter[flag] = quality_counter.get(flag, 0) + 1
        if any(flag in {"missing_body", "short_text"} for flag in flags):
            rejected.append({"article_id": row["article_id"], "flags": flags, "source": row["source"]})
            continue
        records.append(row)

    fake_rows = [r for r in records if r["is_fake"] is True]
    real_rows = [r for r in records if r["is_fake"] is False]
    tg_rows = [r for r in records if r["source"] not in {"stiri.md"} and r["is_fake"] in {True, False}]

    model = None
    if enable_embeddings and SentenceTransformer is not None:
        try:
            model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        except Exception:
            model = None

    texts_for_embedding: List[str] = []

    print("[Phase2] Running language detection, translation, sentiment, and feature extraction...")
    for rec in progress_iter(records, desc="NLP"):
        combined = normalize_whitespace(f"{rec['headline']}\n\n{rec['body_text']}")
        lang = detect_language(combined)
        text_en, translated, translation_truncated = translate_to_english(
            combined,
            lang,
            translator,
            cache=translation_cache,
            max_chars=translation_max_chars,
            retries=translation_retries,
        )

        sentiment = compute_emotion_features(analyzer, text_en)

        engagement = rec["engagement_metrics"]
        engagement_total = (
            safe_int(engagement.get("views", 0))
            + safe_int(engagement.get("likes", 0))
            + safe_int(engagement.get("shares", 0))
            + safe_int(engagement.get("comments", 0))
        )

        rec["language_detected"] = lang
        rec["text_en"] = text_en
        rec["translation_applied"] = translated
        rec["translation_truncated"] = translation_truncated
        rec["sentiment"] = sentiment
        rec["impact_score"] = sentiment["emotional_score"]
        rec["reference_bin"] = assign_reference_bin(abs(sentiment["emotional_score"]))
        rec["engagement_total"] = engagement_total

        texts_for_embedding.append(text_en)

    if model is not None:
        print("[Phase2] Encoding embeddings (this can take several minutes on CPU)...")
        vectors = model.encode(texts_for_embedding, normalize_embeddings=True, show_progress_bar=True)
        for rec, vec in zip(records, vectors):
            rec["embedding"] = [round(float(v), 8) for v in vec.tolist()]
    else:
        for rec in records:
            rec["embedding"] = []

    # Confidence intervals by class
    fake_scores = [r["sentiment"]["emotional_score"] for r in records if r["is_fake"] is True]
    real_scores = [r["sentiment"]["emotional_score"] for r in records if r["is_fake"] is False]

    ci_summary = {
        "fake": bootstrap_mean_ci(fake_scores),
        "real": bootstrap_mean_ci(real_scores),
        "all": bootstrap_mean_ci(fake_scores + real_scores),
    }

    # Confidence intervals by source and language
    by_source: Dict[str, List[float]] = {}
    by_language: Dict[str, List[float]] = {}

    for r in records:
        by_source.setdefault(r["source"], []).append(r["sentiment"]["emotional_score"])
        by_language.setdefault(r["language_detected"], []).append(r["sentiment"]["emotional_score"])

    ci_by_source = {k: bootstrap_mean_ci(v) for k, v in sorted(by_source.items())}
    ci_by_language = {k: bootstrap_mean_ci(v) for k, v in sorted(by_language.items())}

    # Empirical calibration:
    # Probability of high engagement (top quartile) by emotional reference bin.
    totals = [r["engagement_total"] for r in records]
    if totals:
        threshold = sorted(totals)[max(0, int(0.75 * (len(totals) - 1)))]
    else:
        threshold = 0

    calibration: Dict[str, Dict[str, Any]] = {}
    for bin_name in ["very_low", "low", "medium", "high", "very_high"]:
        subset = [r for r in records if r["reference_bin"] == bin_name]
        n = len(subset)
        if n == 0:
            calibration[bin_name] = {
                "n": 0,
                "high_engagement_probability": None,
                "mean_impact_score": None,
            }
            continue

        high = sum(1 for r in subset if r["engagement_total"] >= threshold)
        calibration[bin_name] = {
            "n": n,
            "high_engagement_probability": round(high / n, 6),
            "mean_impact_score": round(statistics.fmean(r["impact_score"] for r in subset), 6),
        }

    comparisons = {
        "mean_fake": (statistics.fmean(fake_scores) if fake_scores else None),
        "mean_real": (statistics.fmean(real_scores) if real_scores else None),
        "delta_fake_minus_real": (
            (statistics.fmean(fake_scores) - statistics.fmean(real_scores))
            if fake_scores and real_scores
            else None
        ),
        "cohen_d_fake_vs_real": cohen_d(fake_scores, real_scores),
    }

    summary = {
        "records_total": len(all_rows),
        "records_kept": len(records),
        "records_rejected": len(rejected),
        "records_fake": len([r for r in records if r["is_fake"] is True]),
        "records_real": len([r for r in records if r["is_fake"] is False]),
        "records_telegram_estimate": len(tg_rows),
        "translation_enabled": enable_translation,
        "translation_active": translator is not None,
        "translation_cache_size": len(translation_cache),
        "translation_max_chars": translation_max_chars,
        "translation_retries": translation_retries,
        "translation_timeout_seconds": translation_timeout,
        "embedding_enabled": model is not None,
        "high_engagement_threshold": threshold,
        "min_text_chars": min_text_chars,
    }

    print("[Phase2] Writing output artifacts...")
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = output_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)

    with (output_dir / "normalized_with_phase2.json").open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    with (artifacts / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    with (artifacts / "confidence_intervals.json").open("w", encoding="utf-8") as f:
        json.dump(
            {
                "global": ci_summary,
                "by_source": ci_by_source,
                "by_language": ci_by_language,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    with (artifacts / "empirical_calibration.json").open("w", encoding="utf-8") as f:
        json.dump(calibration, f, ensure_ascii=False, indent=2)

    with (artifacts / "comparisons.json").open("w", encoding="utf-8") as f:
        json.dump(comparisons, f, ensure_ascii=False, indent=2)

    with (artifacts / "data_quality.json").open("w", encoding="utf-8") as f:
        json.dump(
            {
                "counters": dict(sorted(quality_counter.items())),
                "rejected_examples": rejected[:200],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    elapsed = round(time.perf_counter() - t0, 2)
    print(f"[Phase2] Done in {elapsed}s. Kept {len(records)} records, rejected {len(rejected)}.")


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    default_fake = resolve_existing_path(
        [
            root / "scraper" / "fake" / "stopfals_final_dataset.json",
            root / "stopfals_final_dataset.json",
        ]
    )
    default_real = resolve_existing_path(
        [
            root / "scraper" / "real" / "stirimd_dataset.json",
            root / "stirimd_dataset.json",
        ]
    )
    default_telegram = resolve_existing_path(
        [
            root / "scraper" / "telegram" / "moldova_news_50.json",
            root / "moldova_news_50.json",
        ]
    )

    parser = argparse.ArgumentParser(
        description="Phase 2 pipeline: normalize datasets, translate to English, score emotion with VADER, and export CI/calibration artifacts."
    )

    parser.add_argument(
        "--fake",
        type=Path,
        default=default_fake,
        help="Path to fake-news JSON list.",
    )
    parser.add_argument(
        "--real",
        type=Path,
        default=default_real,
        help="Path to real-news JSON list.",
    )
    parser.add_argument(
        "--telegram",
        type=Path,
        default=default_telegram,
        help="Path to Telegram JSON list.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "phase2" / "outputs",
        help="Directory for normalized data and analysis artifacts.",
    )
    parser.add_argument(
        "--disable-translation",
        action="store_true",
        help="Skip translation and process text in original language.",
    )
    parser.add_argument(
        "--translation-max-chars",
        type=int,
        default=DEFAULT_TRANSLATION_MAX_CHARS,
        help="Max characters per record sent to online translator to avoid long/hanging requests.",
    )
    parser.add_argument(
        "--translation-retries",
        type=int,
        default=DEFAULT_TRANSLATION_RETRIES,
        help="Retry count for failed translation requests.",
    )
    parser.add_argument(
        "--translation-timeout",
        type=int,
        default=DEFAULT_TRANSLATION_TIMEOUT,
        help="HTTP timeout in seconds for translator requests.",
    )
    parser.add_argument(
        "--disable-embeddings",
        action="store_true",
        help="Skip sentence-transformer embeddings for faster debug runs.",
    )
    parser.add_argument(
        "--min-text-chars",
        type=int,
        default=120,
        help="Minimum combined headline+body chars required to keep a record in Phase 2.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = Paths(fake=args.fake, real=args.real, telegram=args.telegram)

    run_pipeline(
        paths=paths,
        output_dir=args.output_dir,
        enable_translation=not args.disable_translation,
        min_text_chars=max(0, int(args.min_text_chars)),
        translation_max_chars=max(200, int(args.translation_max_chars)),
        translation_retries=max(0, int(args.translation_retries)),
        translation_timeout=max(5, int(args.translation_timeout)),
        enable_embeddings=not args.disable_embeddings,
    )


if __name__ == "__main__":
    main()
