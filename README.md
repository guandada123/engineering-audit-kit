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
            https://raw.githubusercontent.com/guandada123/engineering-audit-kit/v6/scripts/audit_locks.py
          python3 /tmp/audit_locks.py --root .
```

⚠️ 该脚本存在**两份副本**（本仓库为权威副本；Claw 的 `.workbuddy/scripts/audit_locks.py` 被其单测引用）。
**改判据要同时改两份**；收敛计划见 Claw 的 `registry.pending_actions`。

> 2026-11-01 实测：原「差异仅 import 顺序」的表述**已不成立**。Claw 副本停在 v4 时代的文案
> （缺 `requirements.lock` 分支提示，397 行 vs 本仓库 402 行），已落后于 v5/v6。
> 在收敛前，判断锁文件相关行为请以本仓库副本为准。

**版本铁律（2026-10-10 血的教训）**

| tag | 状态 | 说明 |
| --- | --- | --- |
| `v1` | ✅ 可用 | 已修 gitleaks license 问题 |
| `v2` | ⛔ **坏版本，勿用** | `quality-gate.yml` 里一行未加引号的 `description: PHP checks: auto|on|off` → **YAML 非法**；唯一下游 QuantTradingSystem 调它时**启动即失败**（无 job/无日志），自 2026-10-02 起 CI 红了 8 天 |
| `v3` | ✅ 可用 | 在 v2 之上修 YAML、改 Docker 直调 gitleaks、并补 bandit / pytest 步骤 |
| `v4` | ✅ 可用 | v3 + 新增 `scripts/audit_locks.py`（跨仓库消费的锁文件漏洞门禁，下游按 pin 的 tag 拉取执行） |
| `v5` | ✅ 可用 | `audit_locks.py` 支持 `requirements.lock`（pip freeze 格式）；**工作流未变**，仍等同 v3 |
| `v6` | ✅ **当前** | **修 quality-gate 的 pytest 假绿灯**：`|| echo` 吞掉测试失败 → 改为真红；`pip install -e .` 只在项目确有可安装包时执行（原 `|| true` 会掩盖安装失败）。**工作流有行为变更，引用方升级后会开始真红** |

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
├── scripts/            # audit_locks.py（锁文件漏洞门禁）/ bootstrap-audit.sh
├── playbooks/          # 审计总纲 · 前端 · Laravel+Livewire · 报告模板
├── configs/            # editorconfig / gitattributes / CODEOWNERS 样例
├── onboarding/         # 各仓库薄调用 ci.yml 种子（per-repo）
└── .github/workflows/
    ├── eak-ci.yml          # 本仓库自身门禁
    ├── quality-gate.yml    # 给下游 workflow_call 的公共质量门
    └── caller-example.yml  # 调用示例（仅手动触发）
```

## CI 状态

本仓库自身（`eak-ci.yml`）的实际门禁强度，**按实测口径写**：

| 检查项 | 实际强度 |
|--------|:----:|
| ruff lint (`scripts/`) | 🔴 阻断 |
| ruff format (`scripts/`) | 🔴 阻断 |
| gitleaks 密钥 | 🔴 阻断 |
| workflow YAML 合法性 | 🔴 阻断 |
| bandit 安全 | 🟡 **仅提示**（`bandit -r scripts/ -ll \|\| true`，发现问题仍绿） |
| 硬编码用户路径 | 🟡 **仅警告**（打印 `::warning::`，不失败） |

> 2026-11-01 更正：此前本表把 bandit 写成「高危=0」、硬编码路径写成「0 处」，属**假事实**——
> 那两步都带 `|| true` 或只 warning，永远不会让 CI 变红。要真正阻断需去掉吞错并让下游同步升级。

`quality-gate.yml`（给下游用的公共门）里仍有同类残留，**尚未修**（v6 只修了 pytest）：

| 步骤 | 现状 | 风险 |
| --- | --- | --- |
| `Python Security Scan (Bandit)` | `\|\| echo 跳过` 吞掉非零退出 | 下游安全扫描永不红 |
| `Dependency Vulnerabilities (npm)` | `\|\| true` | npm 漏洞永不红，名不副实 |
