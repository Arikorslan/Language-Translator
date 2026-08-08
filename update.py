from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from packaging.version import InvalidVersion, Version


DEFAULT_TIMEOUT = 20


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    download_url: str
    size: int


@dataclass(frozen=True)
class ReleaseInfo:
    tag: str
    version: Version
    name: str
    body: str
    published_at: str
    html_url: str
    assets: list[ReleaseAsset]


class UpdateError(RuntimeError):
    pass


class GitHubUpdater:
    def __init__(self, repo: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        if "/" not in repo:
            raise ValueError("repo must be in the format 'owner/repo'")
        self.repo = repo
        self.timeout = timeout

    def _release_url(self) -> str:
        return f"https://api.github.com/repos/{self.repo}/releases/latest"

    @staticmethod
    def _normalize_tag(tag: str) -> str:
        return tag.strip().lstrip("vV")

    def fetch_latest_release(self) -> ReleaseInfo:
        try:
            response = requests.get(
                self._release_url(),
                headers={"Accept": "application/vnd.github+json"},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise UpdateError("Unable to contact GitHub Releases API.") from exc

        data = response.json()
        raw_tag = str(data.get("tag_name") or "").strip()
        if not raw_tag:
            raise UpdateError("Latest release does not include a tag_name.")

        try:
            parsed_version = Version(self._normalize_tag(raw_tag))
        except InvalidVersion as exc:
            raise UpdateError(f"Invalid release tag format: {raw_tag}") from exc

        assets: list[ReleaseAsset] = []
        for item in data.get("assets", []):
            url = str(item.get("browser_download_url") or "")
            name = str(item.get("name") or "")
            if not url or not name:
                continue
            assets.append(
                ReleaseAsset(
                    name=name,
                    download_url=url,
                    size=int(item.get("size") or 0),
                )
            )

        return ReleaseInfo(
            tag=raw_tag,
            version=parsed_version,
            name=str(data.get("name") or raw_tag),
            body=str(data.get("body") or ""),
            published_at=str(data.get("published_at") or ""),
            html_url=str(data.get("html_url") or ""),
            assets=assets,
        )

    def check_for_update(self, current_version: str) -> tuple[bool, ReleaseInfo]:
        try:
            current = Version(self._normalize_tag(current_version))
        except InvalidVersion as exc:
            raise UpdateError(f"Invalid current version: {current_version}") from exc

        latest = self.fetch_latest_release()
        return latest.version > current, latest

    def download_asset(self, asset: ReleaseAsset, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)

        try:
            with requests.get(asset.download_url, stream=True, timeout=self.timeout) as response:
                response.raise_for_status()
                with open(destination, "wb") as handle:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            handle.write(chunk)
        except requests.RequestException as exc:
            raise UpdateError(f"Failed to download update asset: {asset.name}") from exc

        return destination


def _select_default_asset(release: ReleaseInfo) -> ReleaseAsset | None:
    if not release.assets:
        return None

    preferred_suffixes = (".exe", ".msi", ".zip")
    for suffix in preferred_suffixes:
        for asset in release.assets:
            if asset.name.lower().endswith(suffix):
                return asset

    return release.assets[0]


def _run_cli(args: Any) -> int:
    updater = GitHubUpdater(args.repo)
    has_update, release = updater.check_for_update(args.current_version)

    if not has_update:
        print(f"No update available. Current version is {args.current_version}.")
        return 0

    print(f"Update available: {release.tag}")
    print(f"Release: {release.name}")

    if not args.download:
        return 0

    asset = _select_default_asset(release)
    if asset is None:
        raise UpdateError("No downloadable asset found in the latest release.")

    if args.output:
        out_path = Path(args.output)
        if out_path.is_dir():
            out_path = out_path / asset.name
    else:
        out_path = Path.cwd() / asset.name

    updater.download_asset(asset, out_path)
    print(f"Downloaded {asset.name} to {out_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check and download app updates from GitHub Releases")
    parser.add_argument("--repo", required=True, help="GitHub repository in owner/repo format")
    parser.add_argument("--current-version", required=True, help="Current app version, e.g. 1.2.0")
    parser.add_argument("--download", action="store_true", help="Download the latest release asset")
    parser.add_argument(
        "--output",
        default="",
        help="Optional destination file or directory for the downloaded asset",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        return _run_cli(args)
    except UpdateError as exc:
        print(f"Update failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
