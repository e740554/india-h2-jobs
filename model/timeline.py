"""Timeline helpers for Phase 3 annual workforce snapshots."""

from __future__ import annotations

from collections import defaultdict

from model.compute import load_archetypes


PHASES = ("construction", "commissioning", "operations")


def _linear_up(year: int, start: int, peak: int) -> float:
    if year < start:
        return 0.0
    if peak <= start:
        return 1.0 if year >= start else 0.0
    if year >= peak:
        return 1.0
    return (year - start) / (peak - start)


def _triangle(year: int, start: int, peak: int, end: int) -> float:
    if year < start or year > end:
        return 0.0
    if peak <= start:
        if end <= peak:
            return 1.0 if year == peak else 0.0
        return (end - year) / (end - peak) if year > peak else 1.0
    if year <= peak:
        return (year - start) / (peak - start)
    if end <= peak:
        return 1.0
    return (end - year) / (end - peak)


def _phase_weight(
    phase: str,
    year: int,
    start_year: int,
    target_year: int,
    construction_years: int,
) -> float:
    construction_start = max(start_year, target_year - max(1, construction_years))
    construction_peak = max(start_year, target_year - 2)
    commissioning_start = max(start_year, target_year - 2)
    commissioning_peak = max(start_year, target_year - 1)
    operations_start = max(start_year, target_year - 1)

    if phase == "construction":
        return max(
            0.0,
            min(
                1.0,
                _triangle(
                    year,
                    construction_start,
                    construction_peak,
                    target_year,
                ),
            ),
        )
    if phase == "commissioning":
        return max(
            0.0,
            min(
                1.0,
                _triangle(
                    year,
                    commissioning_start,
                    commissioning_peak,
                    target_year + 1,
                ),
            ),
        )
    if phase == "operations":
        return max(
            0.0,
            min(1.0, _linear_up(year, operations_start, target_year)),
        )
    return 0.0


def _empty_phase_bucket() -> dict:
    return {phase: 0.0 for phase in PHASES}


def _round_snapshot(snapshot: dict[str, dict[str, float]]) -> dict[str, dict[str, int]]:
    rounded = {}
    for occ_id, phases in snapshot.items():
        rounded_phases = {
            phase: int(round(phases.get(phase, 0.0)))
            for phase in PHASES
        }
        rounded[occ_id] = {
            **rounded_phases,
            "total": sum(rounded_phases.values()),
        }
    return rounded


def compute_timeline(
    demand_records: list[dict],
    start_year: int,
    target_year: int,
    archetypes: list[dict] | None = None,
    end_year: int | None = None,
) -> dict:
    """Generate year-keyed demand snapshots from demand records."""
    if start_year > target_year:
        raise ValueError("start_year must be less than or equal to target_year")

    if archetypes is None:
        archetypes = load_archetypes()
    archetype_lookup = {archetype["id"]: archetype for archetype in archetypes}
    final_year = end_year if end_year is not None else target_year + 5
    years = range(start_year, final_year + 1)
    has_clusters = any("cluster_id" in record for record in demand_records)

    if has_clusters:
        timeline = {str(year): defaultdict(lambda: defaultdict(_empty_phase_bucket)) for year in years}
    else:
        timeline = {str(year): defaultdict(_empty_phase_bucket) for year in years}

    for record in demand_records:
        occupation_id = record.get("occupation_id") or "__unallocated__"
        phase = record.get("phase")
        archetype = archetype_lookup.get(record.get("archetype_id"), {})
        construction_years = int(archetype.get("construction_years", 3))

        for year in years:
            weight = _phase_weight(
                phase,
                year,
                start_year,
                target_year,
                construction_years,
            )
            if weight <= 0:
                continue
            contribution = float(record.get("demand", 0)) * weight
            if has_clusters:
                cluster_id = record["cluster_id"]
                timeline[str(year)][cluster_id][occupation_id][phase] += contribution
            else:
                timeline[str(year)][occupation_id][phase] += contribution

    finalized = {}
    for year in years:
        year_key = str(year)
        if has_clusters:
            finalized[year_key] = {
                cluster_id: _round_snapshot(cluster_snapshot)
                for cluster_id, cluster_snapshot in timeline[year_key].items()
            }
        else:
            finalized[year_key] = _round_snapshot(timeline[year_key])
    return finalized
