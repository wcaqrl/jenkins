#!/bin/sh
set -eu
cd /lzcsys/var/jenkins-custom
image="${1:-peter/jenkins-custom:2.568.3-3}"
python3 - <<'PY'
import os,pathlib
root=pathlib.Path('/lzcsys/var/jenkins-custom')
for p in [root/'validation/var',root/'validation/cache']:
    p.mkdir(parents=True,exist_ok=True)
    os.chown(p,1000,1000)
(root/'secrets').mkdir(mode=0o700,exist_ok=True)
p=root/'secrets/admin-password'
p.write_text('peter111\n')
os.chmod(p,0o600)
os.chown(p,1000,1000)
reset=root/'validation/var/jenkins/secrets/reset-admin-password'
reset.parent.mkdir(parents=True,exist_ok=True)
reset.write_text('peter111\n')
os.chmod(reset,0o600)
os.chown(reset,1000,1000)
PY
if lzc-docker container inspect peter-jenkins-validation >/dev/null 2>&1; then
  lzc-docker stop -t 30 peter-jenkins-validation >/dev/null
  lzc-docker rm -v peter-jenkins-validation >/dev/null
fi
# 只更新独立验证实例的配置模板，不触碰正式应用的数据。
if [ -d validation/var/jenkins/casc ]; then
  cp build/jenkins.yaml validation/var/jenkins/casc/jenkins.yaml
  chown 1000:1000 validation/var/jenkins/casc/jenkins.yaml
fi
lzc-docker run -d --name peter-jenkins-validation --cpus 2 --memory 3g \
  --network host \
  --mount type=bind,src=/etc/resolv.conf,dst=/etc/resolv.conf,readonly \
  --mount type=bind,src=/lzcsys/var/jenkins-custom/validation/var,dst=/lzcapp/var \
  --mount type=bind,src=/lzcsys/var/jenkins-custom/validation/cache,dst=/lzcapp/cache \
  -e "JENKINS_ADMIN_PASSWORD=$(cat /lzcsys/var/jenkins-custom/secrets/admin-password)" \
  -e JENKINS_URL=http://127.0.0.1:18080/ \
  -e 'JENKINS_OPTS=--httpListenAddress=127.0.0.1 --httpPort=18080' \
  "$image"
python3 -u scripts/verify-on-box.py
lzc-docker restart -t 30 peter-jenkins-validation >/dev/null
python3 -u scripts/verify-on-box.py --after-restart
# 留下数据和容器以便复查；停止验证容器释放内存。
lzc-docker stop -t 30 peter-jenkins-validation >/dev/null
