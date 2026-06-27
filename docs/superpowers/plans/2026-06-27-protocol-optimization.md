# Protocol 批量重启与 WebUI 统一 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 消除协议端批量重启/启停的高并发负载尖峰，并在 Bot WebUI 提供进度反馈与协议管理能力，逐步替代内置 `/protocol/console/` 单体页。

**Architecture:** 新增 `account_batch.py` 编排 rolling/限流批量 job；HTTP `POST /api/accounts/batch` + SSE 进度；协议内置页与 WebUI 统一调用 batch API；WebUI 扩展 create/import/assets 子路由；`service.py` 生命周期方法委托 batch 模块。

**Tech Stack:** Python 3.12 asyncio、FastAPI SSE、Vue 3 + TypeScript

---

## Phase P0 — 批量 API 与负载控制

### Task 1: account_batch 模块

**Files:**
- Create: `src/pallas_plugin_protocol/account_batch.py`
- Test: `tests/test_account_batch.py`

- [ ] 实现 `AccountBatchCoordinator`：rolling stop→stagger start、parallel+semaphore、job 状态与 SSE
- [ ] 默认 `max_concurrency=2`、`stagger_ms=3000`、`mode=rolling`

### Task 2: 配置项

**Files:**
- Modify: `src/pallas_plugin_protocol/config.py`
- Modify: `pallas/console/webui/field_labels.py` + `env_sections.py`（Bot 仓）

- [ ] `pallas_protocol_restart_max_concurrency`（默认 2）
- [ ] `pallas_protocol_restart_stagger_s`（默认 3.0）

### Task 3: service + routes

**Files:**
- Modify: `src/pallas_plugin_protocol/service.py`
- Modify: `src/pallas_plugin_protocol/web/routes.py`

- [ ] `POST /api/accounts/batch` body: action, account_ids, mode, max_concurrency, stagger_ms
- [ ] `GET /api/accounts/batch/{job_id}`
- [ ] `GET /api/accounts/batch/{job_id}/stream` SSE

### Task 4: 内置 WebUI JS

**Files:**
- Modify: `src/pallas_plugin_protocol/web/pages.py`

- [ ] `restartAllAccounts` / `toggleAllAccounts` / `stopSelectedAccounts` 改 batch API + 进度条

---

## Phase P1 — Bot WebUI 进度与批量

### Task 5: protocolApi + composable

**Files:**
- Modify: `src/api/protocolApi.ts`
- Create: `src/utils/protocolBatchProgress.ts`
- Create: `src/composables/useProtocolAccountBatch.ts`

### Task 6: ProtocolManagePage

**Files:**
- Modify: `src/pages/ProtocolManagePage.vue`

- [ ] 批量重启进度 UI；去掉 `Promise.all`
- [ ] 可选「重启全部」按钮（rolling 确认）

---

## Phase P2 — WebUI 协议子页

### Task 7: 路由与子页

**Files:**
- Create: `src/pages/ProtocolCreatePage.vue`
- Create: `src/pages/ProtocolImportPage.vue`
- Create: `src/pages/ProtocolAssetsPage.vue`
- Modify: `src/router/index.ts`, `chunkLoaders.ts`, `mainNav.ts`
- Extend: `src/api/protocolApi.ts`

---

## Phase P3 — 质量

### Task 8: 测试与 CHANGELOG

- [ ] `tests/test_account_batch.py` + Protocol 仓 `pytest` dev 依赖
- [ ] `CHANGELOG.md` Unreleased 条目
- [ ] `uv run ruff check/format` Protocol + WebUI build
