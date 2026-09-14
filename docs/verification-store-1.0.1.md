# Jenkins 商店包 1.0.1 构建与验证记录

## 镜像

- 微服本地标签：`peter/jenkins-custom:2.568.3-3`
- 企业仓库标签：`registry.corp.lazycat.cloud/peterlc/jenkins-custom:2.568.3-3`
- 推送摘要：`sha256:ba55cbea041da01798405211f70f576e0dcbc4c20ab5e7f3da347e37e3164d93`
- 懒猫官方镜像：`registry.lazycat.cloud/peter/jenkins-peter-9a85f1af-ab49-4652-8d83-4ba2b7262e11:a9778070fff0160e`
- 官方 manifest 摘要：`sha256:a9778070fff0160e39edd32ef21515d28fa5223d121e39d510df3a8a5b4ca792`
- 架构：`linux/amd64`

镜像在 `peterlc` 微服上通过 `lzc-docker` 构建并推送，没有在本机 Ubuntu 执行镜像构建。

## 功能验证

远程验证脚本确认以下项目全部通过：

- admin 身份认证成功，匿名访问被拒绝；
- admin 修改密码后，容器重启仍可使用新密码登录；
- 深色主题和 96 个插件成功加载；
- Python、Git、Go、Node.js 和 npm 可用；
- Jenkins Pipeline 成功运行并生成归档产物；
- 容器重启后密码、主题、插件、任务记录和产物保持不变；
- 持久目录使用 `/lzcapp/var/jenkins`；
- 从旧目录升级到新目录的兼容迁移通过验证。

## LPK 配置

- 包名：`peter.lazycat.app.jenkins`
- 版本：`1.0.1`
- 动态 URL：`https://{{ .S.AppDomain }}/`
- 管理员用户名：`admin`
- 初始密码：`peter111`，登录后可修改且不会在重启时回退
- 登录页注入：未配置
- 忘记密码恢复：写入 `secrets/reset-admin-password` 后重启
- 图标：512×512 RGBA PNG

## 应用商店镜像转存

2026-09-11 使用开发者 PAT 请求生产 `/sdk/v3/developer/app/docker/image/push/v3/copy` 成功，HTTP 200，服务端返回 `data: "ok"`。首次以私有企业仓库为源时，任务在拉取阶段因 `UNAUTHORIZED` 失败。

随后在本机将同摘要镜像临时推送到 6 小时自动过期、可匿名拉取的 OCI 中转仓库，并重新请求 SDK。最终进度响应为 `finished: true`、`errmsg: ""`，实际返回：

```text
registry.lazycat.cloud/peter/jenkins-peter-9a85f1af-ab49-4652-8d83-4ba2b7262e11:a9778070fff0160e
```

官方镜像可匿名读取，平台为 `linux/amd64`，26 个文件层及 RootFS 与源镜像完全一致。官方服务只增加了镜像来源与维护者标签，没有改变 Entrypoint、环境变量、运行用户或文件内容。目标微服已成功拉取并确认自定义 Entrypoint。主 manifest 已更新为该真实地址，最终 `lzc-cli lpk lint` 为零警告。
