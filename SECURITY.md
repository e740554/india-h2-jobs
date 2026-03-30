# Security Policy

## Supported Versions

The latest code on `master` is the supported line.

| Version | Supported |
|---------|-----------|
| `master` | Yes |
| `v1.4.0.0` | Yes |
| `v1.3.0.0` and earlier | No |

Historical tags are kept for reproducibility and release history, not for patch support.

## Reporting A Vulnerability

Please do not open a public GitHub issue for security problems.

Instead, email `740554@gmail.com` with:

- a short description of the issue
- affected file or feature
- impact and likely exploitation path
- reproduction steps or proof of concept, if you have them
- any suggested fix or mitigation

Use the subject line `[india-h2-jobs security]`.

The maintainers will aim to acknowledge reports within 5 business days and will coordinate next
steps privately. Please give us reasonable time to investigate and patch before public disclosure.

## What Belongs Here

Security reports are especially helpful for:

- XSS or script-injection paths in the published atlas
- unsafe handling of remote data or generated HTML/JS
- dependency or supply-chain compromise risks
- leaked credentials, tokens, or secrets
- write paths that could let an attacker replace published content unexpectedly

## What Does Not Need Private Disclosure

These can go through normal public issues:

- data quality mistakes
- incorrect workforce coefficients or scenario assumptions
- missing occupations or pathways
- documentation bugs
- visual/UI defects without a security impact
