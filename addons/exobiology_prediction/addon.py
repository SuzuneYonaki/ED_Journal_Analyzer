"""Exobiology Species Prediction addon: makes app/parser/exobiology.py's
predict_exobiology_candidates() / predict_system_exobiology_candidates()
optional, swappable providers instead of hard-coded calls scattered across
journal_parser.py, app/server/api.py's get_system_detail, and
app/services/edsm/body_importer.py.

app/parser/exobiology.py itself stays in core (unmoved). When disabled,
every call site falls back to an empty prediction list, which the
surrounding code already treats as a normal state (e.g. bio_signals == 0
already produces bio_predictions = []), so:

- No speculative genus/species candidates, estimated credit values, or
  high-value-bio TTS alerts are produced anywhere (live scan, historical
  batch reparse, the system-detail API endpoint, or EDSM body import).
- Left untouched (explicitly out of scope):
  - Raw bio_signals *counts* from FSSBodySignals/SAASignalsFound -- a
    separate journal fact, not a prediction.
  - Genuinely confirmed organics from scanned_organics (real DSS/collection
    data) -- journal_parser.py's _lock_confirmed_organics_into_predictions
    still promotes/inserts these into the (possibly empty) predictions list
    regardless of this addon's state.
"""
from app.parser.exobiology import predict_exobiology_candidates, predict_system_exobiology_candidates


def register(ctx):
    ctx.provide("exobiology_predict_body", predict_exobiology_candidates)
    ctx.provide("exobiology_predict_system", predict_system_exobiology_candidates)
