# Changelog

## [2026-07-04] Phase 3: 统一制式

### 基础设施
- 新建 pyproject.toml
- uv.lock 依赖锁定
- ruff.toml 规则配置
- .pre-commit-config.yaml 本地钩子设置

### CI
- eak-ci.yml：ruff lint + bandit + 硬编码路径扫描
