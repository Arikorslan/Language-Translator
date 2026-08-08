# LANG-TRANS-CODEBASE

A desktop language translator app migrated to PyQt6.

## Features
- Text translation with optional auto-detect source language
- Voice input (speech-to-text)
- Text-to-speech output
- Optional saved audio output (`.mp3`)
- Saved audio browser (play/delete)
- Light/Dark theme switch
- In-app update check and download via GitHub Releases

## Run Locally
1. Create and activate your Python environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Start the app:

```powershell
python Translator.py
```

## Configure In-App Updates
The app checks GitHub Releases using `update.py`.

Recommended:
1. Open the **Settings** tab in the app.
2. Set repository as `owner/repo`.
3. Enable or disable auto-check on startup.
4. Click **Save Settings**.

Optional environment fallback (used if local settings are not set):

```powershell
$env:LANG_TRANS_GITHUB_REPO = "owner/repo"
python Translator.py
```

Example:

```powershell
$env:LANG_TRANS_GITHUB_REPO = "your-org/LANG-TRANS-CODEBASE"
python Translator.py
```

When a newer release exists, the app prompts you and can download the asset directly to a location you choose.

Settings are stored at:
- `~/.lang-trans/settings.json`

## Build Windows EXE
Use the included build script:

```powershell
./build_windows.ps1
```

Output binary:
- `dist/LANG-TRANS.exe`

## GitHub Actions Release Build
Workflow file:
- `.github/workflows/windows-release.yml`

Behavior:
- Builds on manual run (`workflow_dispatch`) and version tags (`v*`).
- Uploads `dist/LANG-TRANS.exe` as an artifact.
- On tag builds, attaches the EXE to the GitHub Release.

## Standalone Update Script
`update.py` supports manual checks and downloads:

```powershell
python update.py --repo owner/repo --current-version 10.6.0
python update.py --repo owner/repo --current-version 10.6.0 --download --output C:\Users\YourName\Downloads
```

## Notes
- Set a real GitHub repo for update checks. The default `owner/repo` is a placeholder.
- Release tags should be semantic-style tags (`v10.7.0` or `10.7.0`) for version comparison.
