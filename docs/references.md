# 官方资料与素材来源

核验日期：2026-09-10。本目录配置针对 LPK v2；旧文章把包名和版本放在 manifest 顶层的示例不直接适用。

| 官方资料 | 查阅内容 |
| --- | --- |
| [开发者环境搭建](https://developer.lazycat.cloud/getting-started/env-setup.html) | 安装 CLI、连接微服、授权公钥 |
| [lzc-build.yml 规范](https://developer.lazycat.cloud/spec/build.html) | manifest、icon、pkgout、buildscript；可省略 contentdir |
| [package.yml 规范](https://developer.lazycat.cloud/spec/package.html) | 包名、版本、权限、最低系统版本、平台与本地化 |
| [lzc-manifest.yml 规范](https://developer.lazycat.cloud/spec/manifest.html) | 路由、服务、binds、run_as、healthcheck |
| [LPK 格式](https://developer.lazycat.cloud/spec/lpk-format.html) | LPK v2 结构及内嵌镜像 |
| [文件访问](https://developer.lazycat.cloud/advanced-file.html) | 持久目录与非 root 用户权限 |
| [应用上架审核指南](https://developer.lazycat.cloud/store-submission-guide.html) | 商店资料、免密登录及实际运行测试要求 |
| [Jenkins Docker 安装文档](https://www.jenkins.io/doc/book/installing/docker/) | 官方容器安装与初始化 |
| [Jenkins 官方镜像仓库说明](https://github.com/jenkinsci/docker/blob/master/README.md) | 数据目录、UID、JVM 参数、agent |
| [Jenkins 官方图标](https://www.jenkins.io/artwork/) | 图标来源及署名要求 |

## 镜像记录

上游镜像为 `jenkins/jenkins:lts-jdk21`，摘要与平台信息查询自 [Docker Hub 官方仓库 API](https://hub.docker.com/v2/repositories/jenkins/jenkins/tags/lts-jdk21)。当次记录见同目录 `image-source.json`；manifest 使用多架构索引摘要，包含 Linux amd64 和 arm64。查询镜像元数据不等于完成容器启动验证。

## 图标署名

`lzc-icon.png` 由 [Jenkins 官方 PNG](https://www.jenkins.io/images/logos/jenkins/jenkins.png) 适配为应用商店所需的 512 × 512 RGBA PNG。

图标归属 [Jenkins 项目](https://www.jenkins.io/)，原始设计由 Frontside 创作，适配版本按 [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) 使用。Jenkins 软件的 MIT 许可证与图标许可证不同，详见仓库根目录 `NOTICE.md`。
