# 更新日志

本文件依据 git tag 历史整理，版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。
新提交合入后请在 `## [Unreleased]` 下记录，发布时随版本 tag 归档。

## [Unreleased]

## [4.0.28] - 2026-07-14

- fix(snowluma): WebUI 自动改密前先完成 EULA consent；否则 `change-password` 403，托管口令写不进 `accounts.json` / WebUI 不展示
- fix(snowluma): 一键登录点击 Y 比例 0.78→0.68，避免点到页脚链导致「已点击」但未真正登录
- feat(snowluma): Docker 注入 `SNOWLUMA_ACCEPT_EULA=1` / `SNOWLUMA_ACCEPT_PRIVACY=1`（上游 1.12.2 无人值守同意；旧镜像忽略）

## [4.0.27] - 2026-07-14

- fix(relogin): 临时会话发二维码失败时兜底提示加好友，避免 matcher 整次崩溃

## [4.0.26] - 2026-07-14

- refactor(web): 移除已迁入 Bot WebUI 的独立 HTML 页（`pages_pkg/`）与壳层静态 CSS，仅保留登录页字体片段与 favicon

## [4.0.25] - 2026-07-14

- fix(relogin): 群临时会话回复走 `send_private_msg` + `group_id`，SnowLuma 非好友可收文字/二维码
- feat(snowluma): WebUI API 客户端（改密、inject consent、进程轮询）与配置 Docker 同步
- fix(web): 协议独立 HTML 页重定向至 Bot WebUI `/pallas/protocol` 系列路由；偏好设置跳转 `/pallas/preferences`

## [4.0.24] - 2026-07-14

- chore(release): 版本号对齐（与 4.0.23 变更一并合入 4.0.25 发布）

## [4.0.23] - 2026-07-14

- fix(relogin): 容器重启后 QR 窗未就绪时继续轮询截屏/一键登录，不再立即报「恢复登录失败」
- fix(snowluma): refresh 失败时走 `wait_and_capture_snowluma_qrcode` 而非直接抛错
- fix(snowluma): bootstrap 口令按日志文件日期从新到旧解析，避免容器重建后误用旧口令

## [4.0.22] - 2026-07-13

- fix(snowluma): inject / 重新上号前自动完成 WebUI 首次改密（`mustChangePassword`），避免 `/api/processes` 403
- fix(snowluma): 托管改密后写入 `snowluma_managed_webui_password`，后续优先复用

## [4.0.21] - 2026-07-13

- feat(relogin): SnowLuma 一键登录分支——重新上号时自动点「登录」并等待牛牛连上，成功回复「牛牛已重新上线」
- feat(protocol): `wait_account_bot_connected` / `wait_account_process_running` / `is_bot_connected` 供上号流程轮询
- feat(snowluma): 一键登录与 inject consent、Docker wsClients 同步（4.0.20 起累积，本版一并发布）

## [4.0.20] - 2026-07-13

- fix(snowluma): libzbar 检测改为实测 decode（`zbar_version` API 已不可用导致误报）
- fix(snowluma): 截取 QQ 登录窗而非整屏；关闭 xmessage；xdotool 点击刷新后再识别
- fix(snowluma): 仅保存可解码的 txz.qq.com 二维码，废弃整屏「已过期」回退
- fix(web): 协议页主题与主 WebUI `consolePrefs` 同步；首屏防闪
- fix(web): `account_qrcode_meta` 返回 `host_deps` 状态
- fix(web): 二维码「刷新」调用 `POST /qrcode/refresh`（NapCat RefreshQRcode / SnowLuma 重截屏）
- deps: 显式声明 `httpx`、`pydantic`；`nonebot2[fastapi]` 替代裸 `nonebot2`

## [4.0.19] - 2026-07-13

- feat(snowluma): Docker 容器支持 `memory` / `memory-swap` 限额（默认 1g / 1536m），降低多开 OOM 风险
- feat(snowluma): 账号健康态 `login_required` / `health_status` / `operational_warnings`（容器运行但未连牛牛 → 待扫码）
- feat(snowluma): Hub 启动时审计 QR 截屏宿主机依赖（ImageMagick、libzbar、pillow、pyzbar）；`GET /api/snowluma/host-deps`
- feat(migrate): `POST /api/accounts/migrate-to-snowluma` 与 CLI `tools/migrate_napcat_to_snowluma.py`（默认不保留 NapCat 数据，可选 rolling 启动）
- feat(web): 协议仪表盘 KPI/状态胶囊展示「待扫码」
- fix(migrate): `preserve_napcat_data=True` 时保留既有 `account_data_dir`

