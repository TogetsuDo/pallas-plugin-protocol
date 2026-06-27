# 更新日志

本文件依据 git tag 历史整理，版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。
新提交合入后请在 `## [Unreleased]` 下记录，发布时随版本 tag 归档。

## [Unreleased]

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
