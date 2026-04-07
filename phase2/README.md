# Phase 2 Pipeline (NLP + Emotional Scoring)

This module standardizes mixed-format scraped datasets, translates multilingual text to English, computes emotional impact with VADER, and exports outputs needed for analysis and simulation.

## Why this matches your current decision

The pipeline implements this exact flow:
1. Normalize all datasets into one schema.
2. Detect language per item.
3. Translate non-English content to English.
4. Compute VADER sentiment from translated text.
5. Use VADER compound as emotional impact score in range [-1, 1].
6. Produce confidence intervals, empirical calibration, and fake-vs-real comparisons.

## Input datasets (default)

- `scraper/fake/stopfals_final_dataset.json`
- `scraper/real/stirimd_dataset.json`
- `scraper/telegram/moldova_news_50.json`

## Output files

Main normalized dataset:
- `phase2/outputs/normalized_with_phase2.json`

Analysis artifacts:
- `phase2/outputs/artifacts/summary.json`
- `phase2/outputs/artifacts/confidence_intervals.json`
- `phase2/outputs/artifacts/empirical_calibration.json`
- `phase2/outputs/artifacts/comparisons.json`

## Normalized schema

Canonical schema files used across the project:
- `schemas/news_record.schema.json`
- `schemas/news_dataset.schema.json`

```json
{
  "article_id": "string",
  "source": "string",
  "is_fake": false,
  "publication_date": "ISO8601 or null",
  "headline": "string",
  "body_text": "string",
  "engagement_metrics": {
    "views": 0,
    "likes": 0,
    "shares": 0,
    "comments": 0
  },
  "top_comments": [],
  "debunk_context": null,
  "language_detected": "ro|ru|en|...",
  "text_en": "string",
  "translation_applied": true,
  "sentiment": {
    "vader_neg": 0.0,
    "vader_neu": 0.0,
    "vader_pos": 0.0,
    "emotional_score": 0.0,
    "emotional_intensity": 0.0,
    "emotional_density": 0.0
  },
  "impact_score": 0.0,
  "reference_bin": "very_low|low|medium|high|very_high",
  "engagement_total": 0,
  "embedding": []
}
```

## Emotional metrics definitions

- `emotional_score`: VADER compound score in [-1, 1].
- `emotional_intensity`: absolute value of emotional_score.
- `emotional_density`: share of sentence-level compounds where abs(score) >= 0.5.

## Confidence intervals

The script computes bootstrapped 95% confidence intervals for mean emotional score:
- Global (`fake`, `real`, `all`)
- By source
- By detected language

## Empirical calibration

Calibration is computed from your own data:
- Create emotional bins from absolute impact score.
- Define high engagement as top-quartile `engagement_total`.
- Compute `P(high_engagement | emotional_bin)`.

This gives an empirical reference curve for paper discussion.

## Fake vs real comparison

The script exports:
- Mean score for fake
- Mean score for real
- Mean delta (fake - real)
- Cohen's d effect size

## Optional embeddings

If `sentence-transformers` is available, each article gets an embedding using:
- `sentence-transformers/all-MiniLM-L6-v2`

If unavailable, `embedding` is left as an empty list so the rest of Phase 2 still runs.

## Run

```bash
python phase2/pipeline.py
```

Optional flags:

```bash
python phase2/pipeline.py --disable-translation
python phase2/pipeline.py --fake <path> --real <path> --telegram <path> --output-dir <path>
```

## Notes

- Translation uses `deep-translator` + Google Translate backend when available.
- If translation package is missing, pipeline keeps original text and still computes scores.
- Telegram records with uncertain labels keep their `is_fake` value from source.