## [4.0.18] - 2026-07-13

- feat(snowluma): SnowLuma Docker 无头截屏识别 QQ 登录二维码，写入 `cache/qrcode.png`，供「牛牛重新上号」与协议页 `/qrcode` 复用
- feat(snowluma): 截屏回退 `xwd` + 宿主机 ImageMagick `convert`（SnowLuma 镜像无 import/scrot）
- fix(snowluma): 容器文件读取改用 `docker exec cat`（`docker cp -` 输出 tar 导致 XWD/PNG 损坏）
- deps: 新增 `pillow`、`pyzbar`（宿主机需安装 `libzbar0`；XWD 回退需 `imagemagick`）

## [4.0.17] - 2026-06-30
- refactor(metadata): `help_audience` 由 `maintainer` 改为 `superuser`（项目无独立维护者权限等级，统一到超管）

## [4.0.16] - 2026-06-27
- docs(readme): 命令权限默认等级改用中文展示

## [4.0.15] - 2026-06-27

- style(web): 从 WebUI 同步 `console-shared.css`（窄屏与 AI 观测 Hub 样式）

## [4.0.14] - 2026-06-27
- docs(readme): 「怎么使用」口令统一加行内代码标记

## [4.0.13] - 2026-06-27

- fix(web): 补 `web/contract.py`，修复 pages_pkg 引用 `pallas_plugin_protocol.web.contract` 导致插件 import 失败

## [4.0.12] - 2026-06-27

- style(web): 内置 WebUI 与主控制台全面对齐——CSS 三层同步（console-shared + shell-protocol）、Poppins、data-summary-card / data-conn-capsule、StatCard KPI、SVG 侧栏图标
- feat(web): WebUI 引导横幅支持「不再显示」并 localStorage 记忆
- refactor(web): `pages.py` 拆分为 `pages_pkg/`（shell / dashboard / forms / account）

## [4.0.11] - 2026-06-27

- feat(batch): 新增 `POST /api/accounts/batch` rolling/限流批量启停重启，SSE 进度流；配置项 `pallas_protocol_restart_max_concurrency` / `pallas_protocol_restart_stagger_s`
- fix(web): 内置协议页批量操作改为 batch API，默认 rolling 降低峰值负载
- refactor(batch): 批量编排逻辑抽到 `account_batch_ops`；Bot 启动/停止全部启用账号改走 rolling batch
- feat(web): 内置仪表盘增加「推荐使用 Bot WebUI」引导横幅

## [4.0.10] - 2026-06-27

- fix(config): 改为写入 `config/plugins.json` 禁用 NapCat 内置插件 `napcat-plugin-builtin`，真正阻止 `#napcat` 本地命令响应（4.0.9 写入的 `enableLocalCommand` 字段 NapCat 不识别，无效）

## [4.0.9] - 2026-06-27

- fix(config): 同步 NapCat onebot11.json 时默认写入 `enableLocalCommand: false`，避免触发 `#napcat` 等本地命令（注：该字段 NapCat 不识别，已由 4.0.10 修正）

## [4.0.8] - 2026-06-25
- feat(metadata): 补充重新上号命令冷却声明

## [4.0.7] - 2026-06-24
- feat(knowledge): 声明 knowledge_sources FAQ 供 LLM 注入

## [4.0.6] - 2026-06-19
- docs: 改用 PyPI 版本徽章
- chore(assets): 替换品牌头像为透明背景版本

## [4.0.5] - 2026-06-18
- docs(readme): 统一官方插件卡片模板

## [4.0.4] - 2026-06-18
- docs(readme): 更新官方扩展安装命令

## [4.0.3] - 2026-06-18
- migrate: src.* → pallas.api.* / pallas.product.* / pallas.core.*
- release: bump to 4.0.3 for pallas import migration

## [4.0.2] - 2026-06-18
- docs(readme): 添加 Pallas-Bot hero 图
- chore(release): 4.0.2 同步 README 进 PyPI 包

## [4.0.1] - 2026-06-17
- feat: Pallas-Bot 4.0 官方扩展首包
- fix(build): 修正 hatch wheel 的 src 包路径
- feat(release): PyPI 发版 workflow 与 4.0.1
