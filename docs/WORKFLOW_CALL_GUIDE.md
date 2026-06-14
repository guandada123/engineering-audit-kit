# 质量门公共工作流（workflow_call）接入指南

本文档说明如何将 engineering-audit-kit 仓库内的 `.github/workflows/quality-gate.yml` 作为组织级公共工作流被其他仓库复用。

## 方式一：按分支/Tag 引用（推荐）

在目标仓库新建 `.github/workflows/ci.yml`，内容如下：

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [ main ]

jobs:
  quality-gate:
    uses: guandada123/engineering-audit-kit/.github/workflows/quality-gate.yml@v1
    # 也可以固定到具体 commit SHA：
    # uses: guandada123/engineering-audit-kit/.github/workflows/quality-gate.yml@<commit-sha>
    with:
      node-version: '20'
      run-eslint: true
      run-prettier: true
      run-php: auto
      run-python: auto
      npm-audit-level: high
    secrets: inherit
```

> 说明：
> - `uses:` 引用组织内“中枢仓库”的工作流路径与版本（tag 或 commit SHA 更可审计）
> - `secrets: inherit` 让被调工作流可继承仓库级/组织级 secrets（如 GitHub Token/私有 registry）
> - `with:` 为未来扩展预留的 inputs（当前模板不强制，但建议保持一致）

## 方式二：最小薄壳工作流（仅转发触发）

若你只想让触发规则留在各仓库，具体逻辑全在公共工作流里：

```yaml
name: Quality Gate

on:
  pull_request:
  push:
    branches: [ main ]

jobs:
  call:
    uses: guandada123/engineering-audit-kit/.github/workflows/quality-gate.yml@v1
    secrets: inherit
```

## 权限与组织设置

- 确保 `engineering-audit-kit` 仓库对需要复用的仓库可见（同组织私有或公共）
- 建议使用 `v1` Tag 固定版本；升级时发布 `v2`，调用方按需迁移
- 在组织设置中开启 `Reusable workflows` 权限

## CODEOWNERS 与分支保护

在各业务仓库：
- `.github/CODEOWNERS` 指定质量门相关文件（如 `.github/workflows/**`）由平台/基础架构组评审
- 分支保护规则：
  - 必须通过 `Quality Gate` 工作流
  - 至少 1 名 Reviewer 通过
  - 禁止直接推送到 `main`

## 常见问题

1. 无法引用私有仓库工作流？
   - 确认两个仓库在同一组织，且 `actions: read` 权限开放
2. 被调工作流里需要访问 secrets？
   - 在调用侧工作流的 job 下加上 `secrets: inherit`
3. 想按项目差异化阈值？
   - 后续版本将在 `quality-gate.yml` 增加 `inputs`（如 `coverage-threshold`, `enable-lighthouse` 等）

---

如需我代为在各仓库落地薄壳工作流，请提供仓库列表或授权组织访问。