# Jenkins 1.0.2 免密登录验证记录

验证日期：2026-09-14

## 构建结果

- 包名：`peter.lazycat.app.jenkins`
- 版本：`1.0.2`
- 产物：`dist/peter.lazycat.app.jenkins-v1.0.2.lpk`
- 大小：187904 bytes
- SHA-256：`2558081914615a039b93fab0d48e28571de44a292839a3037b674cc44298f67d`
- LPK v2、tar 格式、不内嵌镜像
- `lzc-cli lpk lint`：无警告

## 实例适配检查

在 Jenkins 2.568.3 实例上确认：

- 登录页路径为 `/login`，表单提交到 `/j_spring_security_check`。
- 用户名输入框为 `#j_username`，密码输入框为 `#j_password`。
- 正确登录返回 `302 Location: /`，错误登录返回 `302 Location: /loginError`。
- 安全设置页表单提交到 `/user/admin/security/configSubmit`。
- 新密码字段为 `user.password`，确认字段为 `user.password2`。
- 未修改密码时两个密码字段包含不同的受保护占位值，因此只有“非空且相等”才按真实改密处理。

## 注入逻辑检查

两段 inline JavaScript 均通过语法检查。模拟上下文覆盖以下分支，全部通过：

1. 登录成功后提交用户名和密码到 `ctx.persist`。
2. 登录失败并跳转 `/loginError` 时不写入持久值。
3. 网页改密成功后提交新密码。
4. 未改密的两个不同受保护占位值被忽略。

## 微服安装与浏览器验证

- `lzc-cli app install` 把已安装应用升级至 1.0.2，命令返回“安装成功”。
- 最终运行清单包含 `jenkins-capture-admin-credentials`、`jenkins-commit-admin-credentials`、`jenkins-login-autofill`。
- Jenkins 服务容器恢复为 `healthy`，lzcinit 日志没有 inject 错误。
- 浏览器访问应用入口后直接显示“工作台 - Jenkins”，用户状态为 `Administrator`。
- 浏览器访问 `/logout` 后自动返回工作台，验证退出后的自动登录生效。
- `/lzcapp/var/_lzc_ext/inject/persist.json` 已创建，检查确认两个 Jenkins 键名存在；验证过程未输出密码值。

网页实际修改管理员密码会改变真实账号凭据，因此本次没有执行该破坏性步骤；改密的 request/response 分支通过模拟上下文验证。
