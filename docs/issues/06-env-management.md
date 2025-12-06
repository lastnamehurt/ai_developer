# feat: centralized env management with masking and validation

## Summary
- Provide `ai env set/get/list/validate` for global and project scopes.
- Mask secrets in output; warn on unused keys.
- Optional: encrypted-at-rest storage for secrets.

## Acceptance Criteria
- Env commands store and merge global + project scopes correctly (project overrides global).
- `ai env list` masks values; `ai env validate` reports missing/unused keys per profile.
- (Optional) Encryption flag stores secrets encrypted; falls back to plaintext if not enabled.

## Tasks
- Implement env store read/write with scope precedence.
- Add CLI commands and masking logic.
- Add validation against profile-declared requirements.
- Explore encryption option (if feasible now; otherwise stub for later).
