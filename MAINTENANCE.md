# LANG-TRANS Maintenance Guide

This document is the operational and maintenance reference for LANG-TRANS.
It is based on the current code in this repository.

## 1. Current Project Snapshot

- App type: desktop translator (PyQt6).
- Main entrypoint: `Translator.py`.
- Runtime capabilities:
  - text translation (googletrans)
  - source language auto-detect
  - speech-to-text input
  - text-to-speech output
  - optional saved audio files
  - in-app update checks and release-asset download from GitHub Releases

Known current version constant:
- `APP_VERSION = "1.0.0"`

## 2. Directory and Module Ownership

- `Translator.py`
  - UI composition, user workflows, settings persistence, update UX, application lifecycle.
- `backend/translate.py`
  - Translation wrapper around `googletrans.Translator`.
- `backend/voiceInput.py`
  - Speech recognition wrapper (microphone capture + recognition).
- `backend/voiceOutput.py`
  - gTTS generation and pygame playback for spoken output and saved output.
- `update.py`
  - GitHub Releases API integration, semantic version comparison, asset download.
- `assets/xtract.py`
  - Extracts icon/image binary resources to user Pictures folder and removes them on exit.
- `build_windows.ps1`
  - Windows packaging automation (PyInstaller one-file build).

## 3. Runtime Data and Persistence

### Settings Storage

- File location: `~/.lang-trans/settings.json`
- Currently persisted keys:
  - `github_repo`
  - `auto_check_updates`

Settings behavior:
- On startup, app loads defaults and overlays any saved JSON values.
- Save action validates repository format (`owner/repo`) unless left as placeholder.
- Reset action returns to default fallback values and persists them.

### Audio File Storage

- Base path: `~/LANGUAGE_TRANSLATOR_AUDIOS`
- App scans recursively for `.mp3` files for the "Saved Audio Files" tab.
- Saved file playback uses pygame mixer.

## 4. Startup and Shutdown Lifecycle

Startup sequence (simplified):
1. Extract runtime image/icon assets.
2. Initialize Qt app/window and services.
3. Build UI, populate language options, refresh audio list.
4. Trigger delayed auto-update check (if enabled and repo is configured).

Shutdown sequence:
1. Stop active update worker thread safely.
2. Stop active voice worker thread safely.
3. Attempt cleanup of extracted asset files.

## 5. Update System Maintenance

In-app update flow:
1. App reads configured `github_repo`.
2. Calls GitHub latest release API through `update.py` helper classes.
3. Compares normalized semantic versions.
4. If newer release exists, prompts user.
5. User chooses save location for release asset download.

Release asset selection preference:
- `.exe`, then `.msi`, then `.zip`, then first available asset.

### Release Requirements for Healthy Updates

Maintainers should ensure:
- release tags use semantic-compatible format (examples: `v10.7.0`, `10.7.0`)
- at least one downloadable asset is attached
- Windows executable assets are clearly named

## 6. Build and Packaging Maintenance

Primary build script:
- `build_windows.ps1`

What it does:
1. resolves Python interpreter (prefers workspace venv when present)
2. upgrades pip
3. installs dependencies from `requirements.txt`
4. builds `dist/LANG-TRANS.exe` using PyInstaller

Current build command pattern:
- one-file, windowed executable
- icon set to `Arabic.ico`
- bundles `assets` data directory

## 7. Immediate Maintenance Risks (High Priority)

### Risk A: Dependency File Merge Conflict

File impacted:
- `requirements.txt`

Current problem:
- unresolved conflict markers exist (`<<<<<<<`, `=======`, `>>>>>>>`)

Impact:
- dependency installation may fail or become inconsistent
- CI/CD or local reproducible setup is blocked/unreliable

Required action:
- resolve and commit a single canonical dependency list
- remove conflict markers completely
- verify with clean install and smoke run

### Risk B: Documentation Drift on CI Workflow

Current drift:
- `README.md` mentions `.github/workflows/windows-release.yml`
- workflow file is not present in this repository snapshot

Impact:
- contributor confusion about automated release process

Required action:
- either add the workflow file or update README to reflect manual-only release

### Risk C: Encoding Artifact in Copyright String

File impacted:
- `Translator.py`

Current problem:
- copyright constant appears as `Copyright Â© Ariko 2026`

Impact:
- UI polish/regression in visible branding text

Required action:
- normalize source encoding to UTF-8 and fix the literal string

## 8. Preventive Maintenance Checklist

Run this checklist before each release:

1. Dependency integrity
   - `requirements.txt` has no conflict markers.
   - clean virtual environment install succeeds.
2. Syntax and import sanity
   - `python -m py_compile Translator.py update.py`
3. App smoke test
   - launch app
   - run translation
   - run voice input (if microphone available)
   - run text-to-speech
   - save/delete/play one audio file
4. Update flow test
   - set a real test repo in settings
   - run "Check Updates"
   - verify no-update and update-available flows
5. Build test
   - execute `build_windows.ps1`
   - confirm `dist/LANG-TRANS.exe` launches
6. Documentation sync
   - ensure README matches current behavior and repo contents

## 9. Troubleshooting Runbook

### App fails to translate
- Check internet connectivity.
- Confirm `googletrans` package installed.
- Validate source/target language codes are populated.

### Voice input fails
- Confirm microphone permissions and availability.
- Check `SpeechRecognition` and `PyAudio` installation status.
- Verify no device-lock conflicts from other apps.

### No audio playback
- Confirm `pygame` mixer can initialize.
- Validate generated `.mp3` is created under audio root.
- Test with another output language if a language TTS model is unsupported.

### Update check fails
- Confirm repository setting is valid (`owner/repo`).
- Check network access to `api.github.com`.
- Validate release tag formatting in GitHub releases.

### Build script errors
- Confirm active interpreter resolves correctly.
- Confirm `pyinstaller` and dependencies install successfully.
- Confirm `Arabic.ico` and `assets` folder exist.

## 10. Recommended Backlog (Next Improvements)

1. Resolve `requirements.txt` and lock dependency strategy.
2. Add automated CI workflow for lint/build artifacts (or remove references).
3. Add structured logging instead of print-based exception reporting.
4. Add unit tests for `update.py` version/asset selection logic.
5. Add a lightweight smoke-test script for release gating.
6. Harden path handling in backend modules to be fully cross-platform.

## 11. Suggested Ownership Boundaries

- UI + settings + UX: `Translator.py`
- update transport and version logic: `update.py`
- translation provider abstraction: `backend/translate.py`
- speech input/output providers: `backend/voiceInput.py`, `backend/voiceOutput.py`
- packaged assets extraction lifecycle: `assets/xtract.py`
- distribution automation: `build_windows.ps1`

Keeping these boundaries stable reduces regressions and allows isolated refactoring.