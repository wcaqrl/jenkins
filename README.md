# Jenkins 定制镜像与懒猫 LPK

包名为 `peter.lazycat.app.jenkins`，当前版本为 `1.0.2`。镜像构建、运行和验证均在 `peterlc` 微服上完成，本机只保存源文件、资料和轻量 LPK。

## 当前状态

- 微服本地镜像：`peter/jenkins-custom:2.568.3-3`
- 企业仓库镜像：`registry.corp.lazycat.cloud/peterlc/jenkins-custom:2.568.3-3`
- 企业仓库摘要：`sha256:ba55cbea041da01798405211f70f576e0dcbc4c20ab5e7f3da347e37e3164d93`
- 懒猫官方镜像：`registry.lazycat.cloud/peter/jenkins-peter-9a85f1af-ab49-4652-8d83-4ba2b7262e11:a9778070fff0160e`
- 官方 manifest 摘要：`sha256:a9778070fff0160e39edd32ef21515d28fa5223d121e39d510df3a8a5b4ca792`
- 平台：`linux/amd64`
- LZCOS 最低版本：`1.6.0`
- LPK：`dist/peter.lazycat.app.jenkins-v1.0.2.lpk`

生产应用商店的 `/sdk/v3` `copy-image` 已使用开发者 PAT 完成转存，进度返回 `finished=true`、`errmsg` 为空，并生成小写 `registry.lazycat.cloud/peter/` 路径。主 manifest 已引用接口返回的真实官方地址。

## 已验证的镜像内容

| 项目 | 版本或配置 |
| --- | --- |
| Jenkins | 2.568.3 LTS，JDK 21 |
| Python | 3.12.14，含 pip、venv、SSL 和 SQLite |
| Git | 2.47.3 |
| Go | 1.27.1 |
| Node.js | 26.8.2 |
| npm | 12.0.2 |
| Jenkins 插件 | 23 个直接选择的插件，连同依赖共 96 个已加载插件 |
| 账号 | 管理员 `admin`，初始密码 `peter111`，支持登录后修改 |
| 外观 | 默认深色主题 |
| 持久化 | `/lzcapp/var/jenkins` |

微服验证覆盖初始管理员认证、管理员修改密码、修改后重启登录、匿名访问拒绝、深色主题、插件状态、Python/Git/Go/Node/npm 工具链、Pipeline、归档产物及容器重启后的数据恢复，全部通过。

## 登录与密码

管理员用户名固定为 `admin`，初始密码为 `peter111`。manifest 通过 `JENKINS_ADMIN_PASSWORD` 把初始密码交给容器启动脚本。第一次启动使用 `jenkins-bootstrap.yaml` 创建账号；检测到 admin 已存在后，后续启动改用不包含用户密码的 `jenkins.yaml`，因此管理员在 Jenkins 网页修改密码后不会被 JCasC 覆盖。

登录采用懒猫官方 inject 三阶段方案：`request` 阶段只把 Jenkins 登录或网页改密请求中的候选凭据放入 `ctx.flow`，`response` 阶段确认 Jenkins 接受请求后才写入当前微服用户的 `ctx.persist`，`browser` 阶段使用 `builtin://simple-inject-password` 自动填充并提交登录表单。首次没有持久值时使用 `admin / peter111`；管理员从 Jenkins 的“安全”页面修改密码后，下一次自动登录会使用新密码。登录失败页不会自动提交，避免旧凭据造成重试循环。

Jenkins 的安全设置页没有“当前密码”字段。未修改密码时，`user.password` 与 `user.password2` 是两个不同的受保护占位值；inject 仅在两字段非空且相等时把它识别为真实改密请求。通过脚本控制台、API 或一次性重置文件改密后，需要在登录失败页手动登录一次，成功响应会同步新的免密凭据。

初始或最近一次主动重置的密码文件为：

```text
/lzcapp/var/jenkins/secrets/admin-password
```

管理员从网页修改密码后，这个文件不会更新，也不能用于查看当前密码。Jenkins 只把新密码的单向哈希保存在 `/lzcapp/var/jenkins/users/admin_*/config.xml`；该哈希无法还原成明文密码。管理员应把新密码保存在自己的密码管理器中。

如果忘记密码，微服管理员可以写入一次性重置文件：

```bash
cd /path/to/jenkins
lzc-cli project exec --release -s jenkins -w / -- sh -c \
  'umask 077; printf "%s\\n" "New_password_123" > /lzcapp/var/jenkins/secrets/reset-admin-password'
```

