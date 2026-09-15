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
  status=$?
  mkdir -p "$artifact_dir"
  cp -a "$root/reports/." "$artifact_dir/" >/dev/null 2>&1 || true
  if "$engine" container inspect "$container" >/dev/null 2>&1; then
    "$engine" logs "$container" >"$artifact_dir/container.log" 2>&1 || true
    "$engine" container inspect "$container" >"$artifact_dir/container-inspect.json" 2>&1 || true
    if (( status != 0 )); then
      echo '::group::Jenkins validation container log'
      "$engine" logs --tail 120 "$container" 2>&1 || true
      echo '::endgroup::'
      log_tail="$("$engine" logs --tail 40 "$container" 2>&1 || true)"
      log_tail="${log_tail//'%'/'%25'}"
      log_tail="${log_tail//$'\r'/'%0D'}"
      log_tail="${log_tail//$'\n'/'%0A'}"
      echo "::error title=Jenkins validation failed::${log_tail}"
    fi
  fi
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
  "JENKINS_VALIDATION_INITIAL_PASSWORD=peter111"
  "JENKINS_VALIDATION_PLUGINS_FILE=$PWD/image/plugins.txt"
  "JENKINS_VALIDATION_REPORTS_DIR=$root/reports"
)

run_validation() {
  local output status output_tail escaped
  set +e
  output="$(env "${validation_env[@]}" python3 -u scripts/verify-on-box.py "$@" 2>&1)"
  status=$?
  set -e
  printf '%s\n' "$output"
  if (( status != 0 )); then
    printf '%s\n' "$output" >"$root/reports/validation-error.log"
    output_tail="${output: -2000}"
    escaped="${output_tail//'%'/'%25'}"
    escaped="${escaped//$'\r'/'%0D'}"
    escaped="${escaped//$'\n'/'%0A'}"
    echo "::error file=scripts/verify-on-box.py,title=Jenkins validation script failed::${escaped}"
  fi
  return "$status"
}

run_validation
"$engine" restart -t 30 "$container" >/dev/null
run_validation --after-restart

echo "Validation reports will be copied to $artifact_dir"
