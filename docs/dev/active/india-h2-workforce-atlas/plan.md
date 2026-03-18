---
title: India H2 Workforce Atlas — Implementation Plan
status: active
created: 2026-03-18
spec: docs/superpowers/specs/2026-03-18-india-h2-workforce-atlas-design.md
---

# Implementation Plan

## Critical Path

- **NGHM-presentable demo:** Sprints 0–3 (~4.5 weeks)
- **Full production:** Sprints 0–5 (~7 weeks)
- Pace: 15–20 focused hours/week

## Sprints

| Sprint | Duration | What Ships |
|--------|----------|------------|
| **0** | 3–4 days | Repo scaffold, data recon |
| **1** | 1.5 weeks | 500+ occupations in CSV |
| **2** | 1 week | Scored dataset (scores.json) |
| **3** | 1.5 weeks | **NGHM-presentable demo** |
| **4** | 1 week | 3,000+ occupations, GitHub Pages |
| **5** | 1.5 weeks | hygoat.in live, mobile, partners |

## Key Decision: Claude Code for Scoring

Scoring uses Claude Code subagents instead of Anthropic API. No API key needed.
- Dev: Claude Code runs scoring interactively
- CI (future): Can add API option when GitHub Actions pipeline exists
- Cost: $0 (included in Claude Code subscription)