随后在微服应用管理界面重启 Jenkins。启动脚本会用该值重置 admin 密码，并自动删除 `reset-admin-password`；后续重启再次停止覆盖密码。

`JENKINS_URL` 使用安装时渲染的 `https://{{ .S.AppDomain }}/`，无需写死微服域名。

## 持久化

Jenkins Home 统一设为 `/lzcapp/var/jenkins`，配置、用户、凭据、插件、任务、工作区、构建历史和归档产物都保存在该目录。LZCOS 将 `/lzcapp/var` 映射到应用持久存储，`run_as: "1000:1000"` 与 Jenkins 官方镜像用户一致。

启动脚本包含一次兼容迁移：若新目录尚不存在但检测到旧版 `/lzcapp/var/jenkins_home`，会把旧目录整体移动到新位置。这是代码中唯一保留旧名称的地方，用于升级时保护既有数据。

## 项目文件

| 文件 | 用途 |
| --- | --- |
| `image/Dockerfile` | 基于官方 Jenkins 镜像安装工具链和插件 |
| `image/entrypoint.sh` | 准备持久目录、同步密码并启动 Jenkins |
| `image/jenkins-bootstrap.yaml` | 首次初始化或主动重置时创建、更新 admin |
| `image/jenkins.yaml` | 后续启动的 JCasC 授权、主题和执行器配置，不覆盖密码 |
| `image/plugins.txt` | 插件输入清单 |
| `image/plugins.lock.txt` | 实际安装的插件版本快照 |
| `image/versions.lock.json` | 上游镜像和工具链版本、摘要及校验值 |
| `scripts/build-on-box.sh` | 在微服构建、验证并推送企业仓库镜像 |
| `scripts/remote-validate.sh` | 微服端功能与重启持久化验证 |
| `docs/passwordless-login.md` | 三阶段免密登录原理、Jenkins 适配点与验证步骤 |
| `docs/verification-1.0.2.md` | 1.0.2 构建、安装及免密登录验证记录 |
| `lzc-manifest.yml` | 路由、服务、动态域名和固定管理员密码配置 |
| `package.yml` | 包信息、中英文说明、权限和系统版本 |
| `lzc-build.yml` | LPK 构建入口 |
| `lzc-icon.png` | 512×512 RGBA 应用图标 |

项目没有 `lzc-build.dev.yml`。固定管理员密码按要求写在 manifest 的服务环境变量中，没有写入镜像层。

## 构建与安装

只修改 LPK 配置时在本机执行：

```bash
cd /path/to/jenkins
lzc-cli project build
lzc-cli lpk info dist/peter.lazycat.app.jenkins-v1.0.2.lpk
lzc-cli lpk lint dist/peter.lazycat.app.jenkins-v1.0.2.lpk
```

重新制作镜像时执行：

```bash
cd /path/to/jenkins
./scripts/build-on-box.sh
```

该脚本把镜像构建、运行验证和企业仓库推送放在微服上。取得生产 `copy-image` 返回的官网镜像地址后，更新 `lzc-manifest.yml`，再在本机执行 `lzc-cli project build` 和商店 lint，最后安装验证：

```bash
lzc-cli app install "$PWD/dist/peter.lazycat.app.jenkins-v1.0.2.lpk"
```

`unsupported_platforms` 只能声明客户端平台，不能填 Docker 架构；项目已删除错误的 `linux/arm64` 值。

相关资料：[Jenkins Docker](https://github.com/jenkinsci/docker)、[Configuration as Code](https://plugins.jenkins.io/configuration-as-code/)、[深色主题](https://plugins.jenkins.io/dark-theme/)、[懒猫 LPK v2 规范](https://developer.lazycat.cloud/spec/lpk-format.html)。

## 自动跟随 Jenkins LTS

仓库已提供两段 GitHub Actions 流程：`.github/workflows/build-jenkins-image.yml` 检查官方 Jenkins LTS 摘要、构建并完整验证定制镜像；`.github/workflows/publish-lazycat.yml` 复用 `ca-x/lazycat-github-action` 完成官方镜像转存、应用 patch 版本递增、LPK 构建与 lint、GitHub Release 和懒猫应用商店审核提交。

启用前只需完成两项一次性设置：把首次生成的 `ghcr.io/wcaqrl/jenkins-lazycat` 包设为 Public，并把具有 `developer.app.manage` 权限的懒猫开发者 PAT 保存为仓库 Secret `LZC_API_TOKEN`。完整说明见 `docs/automation.md`。
