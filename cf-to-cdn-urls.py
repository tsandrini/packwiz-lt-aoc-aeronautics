#!/usr/bin/env python3
"""
Rewrite each `mods/*.pw.toml` from `mode = "metadata:curseforge"` to a direct
`url = "..."` pointing at CurseForge's mediafilez CDN.

Background: nix-minecraft's `pkgs.fetchPackwizModpack` runs packwiz-installer
in a FOD sandbox. For mods whose authors set "third-party downloads disabled"
on CurseForge, packwiz-installer fails because the CF API refuses to give it a
download URL. The same files ARE accessible via the public CDN — they're just
gated behind knowing the URL pattern. This script computes the URL from each
.pw.toml's stored `file-id` + `filename` and substitutes it in.

Run this after every `packwiz cf add ...` / `packwiz update ...` invocation
that touches a CurseForge entry. Modrinth entries (which use `[update.modrinth]`)
are not affected and are skipped.

URL formula:
    https://mediafilez.forgecdn.net/files/<file-id // 1000>/<file-id % 1000>/<URL-encoded filename>

Usage:
    python3 cf-to-cdn-urls.py          # operates on ./mods
    python3 cf-to-cdn-urls.py <dir>    # operates on a custom mods dir
"""
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "mods")

re_filename = re.compile(r'^filename = "(.+)"$', re.M)
re_fileid = re.compile(r'^file-id = (\d+)$', re.M)
re_mode = re.compile(r'^mode = "metadata:curseforge"$', re.M)

rewritten = 0
skipped = 0

for path in sorted(ROOT.glob("*.pw.toml")):
    text = path.read_text()
    if not re_mode.search(text):
        skipped += 1
        continue
    fn = re_filename.search(text)
    fid = re_fileid.search(text)
    if not (fn and fid):
        print(f"  SKIP (no filename/file-id): {path}", file=sys.stderr)
        skipped += 1
        continue
    filename = fn.group(1)
    file_id = int(fid.group(1))
    chunk1 = file_id // 1000
    chunk2 = file_id % 1000
    encoded = urllib.parse.quote(filename)
    url = f"https://mediafilez.forgecdn.net/files/{chunk1}/{chunk2}/{encoded}"

    new_text = re_mode.sub(f'url = "{url}"', text, count=1)
    path.write_text(new_text)
    rewritten += 1

print(f"rewritten={rewritten} skipped={skipped}")
