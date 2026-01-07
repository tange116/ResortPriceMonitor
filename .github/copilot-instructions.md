<!-- Copilot instructions for AI coding agents
     Generated: 2026-01-03
     NOTE: This repository had no discoverable README or manifest files
           when this file was created. Update the "Project specifics"
           section below after you inspect the repo. -->

# Copilot instructions — Project onboarding

Purpose
- Help an AI agent become productive quickly in this repository by
  documenting discovery steps, project-specific patterns, and merge
  guidance. Update the "Project specifics" section with concrete
  references after inspecting repo files.

Quick discovery checklist (first actions)
- Look for language manifests: `package.json`, `pyproject.toml`,
  `requirements.txt`, `go.mod`, `Cargo.toml`. Example:
  `git ls-files | grep -E "package.json|pyproject.toml|requirements.txt|go.mod|Cargo.toml|Pipfile"`
- Locate entrypoints: search for `main()` or `cmd/`, `src/`, `app/`:
  `git grep -n "def main\(|func main\(|if __name__ == \"__main__\"" || true`
- Find Docker/infra files: `Dockerfile`, `docker-compose.yml`, `Makefile`, `k8s/`.

How to infer build & test commands
- If `package.json` present: prefer `npm ci` then `npm test` or `pnpm install && pnpm test`.
- If `pyproject.toml` or `requirements.txt`: use a venv, `pip install -r requirements.txt` or `pip install -e .` then `pytest`.
- If `go.mod`: `go test ./...` and `go build ./...`.
- If none exist: run `git ls-files` and inspect the top-level folders; ask a human for the preferred workflow.

Project-specific patterns to look for
- Config: check for `.env`, `config/`, or `configs/ and any `Config` structs/classes.
- Services: multi-service layout usually under `services/`, `cmd/`, or `microservices/`.
- Data flows: search for database clients (e.g., `pg`, `sqlalchemy`, `database/sql`) and API clients (`axios`, `requests`, `fetch`).
- Background jobs: look for queue libraries (`celery`, `bull`, `sidekiq`, `rabbitmq`).

Merge & editing guidance for AI agents
- If `.github/copilot-instructions.md` already exists, preserve non-generated sections.
- Keep changes minimal and concentrated: update the "Project specifics" and add examples.
- When adding commands, verify they exist in `package.json`/`Makefile` before suggesting.

Project specifics (edit after repo scan)
- Primary language: **UNKNOWN** — update with `JavaScript/TypeScript`, `Python`, `Go`, etc.
- Primary entrypoint(s): **UNKNOWN** — replace with actual files (e.g., `cmd/server/main.go`, `src/app.py`).
- Test command: **UNKNOWN** — update with `npm test` / `pytest` / `go test ./...`.

Examples (how to reference code while coding)
- To change API handler, open the main router file (likely in `src/` or `cmd/`) and update the route there.
- To add a dependency, modify `package.json` or `pyproject.toml` and run the project's preferred install command.

Questions for a human maintainer
- What is the single command to run the app locally?
- Where are integration tests and how are they run?
- Any non-obvious environment variables or secrets required for local runs?

If you want, I can now scan the repository for manifests and update the "Project specifics" section automatically — say "Scan now".

- when using agent mode, please follow these instructions closely to ensure a smooth onboarding process.
- always use the free or low cost tools and services unless explicitly instructed otherwise
- when there is a premium request please notify the user before proceeding
