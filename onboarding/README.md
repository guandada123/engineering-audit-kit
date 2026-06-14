# 工程质量公共工作流落地包（per-repo 薄调用）

本目录提供 QTS / Claw / StockInsight / MarvisBridge 四个仓库的薄调用工作流 `ci.yml`，用于快速接入中枢仓库 `guandada123/engineering-audit-kit` 提供的 Reusable Workflow（Quality Gate）。

## 已完成的 PR

| 仓库 | PR | 状态 |
|------|-----|------|
| QuantTradingSystem | [#16](https://github.com/guandada123/QuantTradingSystem/pull/16) | 待合并 |
| Claw | [#3](https://github.com/guandada123/Claw/pull/3) | 待合并 |
| StockInsight | [#9](https://github.com/guandada123/StockInsight/pull/9) | 待合并 |
| Marvis Bridge | 本地项目，待决定方案 |

## 中枢仓库

- 仓库：https://github.com/guandada123/engineering-audit-kit
- 版本标签：`v1`
- 质量门工作流：`.github/workflows/quality-gate.yml`（Reusable Workflow）

## MarvisBridge 特殊处理

Marvis Bridge（`~/workbuddy_marvis_bridge/`）为本地项目，无 GitHub 远程仓库。
两个方案可选：

**方案 A**：创建 GitHub 仓库 `guandada123/MarvisBridge` 并推代码，接入公共工作流（推荐，统一管理）
**方案 B**：独立维护本地质量门，将 `quality-gate.yml` 复制为独立工作流（不由中枢控制）

## 使用步骤（新仓库接入）

1. 拷贝对应 `per-repo/<repo>/.github/workflows/ci.yml` 到业务仓库；
2. `uses` 行固定引用 `guandada123/engineering-audit-kit@v1`；
3. 在组织设置中允许 Reusable workflows 被调用；
4. 在分支保护规则中将 `Quality Gate (Reusable)` 设为必需检查。