# 工程质量公共工作流落地包（per-repo 薄调用）

本目录提供 QTS / Claw / StockInsight / MarvisBridge 四个仓库的薄调用工作流 `ci.yml`，用于快速接入中枢仓库 `guandada123/engineering-audit-kit` 提供的 Reusable Workflow（Quality Gate）。

## 已完成的 PR

| 仓库 | PR | 状态 |
|------|-----|------|
| QuantTradingSystem | [#16](https://github.com/guandada123/QuantTradingSystem/pull/16) | 待合并 |
| Claw | [#3](https://github.com/guandada123/Claw/pull/3) | 待合并 |
| StockInsight | [#9](https://github.com/guandada123/StockInsight/pull/9) | 待合并 |
| Marvis Bridge | [#1](https://github.com/guandada123/MarvisBridge/pull/1) | 待合并 |

## 中枢仓库

- 仓库：https://github.com/guandada123/engineering-audit-kit
- 版本标签：`v1`
- 质量门工作流：`.github/workflows/quality-gate.yml`（Reusable Workflow）

## 使用步骤（新仓库接入）

1. 拷贝对应 `per-repo/<repo>/.github/workflows/ci.yml` 到业务仓库；
2. `uses` 行固定引用 `guandada123/engineering-audit-kit@v1`；
3. 在组织设置中允许 Reusable workflows 被调用；
4. 在分支保护规则中将 `Quality Gate (Reusable)` 设为必需检查。