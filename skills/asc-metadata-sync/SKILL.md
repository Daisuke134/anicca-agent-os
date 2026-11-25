---
name: asc-metadata-sync
description: Sync and validate App Store metadata and localizations with asc, including legacy metadata format migration. Use when updating metadata or translations.
---

# asc metadata sync

Use this skill to keep local metadata in sync with App Store Connect.

## Two Types of Localizations

### 1. Version Localizations (per-release)
Fields: `description`, `keywords`, `whatsNew`, `supportUrl`, `marketingUrl`, `promotionalText`

```bash
# List version localizations
asc localizations list --version "VERSION_ID"

# Download
asc localizations download --version "VERSION_ID" --path "./localizations"

# Upload from .strings files
asc localizations upload --version "VERSION_ID" --path "./localizations"
```

### 2. App Info Localizations (app-level)
Fields: `name`, `subtitle`, `privacyPolicyUrl`, `privacyChoicesUrl`, `privacyPolicyText`

```bash
# First, find the app info ID
asc app-infos list --app "APP_ID"

# List app info localizations
asc localizations list --app "APP_ID" --type app-info --app-info "APP_INFO_ID"

# Upload app info localizations
asc localizations upload --app "APP_ID" --type app-info --app-info "APP_INFO_ID" --path "./app-info-localizations"
```

**Note:** If you get "multiple app infos found", you must specify `--app-info` with the correct ID.

## Legacy Metadata Format Workflow

### Export current state
```bash
asc migrate export --app "APP_ID" --output "./metadata"
```

### Validate local files
```bash
# Use --help to discover flags for your metadata directory
asc migrate validate --help
```
This checks character limits and required fields.

### Import updates
```bash
# Use --help to discover flags for your metadata directory
asc migrate import --help
```

## Quick Field Updates

### Version-specific fields
```bash
# What's New
asc app-info set --app "APP_ID" --locale "en-US" --whats-new "Bug fixes and improvements"

# Description
asc app-info set --app "APP_ID" --locale "en-US" --description "Your app description here"

# Keywords
asc app-info set --app "APP_ID" --locale "en-US" --keywords "keyword1,keyword2,keyword3"

# Support URL
asc app-info set --app "APP_ID" --locale "en-US" --support-url "https://support.example.com"
```

### Version metadata
```bash
# Copyright
asc versions update --version-id "VERSION_ID" --copyright "2026 Your Company"

# Release type
asc versions update --version-id "VERSION_ID" --release-type AFTER_APPROVAL
```

### TestFlight notes
```bash
asc build-localizations create --build "BUILD_ID" --locale "en-US" --whats-new "TestFlight notes here"
```

## .strings File Format

For bulk updates, use .strings files:

```
// en-US.strings
"description" = "Your app description";
"keywords" = "keyword1,keyword2,keyword3";
"whatsNew" = "What's new in this version";
"supportUrl" = "https://support.example.com";
```

For app-info type:
```
// en-US.strings (app-info type)
"privacyPolicyUrl" = "https://example.com/privacy";
"name" = "Your App Name";
"subtitle" = "Your subtitle";
```

## Multi-Language Workflow

1. Export all localizations:
```bash
asc localizations download --version "VERSION_ID" --path "./localizations"
```

2. Translate the .strings files (or use translation service)

3. Upload all at once:
```bash
asc localizations upload --version "VERSION_ID" --path "./localizations"
```

4. Verify:
```bash
asc localizations list --version "VERSION_ID" --output table
```

## Character Limits

| Field | Limit |
|-------|-------|
| Name | 30 |
| Subtitle | 30 |
| Keywords | 100 (comma-separated) |
| Description | 4000 |
| What's New | 4000 |
| Promotional Text | 170 |

Use `asc migrate validate` to check limits before upload.

## Notes
- Version localizations and app info localizations are different; use the right command and `--type` flag.
- `asc migrate validate` enforces character limits before upload.
- Use `asc localizations list` to confirm available locales and IDs.
- Privacy Policy URL is in app info localizations, not version localizations.

## Verification (mandatory, added 2026-11-17)

A metadata sync under this skill is verified against App Store Connect's own state, not against the local files. Structure follows the house verification block (invariants / grader / E2E / oracle).

1. **Invariants.** (a) Version localizations and app info localizations are never mixed: the command, the `--type` flag, and the app / version / app-info IDs all match the field being changed. (b) `asc migrate validate` passes before any upload — character limits hold (name 30, subtitle 30, keywords 100, description 4000, whatsNew 4000, promotionalText 170) and no required field is empty. (c) After upload, every locale — including locales that were not supposed to change — matches the intended content field by field when re-listed from the server.
2. **Grader.** A separate pass re-downloads the localizations (`asc localizations download`) and diffs them against the intended .strings files. The uploading command's success output is not the grade.
3. **E2E evidence.** The `asc localizations list` output is read in full for every locale after the sync, and the changed fields are read back from App Store Connect itself — the local .strings files are the input, never the evidence.
4. **Differential oracle.** The pre-sync export (`asc migrate export`) is the baseline. Any field that differs from the baseline without being in the intended change set is a defect, including silent changes in untouched locales.
5. **Repeat failures.** A second wrong-type upload (version vs app-info) or a second collateral overwrite becomes a pre-upload checklist gate naming the exact IDs, written into the sync runbook the same day.
