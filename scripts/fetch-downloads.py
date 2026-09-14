#!/usr/bin/env python3
"""Download pinned toolchain archives on the microserver, verifying SHA-256."""
import hashlib
import json
import pathlib
import sys
import urllib.request

root = pathlib.Path(sys.argv[1])
lock = json.loads((root / 'versions.lock.json').read_text())
downloads = root / 'downloads'
downloads.mkdir(exist_ok=True)
items = [
    (f"{lock['go']}.linux-amd64.tar.gz", 'https://go.dev/dl/', lock['go_sha256']),
    (f"node-{lock['node']}-linux-x64.tar.xz", f"https://nodejs.org/dist/{lock['node']}/", lock['node_sha256']),
]
for name, base, expected in items:
    target = downloads / name
    if not target.exists() or hashlib.file_digest(target.open('rb'), 'sha256').hexdigest() != expected:
        partial = target.with_suffix(target.suffix + '.part')
        with urllib.request.urlopen(base + name, timeout=120) as src, partial.open('wb') as dst:
            while chunk := src.read(1024 * 1024):
                dst.write(chunk)
        with partial.open('rb') as src:
            assert hashlib.file_digest(src, 'sha256').hexdigest() == expected, name
        partial.replace(target)
    print('Verified', name)
