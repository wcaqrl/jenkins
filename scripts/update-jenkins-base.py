#!/usr/bin/env python3
"""Update the pinned Jenkins base image and its audit metadata."""

import argparse
import datetime
import json
import pathlib
import re


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--jenkins-version", required=True)
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    if not re.fullmatch(r"jenkins/jenkins:lts-jdk21@sha256:[0-9a-f]{64}", args.base_ref):
        raise SystemExit(f"unexpected Jenkins base reference: {args.base_ref}")
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,2}", args.jenkins_version):
        raise SystemExit(f"unexpected Jenkins version: {args.jenkins_version}")

    dockerfile = args.root / "image" / "Dockerfile"
    source = dockerfile.read_text()
    updated, count = re.subn(
        r"^ARG JENKINS_BASE_IMAGE=.*$",
        f"ARG JENKINS_BASE_IMAGE={args.base_ref}",
        source,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise SystemExit("Dockerfile must contain exactly one JENKINS_BASE_IMAGE argument")
    dockerfile.write_text(updated)

    lockfile = args.root / "image" / "versions.lock.json"
    lock = json.loads(lockfile.read_text())
    base_changed = lock.get("jenkins") != args.jenkins_version or lock.get("base_image") != args.base_ref
    lock["jenkins"] = args.jenkins_version
    lock["base_image"] = args.base_ref
    if base_changed:
        lock["checked_on"] = datetime.date.today().isoformat()
    lockfile.write_text(json.dumps(lock, indent=2) + "\n")


if __name__ == "__main__":
    main()
