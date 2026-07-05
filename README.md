# Engineering Audit Kit — 工程审计工具包

[![EAK CI](https://github.com/guandada123/engineering-audit-kit/actions/workflows/eak-ci.yml/badge.svg)](https://github.com/guandada123/engineering-audit-kit/actions/workflows/eak-ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)]()

可复用的审计剧本、安全扫描规则与配置模板，用于自动化工程审计与合规检查。

## 功能

- **代码审计**：ruff + bandit 静态分析，硬编码路径扫描，gitleaks 密钥泄露检测
- **安全门禁**：pre-commit 自动化检查，CI 门禁配置
- **模板库**：审计报告模板、配置文件模板

## 快速开始

```bash
# 安装依赖
uv sync

# 运行审计
pre-commit run --all-files

# 安全扫描
bandit -r . -lll
```

## 项目结构

```
├── pyproject.toml      # 项目配置与依赖
├── ruff.toml           # ruff 规则
├── .pre-commit-config.yaml
├── .gitmessage         # commit 模板
├── CHANGELOG.md
└── .github/workflows/
    └── eak-ci.yml      # CI 流水线
```

## CI 状态

| 检查项 | 门禁 |
|--------|:----:|
| ruff lint | ✅ 阻断 |
| ruff format | ✅ 阻断 |
| bandit 安全 | ✅ 高危=0 |
| 硬编码路径 | ✅ 0 处 |
| gitleaks 密钥 | ✅ 阻断 |
