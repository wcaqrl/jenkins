#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
target="${JENKINS_BUILD_HOST:-root@peterlc.heiyu.space}"
local_image='peter/jenkins-custom:2.568.3-3'
push_image='registry.corp.lazycat.cloud/peterlc/jenkins-custom:2.568.3-3'
mux_dir=$(mktemp -d)
cleanup() {
  ssh -S "$mux_dir/control" -O exit "$target" >/dev/null 2>&1 || true
  rm -rf "$mux_dir"
}
trap cleanup EXIT
ssh -M -S "$mux_dir/control" -o ControlPersist=10m -fnN "$target"
remote() { ssh -S "$mux_dir/control" "$target" "$@"; }
remote 'mkdir -p /lzcsys/var/jenkins-custom/build /lzcsys/var/jenkins-custom/scripts /lzcsys/var/jenkins-custom/reports'
tar -C image --exclude=downloads -cf - . | remote 'tar -xf - -C /lzcsys/var/jenkins-custom/build'
tar -C scripts -cf - fetch-downloads.py remote-validate.sh verify-on-box.py |
  remote 'tar -xf - -C /lzcsys/var/jenkins-custom/scripts'
remote 'python3 /lzcsys/var/jenkins-custom/scripts/fetch-downloads.py /lzcsys/var/jenkins-custom/build'
remote "cd /lzcsys/var/jenkins-custom/build && DOCKER_BUILDKIT=0 lzc-docker build --network host --cpuset-cpus 0-3 --memory 4g -t $local_image ."
remote "sh /lzcsys/var/jenkins-custom/scripts/remote-validate.sh $local_image"
# 使用微服 root 用户已有的企业仓库登录凭据。
remote "lzc-docker tag $local_image $push_image && lzc-docker push $push_image"
echo "镜像构建、验证和推送完成：$push_image"
echo '下一步调用应用商店 copy-image，取得 registry.lazycat.cloud 地址后更新 lzc-manifest.yml，再运行 lzc-cli project build。'
