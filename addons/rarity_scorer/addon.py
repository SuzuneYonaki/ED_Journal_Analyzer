"""Astrophysical Rarity Scorer addon: makes app/parser/rarity_scorer.py's
calculate_celestial_rarity() an optional, swappable "rarity_score" provider
instead of a hard-coded call inside journal_parser.py's _handle_scan.

app/parser/rarity_scorer.py itself stays in core (unmoved) -- this addon
only registers it into the provider slot journal_parser.py looks up. When
disabled, journal_parser.py falls back to a safe empty-equivalent result
(rarity_scorer.calculate_celestial_rarity already returns this exact shape
for invalid input, so it is reused here as the "off" default too), meaning:

- No age/orbital-extreme/density/ring rarity tags get added to a body's
  anomalies_json (app.analyzer.anomaly_finder's own tags -- rare stars,
  rare planets, high gravity, etc. -- are untouched, since that is a
  separate always-core module).
- No GGG *candidate* probability scoring or its TTS alert (GGG_evaluation
  is embedded inside calculate_celestial_rarity as calculate_ggg_probability).
- GGG *confirmed* detection (from the player's own Codex entries) is
  untouched -- that lookup lives directly in journal_parser.py, independent
  of this addon.
- Raw bio_signals counts and Exobiology species prediction are untouched
  (owned by the separate exobiology_prediction addon).
"""
from app.parser.rarity_scorer import calculate_celestial_rarity


def register(ctx):
    ctx.provide("rarity_score", calculate_celestial_rarity)
