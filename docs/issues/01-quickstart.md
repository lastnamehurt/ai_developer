# feat: ai quickstart project detection and setup

## Summary
- Detect project stack (package.json, requirements.txt, docker-compose, etc.).
- Recommend a profile (web/qa/infra or closest match) with rationale.
- Interactive apply to generate/update `.aidev/` and profile selection; rerunnable safely.

## Acceptance Criteria
- Running `ai quickstart` on sample JS and Python projects completes end-to-end without errors.
- Outputs detected stack and chosen profile with a brief justification.
- Regenerating on an already-initialized project is idempotent (no duplicate files; preserves existing profile unless user changes).

## Tasks
- Implement stack detectors (JS/TS, Python, Docker/K8s hints) with confidence scoring.
- Map detection results to profile recommendations.
- Add interactive prompt to accept/reject recommendation or choose custom.
- Wire quickstart to `ConfigManager.init_project` and profile selection.
- Add tests for detector logic and end-to-end quickstart happy path.
