# Contributing

This repository is the canonical source for MELSEC SLMP profile data.

## Add Or Change A Profile

1. Add or update evidence under `evidence/`.
2. Update the editable source:
   - capability profiles: `evidence/profile-definitions/*.md`
   - device ranges: `device-ranges/slmp_device_range_rules.md`
3. Run:

   ```powershell
   python tools/generate_capability_profiles.py
   python tools/generate_device_range_rules.py
   python tools/generate_profile_tables.py
   python tools/validate_profiles.py
   ```

4. Create a new tag for the data update, then update downstream fixture sync
   scripts to that tag in the same release wave.

Do not move or replace a published tag. Field additions are compatible and keep
`schema_version` unchanged. Rename, remove, or semantic changes require a
schema version increment.

## Evidence Rules

Live PLC checks must follow the workspace live-communication rules. Profile
definition notes are decision records, not communication logs.

Keep user-facing library docs predictable. Shared setup, troubleshooting,
range tables, and common protocol notes belong in `plc-comm-docs-site`; this
repository owns canonical data, evidence, and generated comparison tables.

