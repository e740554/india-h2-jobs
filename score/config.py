"""Scoring configuration for India H2 Workforce Atlas.

Scoring is done via Claude Code subagents — no API key needed.
This config controls batch size and retry behavior for the scoring pipeline.
"""

# Scoring dimensions
DIMENSIONS = [
    "h2_adjacency",
    "transition_demand",
    "skill_transferability",
    "digital_automation_exposure",
    "formalization_rate",
    "scarcity_risk",
]

# Pipeline settings
BATCH_SIZE = 50  # Occupations per batch
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2
