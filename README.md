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

## 可复用工作流（下游调用）

下游仓库这样调用（见 `.github/workflows/caller-example.yml`）：

```yaml
jobs:
  quality-gate:
    uses: guandada123/engineering-audit-kit/.github/workflows/quality-gate.yml@v3
    with:
      run-python: "on"
      run-php: "off"
    secrets: inherit
```

### 可直接拉取执行的脚本

| 脚本 | 作用 | 下游用法 |
| --- | --- | --- |
| `scripts/audit_locks.py` | **锁文件依赖漏洞门禁**：只读 `uv.lock` + 查 OSV；**只挡「有修复版本」**的漏洞，无修复版本只提示；allowlist 每条必须带 `reason` + `expires`（到期即失效）；查询失败按 `rc=2` 视为**无法判定**（不静默放过）。退出码 0 通过 / 1 有可处置 / 2 无法判定 | 按 **pin 的 tag** 拉取执行，见下方示例 |

```yaml
  lock-audit:
    name: Lock Dependency Audit (blocking)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }   # 需要 3.11+（tomllib）
      - run: |
          curl -fsSL -o /tmp/audit_locks.py \
            https://raw.githubusercontent.com/guandada123/engineering-audit-kit/v4/scripts/audit_locks.py
          python3 /tmp/audit_locks.py --root .
```

⚠️ 该脚本目前存在**两份同源副本**（本仓库 + Claw 的 `.workbuddy/scripts/audit_locks.py`，后者被其单测引用），
差异仅 import 顺序。**改判据要同时改两份**；收敛计划见 Claw 的 `registry.pending_actions`。

**版本铁律（2026-10-10 血的教训）**

| tag | 状态 | 说明 |
| --- | --- | --- |
| `v1` | ✅ 可用 | 已修 gitleaks license 问题 |
| `v2` | ⛔ **坏版本，勿用** | `quality-gate.yml` 里一行未加引号的 `description: PHP checks: auto|on|off` → **YAML 非法**；唯一下游 QuantTradingSystem 调它时**启动即失败**（无 job/无日志），自 2026-10-02 起 CI 红了 8 天 |
| `v3` | ✅ 可用 | 在 v2 之上修 YAML、改 Docker 直调 gitleaks、并补 bandit / pytest 步骤 |
| `v4` | ✅ **当前** | v3 + 新增 `scripts/audit_locks.py`（跨仓库消费的锁文件漏洞门禁，下游按 pin 的 tag 拉取执行） |

⚠️ 两个坑，打 tag 前必看：

1. **本仓库的 tag 与提交时间不一致**：`v2` 指向的提交（6b346f2）比 `v1`（ae57b18）**更旧**，
   于是 Dependabot 按版本号"升级" v1→v2 实际上把下游**降级到了坏版本**。发新 tag 时务必确认
   它指向 **当前 main**，且新 tag 号大于既有全部 tag。
2. **必须有机器校验**：EAK CI 新增 `Workflow YAML Validate` job（`.github/workflows/**` 变更即触发），
   任何 workflow 文件解析失败就红。此前 CI 只 lint `scripts/`，workflows/ 完全没覆盖，
   坏文件才会被直接打上 tag。

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
