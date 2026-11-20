# Portfolio style standard

Target look: one developer, calm and concrete. Behavior stays the same; style aligns.

## Layout

```
backend/           # FastAPI + worker
frontend/          # React dashboard
packages/          # SDK + CLI
Makefile           # run test lint fmt (+ compose helpers)
.env.example
Dockerfile(s)      # multi-stage, non-root where practical
README.md
```

## Python

- Version: **3.12**
- Tooling: **ruff**
- Config: **pydantic-settings**
- Comments: English only, explain *why*

## README

One sentence · screenshot · 4–6 capabilities · mermaid · stack · run · config table.

## Commits

Conventional Commits, English, short. Sole human author.
