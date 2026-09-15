ARG PYTHON_BASE_IMAGE=python:3.12-slim-trixie@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea
ARG JENKINS_BASE_IMAGE=jenkins/jenkins:lts-jdk21@sha256:c1e4c349365f6d16d88595b2c5f7e8ff39b8ae1d061f62420bac193b4b9616d0
FROM ${PYTHON_BASE_IMAGE} AS python
FROM ${JENKINS_BASE_IMAGE}
ARG JENKINS_BASE_IMAGE
ARG BUILD_FINGERPRINT=local
LABEL org.opencontainers.image.source="https://github.com/wcaqrl/jenkins" \
      org.opencontainers.image.base.name="${JENKINS_BASE_IMAGE}" \
      peter.lazycat.build-fingerprint="${BUILD_FINGERPRINT}"
USER root
RUN sed -i 's|http://deb.debian.org/debian|https://mirrors.ustc.edu.cn/debian|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    git openssh-client curl ca-certificates xz-utils unzip build-essential pkg-config \
    libbz2-1.0 libffi8 libgdbm6t64 libgdbm-compat4t64 liblzma5 libncursesw6 \
    libreadline8t64 libsqlite3-0 libssl3t64 libuuid1 zlib1g libexpat1 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=python /usr/local/ /usr/local/
RUN ldconfig && python3.12 -c "import ssl, sqlite3, bz2, lzma, ctypes, readline, venv"
COPY downloads/go1.27.1.linux-amd64.tar.gz /tmp/go.tar.gz
COPY downloads/node-v26.8.2-linux-x64.tar.xz /tmp/node.tar.xz
RUN echo "63d339f0da5ab53635a56f2490a7984dfe12dfcff22ad749f63edaf590168445  /tmp/go.tar.gz" | sha256sum -c - \
    && echo "40e1d3225c1c9ae9a2671c98ecb9857e4d5555026394f348645676798840d5c5  /tmp/node.tar.xz" | sha256sum -c - \
    && tar -xzf /tmp/go.tar.gz -C /usr/local \
    && mkdir -p /opt/node \
    && tar -xJf /tmp/node.tar.xz -C /opt/node --strip-components=1 \
    && rm /tmp/go.tar.gz /tmp/node.tar.xz
ENV PATH="/opt/node/bin:/usr/local/go/bin:/usr/local/bin:${PATH}"
RUN npm install --global npm@12.0.2 && npm cache clean --force
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
USER jenkins
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt --latest true
USER root
COPY jenkins.yaml /opt/jenkins-custom/jenkins.yaml
COPY jenkins-bootstrap.yaml /opt/jenkins-custom/jenkins-bootstrap.yaml
COPY entrypoint.sh /usr/local/bin/jenkins-custom-entrypoint
COPY versions.lock.json /opt/jenkins-custom/versions.lock.json
RUN chmod 0755 /usr/local/bin/jenkins-custom-entrypoint
ENV JENKINS_HOME=/lzcapp/var/jenkins \
    JENKINS_JAVA_OPTS="-Djenkins.install.runSetupWizard=false -Xms256m -Xmx1536m" \
    CASC_JENKINS_CONFIG=/opt/jenkins-custom/jenkins.yaml \
    SECRETS=/lzcapp/var/jenkins/secrets \
    GOPATH=/lzcapp/cache/go \
    GOCACHE=/lzcapp/cache/go-build \
    npm_config_cache=/lzcapp/cache/npm \
    PIP_CACHE_DIR=/lzcapp/cache/pip \
    TZ=Asia/Shanghai
USER jenkins
ENTRYPOINT ["/usr/local/bin/jenkins-custom-entrypoint"]
