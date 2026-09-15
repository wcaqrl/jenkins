# Jenkins LTS 自动构建与懒猫商店发布

## 流程

1. `Build Jenkins custom image` 每 6 小时读取官方 `jenkins/jenkins:lts-jdk21` 的 amd64 摘要。
2. 摘要或本仓库镜像配置变化时，更新 `image/Dockerfile` 与 `image/versions.lock.json`，下载并校验固定版本的 Go、Node.js 包，然后构建定制镜像。
3. `scripts/ci-validate.sh` 启动隔离实例，检查 Jenkins、插件、深色主题、Python、Git、Go、Node.js、npm、Pipeline、管理员改密和重启持久化。只有全部通过才推送到 `ghcr.io/wcaqrl/jenkins-lazycat:lts-jdk21`。
4. 镜像工作流成功后以 `workflow_run` 启动 `Publish LazyCat Jenkins`，再调用 `ca-x/lazycat-github-action`。Action 按 amd64 digest 判断变化，通过开发者平台 `copy-image` 将定制镜像转存到 `registry.lazycat.cloud/peter/`，把应用 patch 版本递增，修改 `lzc-manifest.yml` 和 `package.yml`，构建及官方 lint LPK，创建 GitHub Release，再上传 LPK 并创建审核。
5. 同一 digest 重复执行不会增加版本；已有 Release、商店版本或审核中的版本会被识别，流水线可用于恢复中断的发布。

`lazycat-github-action` 的镜像交付发生在 LPK buildscript 之前，所以定制 Jenkins 镜像必须由第一条 workflow 先构建，不能直接把 `jenkins/jenkins` 配成 LPK 的运行镜像。

## 一次性设置

1. 在 GitHub 仓库 Settings → Actions → General 中允许 Actions 创建提交和 Release（Workflow permissions 选择 Read and write permissions）。
2. 第一次手动运行 `Build Jenkins custom image`。GHCR 包创建后，在包设置中把 `wcaqrl/jenkins-lazycat` 的可见性改成 Public。懒猫服务端的 copy-image 没有源仓库凭据参数，因此它必须能匿名拉取这个中转镜像。
3. 在仓库 Settings → Secrets and variables → Actions 中创建 Secret `LZC_API_TOKEN`，内容为懒猫开发者 PAT。PAT 需要 `developer.app.manage` 权限。不要把 PAT 写进 workflow、配置文件或日志。
4. 手动运行 `Publish LazyCat Jenkins` 完成第一次转存和发布。此后定时任务自动工作。

生产 PAT 默认请求 `https://appstore.api.lazycat.cloud/sdk/v3/developer`，认证头为 `X-API-Token`。转存使用：

```text
GET /sdk/v3/developer/app/docker/image/push/v3/copy?image=<源镜像>&platform=amd64
GET /sdk/v3/developer/app/docker/image/push/v3/progress?image=<源镜像>&platform=amd64
```

随后使用 LPK 上传和审核接口：

```text
POST /sdk/v3/developer/app/lpk/upload
POST /sdk/v3/developer/app/peter.lazycat.app.jenkins/review/create
```

## 安全边界

- 定制镜像中转使用 GHCR 的公开只读镜像；写入由仓库自带的短期 `GITHUB_TOKEN` 完成。
- 懒猫 PAT 只保存为 GitHub Secret，并只映射给发布 job。
- LPK 运行时只引用 copy-image 返回的 `registry.lazycat.cloud/peter/...` 地址。
- 构建或验证失败时不会推送新标签，也不会生成 LPK 或提交审核。
