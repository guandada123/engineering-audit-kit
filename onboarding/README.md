# 工程质量公共工作流落地包（per-repo 薄调用）

本目录提供 QTS / Claw / MarvisBridge 三个示例仓库的薄调用工作流 `ci.yml`，用于快速接入中枢仓库 `engineering-audit-kit` 提供的 Reusable Workflow（Quality Gate）。

使用步骤：
1. 在业务仓库创建 `.github/workflows/ci.yml`，拷贝对应示例文件内容；
2. 将 `ORG_OR_USER` 替换为你们的 GitHub 组织或用户名；
3. 给 `engineering-audit-kit` 仓库打上版本标签 `v1`；
4. 在组织设置中允许被复用的工作流（Reusable workflows）被调用；
5. 在分支保护规则中将该工作流设为必需检查；
6. 提交 PR 验证质量门执行结果。

注意：不同仓库可按需调整 `with` 参数，例如 run-python/on/off、run-eslint 等开关。