#!/usr/bin/env bash
set -Eeuo pipefail

image="${1:?usage: ci-validate.sh IMAGE}"
engine="${CONTAINER_ENGINE:-docker}"
run_id="${GITHUB_RUN_ID:-local}"
run_attempt="${GITHUB_RUN_ATTEMPT:-1}"
container="jenkins-lazycat-validation-${run_id}-${run_attempt}"
root="$(mktemp -d)"
artifact_dir="${JENKINS_VALIDATION_ARTIFACT_DIR:-/tmp/jenkins-validation-report}"

cleanup() {
  mkdir -p "$artifact_dir"
  cp -a "$root/reports/." "$artifact_dir/" >/dev/null 2>&1 || true
  "$engine" rm -f -v "$container" >/dev/null 2>&1 || true
  rm -rf "$root"
}
trap cleanup EXIT

mkdir -p "$root/validation/var/jenkins/secrets" "$root/validation/cache" "$root/secrets" "$root/reports"
printf '%s\n' 'peter111' >"$root/validation/var/jenkins/secrets/reset-admin-password"
if command -v sudo >/dev/null 2>&1; then
  sudo chown -R 1000:1000 "$root/validation/var" "$root/validation/cache"
else
  chown -R 1000:1000 "$root/validation/var" "$root/validation/cache"
fi

"$engine" run -d --name "$container" --cpus 2 --memory 3g \
  --publish 127.0.0.1:18080:8080 \
  --mount "type=bind,src=$root/validation/var,dst=/lzcapp/var" \
  --mount "type=bind,src=$root/validation/cache,dst=/lzcapp/cache" \
  --env JENKINS_ADMIN_PASSWORD=peter111 \
  --env JENKINS_URL=http://127.0.0.1:18080/ \
  "$image" >/dev/null

validation_env=(
  "JENKINS_VALIDATION_ROOT=$root"
  "JENKINS_VALIDATION_BASE_URL=http://127.0.0.1:18080"
  "JENKINS_VALIDATION_PLUGINS_FILE=$PWD/image/plugins.txt"
  "JENKINS_VALIDATION_REPORTS_DIR=$root/reports"
)
env "${validation_env[@]}" python3 -u scripts/verify-on-box.py
"$engine" restart -t 30 "$container" >/dev/null
env "${validation_env[@]}" python3 -u scripts/verify-on-box.py --after-restart

echo "Validation reports will be copied to $artifact_dir"
