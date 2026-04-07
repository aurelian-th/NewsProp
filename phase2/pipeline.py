import argparse
import json
import math
import random
import re
import statistics
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


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
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore
except Exception:
    SentimentIntensityAnalyzer = None


SUPPORTED_TRANSLATION_LANGS = {"ro", "ru", "uk", "fr", "de", "it", "es"}


@dataclass
class Paths:
    fake: Path
    real: Path
    telegram: Path


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


def build_translator(enable_translation: bool):
    if not enable_translation:
        return None
    if GoogleTranslator is None:
        return None
    try:
        return GoogleTranslator(source="auto", target="en")
    except Exception:
        return None


def translate_to_english(text: str, src_lang: str, translator) -> Tuple[str, bool]:
    if not text.strip():
        return "", False

    if src_lang in {"en", "unknown"}:
        return text, False

    if src_lang not in SUPPORTED_TRANSLATION_LANGS and not re.search(r"[\u0400-\u04FF]", text):
        return text, False

    if translator is None:
        return text, False

    try:
        translated = translator.translate(text)
        return normalize_whitespace(translated), True
    except Exception:
        return text, False


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
        "is_fake": is_fake,
        "publication_date": publication_date,
        "headline": headline,
        "body_text": body_text,
        "engagement_metrics": engagement_metrics,
        "top_comments": top_comments,
        "debunk_context": debunk_context,
    }


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


def run_pipeline(paths: Paths, output_dir: Path, enable_translation: bool) -> None:
    if SentimentIntensityAnalyzer is None:
        raise RuntimeError(
            "Missing dependency: vaderSentiment. Install with: pip install -r phase2/requirements.txt"
        )

    analyzer = SentimentIntensityAnalyzer()
    translator = build_translator(enable_translation=enable_translation)

    fake_rows = [normalize_record(x, default_is_fake=True) for x in load_json_list(paths.fake)]
    real_rows = [normalize_record(x, default_is_fake=False) for x in load_json_list(paths.real)]
    tg_rows = [normalize_record(x, default_is_fake=None) for x in load_json_list(paths.telegram)]

    records = fake_rows + real_rows + tg_rows

    model = None
    if SentenceTransformer is not None:
        try:
            model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        except Exception:
            model = None

    texts_for_embedding: List[str] = []

    for rec in records:
        combined = normalize_whitespace(f"{rec['headline']}\n\n{rec['body_text']}")
        lang = detect_language(combined)
        text_en, translated = translate_to_english(combined, lang, translator)

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
        rec["sentiment"] = sentiment
        rec["impact_score"] = sentiment["emotional_score"]
        rec["reference_bin"] = assign_reference_bin(abs(sentiment["emotional_score"]))
        rec["engagement_total"] = engagement_total

        texts_for_embedding.append(text_en)

    if model is not None:
        vectors = model.encode(texts_for_embedding, normalize_embeddings=True, show_progress_bar=False)
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
        "records_total": len(records),
        "records_fake": len(fake_rows),
        "records_real": len(real_rows),
        "records_telegram": len(tg_rows),
        "translation_enabled": enable_translation,
        "translation_active": translator is not None,
        "embedding_enabled": model is not None,
        "high_engagement_threshold": threshold,
    }

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


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Phase 2 pipeline: normalize datasets, translate to English, score emotion with VADER, and export CI/calibration artifacts."
    )

    parser.add_argument(
        "--fake",
        type=Path,
        default=root / "scraper" / "fake" / "stopfals_final_dataset.json",
        help="Path to fake-news JSON list.",
    )
    parser.add_argument(
        "--real",
        type=Path,
        default=root / "scraper" / "real" / "stirimd_dataset.json",
        help="Path to real-news JSON list.",
    )
    parser.add_argument(
        "--telegram",
        type=Path,
        default=root / "scraper" / "telegram" / "moldova_news_50.json",
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

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = Paths(fake=args.fake, real=args.real, telegram=args.telegram)

    run_pipeline(
        paths=paths,
        output_dir=args.output_dir,
        enable_translation=not args.disable_translation,
    )


if __name__ == "__main__":
    main()
