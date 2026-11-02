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
    uses: guandada123/engineering-audit-kit/.github/workflows/quality-gate.yml@v8
    with:
      run-python: "on"
      run-php: "off"
      # 单包仓库：留默认 auto，根目录 pytest 失败即红（v7 起不再吞错）
      # 多包/微服务仓库：根目录一起收集会撞同名 tests 包，设 off 并由自己的 workflow 按服务跑
      run-pytest: "auto"   # auto | on | off
    secrets: inherit
```

> `run-pytest: off` 与「吞掉失败」的区别：off 会让该步骤在 GitHub 上显示为 **skipped**（可见），
> 且含义是「测试由别处负责」；而 v6 之前的 `|| echo` 是显示 **success** 但实际失败——后者是假事实。

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
            https://raw.githubusercontent.com/guandada123/engineering-audit-kit/v8/scripts/audit_locks.py
          python3 /tmp/audit_locks.py --root .
```

⚠️ 该脚本存在**两份副本**：本仓库为**唯一真源**，Claw 的 `.workbuddy/scripts/audit_locks.py` 是逐字节一致的同步副本
（被其单测 `tests/test_audit_locks.py` 与 CI 直接引用）。

**改判据只改本仓库**，然后按 tag 覆盖 Claw 副本：

```bash
curl -fsSL -o ../Claw/.workbuddy/scripts/audit_locks.py \
  https://raw.githubusercontent.com/guandada123/engineering-audit-kit/v8/scripts/audit_locks.py
```

**漂移已被机器卡住**（2026-11-01 收敛）：Claw 的 `security-scan.yml` 新增
`Verify local copy matches EAK single source` 步骤——下载 ping 住的 tag 文件与本地副本 `diff`，
不一致立即红，不再靠人记着"两份都要改"。

> 历史：v4 时两份差异只有 import 顺序（因两仓 `target-version` 不同：Claw=py39、EAK=py311，
> `tomllib` 的 stdlib 归属判定不同）。v5 起 Claw 副本一度停在 v4 文案（缺 requirements.lock 分支），
> 差异从"排序"变成"行为"。现改为逐字节一致，并在 Claw 的 ruff 配置里对该文件豁免 I001。

**版本铁律（2026-10-10 血的教训）**

| tag | 状态 | 说明 |
| --- | --- | --- |
| `v1` | ✅ 可用 | 已修 gitleaks license 问题 |
| `v2` | ⛔ **坏版本，勿用** | `quality-gate.yml` 里一行未加引号的 `description: PHP checks: auto|on|off` → **YAML 非法**；唯一下游 QuantTradingSystem 调它时**启动即失败**（无 job/无日志），自 2026-10-02 起 CI 红了 8 天 |
| `v3` | ✅ 可用 | 在 v2 之上修 YAML、改 Docker 直调 gitleaks、并补 bandit / pytest 步骤 |
| `v4` | ✅ 可用 | v3 + 新增 `scripts/audit_locks.py`（跨仓库消费的锁文件漏洞门禁，下游按 pin 的 tag 拉取执行） |
| `v5` | ✅ 可用 | `audit_locks.py` 支持 `requirements.lock`（pip freeze 格式）；**工作流未变**，仍等同 v3 |
| `v6` | ✅ 可用 | **修 quality-gate 的 pytest 假绿灯**：`|| echo` 吞掉测试失败 → 改为真红；`pip install -e .` 只在项目确有可安装包时执行（原 `|| true` 会掩盖安装失败）。**工作流有行为变更，引用方升级后会开始真红** |
| `v7` | ✅ 可用 | v6 + 新增 `run-pytest: auto\|on\|off` 输入。起因：多包/微服务仓库在根目录收集会撞同名 `tests` 包（pytest `ImportPathMismatchError`），v6 会让这类仓库无法用公共门；`off` 是**明确委托**（测试由仓库自己的 workflow 按服务跑），不是吞失败 |
| `v8` | ✅ **当前** | **把剩下两处吞错变真闸门**：`bandit ... \|\| echo 跳过` → `bandit -r . -lll`（HIGH 即阻断，且不再传 `-c pyproject.toml`——根目录无 `[tool.bandit]` 时报错正是被吞掉的那一段）；`npm audit ... \|\| true` → 去掉 `\|\| true`（放松用 `npm-audit-level`）。本仓 `eak-ci.yml` 的 bandit 同步改为 `-lll` 阻断。**引用方升上来后，此前被吞的安全问题会开始红** |

⚠️ 两个坑，打 tag 前必看：

1. **本仓库的 tag 与提交时间不一致**：`v2` 指向的提交（6b346f2）比 `v1`（ae57b18）**更旧**，
   于是 Dependabot 按版本号"升级" v1→v2 实际上把下游**降级到了坏版本**。发新 tag 时务必确认
   它指向 **当前 main**，且新 tag 号大于既有全部 tag。
2. **必须有机器校验**：EAK CI 新增 `Workflow YAML Validate` job（`.github/workflows/**` 变更即触发），
   任何 workflow 文件解析失败就红。此前 CI 只 lint `scripts/`，workflows/ 完全没覆盖，
   坏文件才会被直接打上 tag。

## 消费点巡检（pin 是否落后 / 镜像是否漂移）

```bash
python3 scripts/check_eak_pins.py            # 扫 EAK 同级全部仓库，人读摘要
python3 scripts/check_eak_pins.py --json     # 机器可读
python3 scripts/check_eak_pins.py --self-test  # 验证判定逻辑本身（临时夹具）
```

它同时查两类东西，因为两者风险不同：

| 消费方式 | 例子 | 风险 | 本脚本怎么判 |
| --- | --- | --- | --- |
| **按 tag 拉取** | `raw.githubusercontent.com/.../vN/scripts/audit_locks.py`、`uses: ...@vN` | **staleness**：EAK 修了判据，消费方仍停在老 tag，门禁悄悄变弱（diff 式门禁对此无效——v5 对 v5 永远相等） | 与最新 tag 比数值；引用不存在的 tag 单列 `unknown` |
| **本地镜像** | Claw 的 `.workbuddy/scripts/audit_locks.py` | **漂移**：文件在本地、内容是老的 | 与真源比 sha256 |

退出码：`0` 全 current / `1` 有 stale 或 unknown / `2` 无法判定（拿不到 tag 列表）。

**为什么不做成消费方 CI 门**：那会让每次 EAK 发 tag 都红别的仓库，把多仓发布节奏耦死；
而这类门一旦误红，最容易被 `|| echo` 掉——又回到假绿灯。所以它只做**单点巡检**，不阻塞 PR；
本仓自身则用 CI 的 `Pin Freshness (self)` job 拦住「onboarding / 文档里的版本号」这类最容易烂的地方。

> 2026-11-02 首次运行就抓到 8 处 stale：onboarding 的 4 份薄调用种子与调用指南
> 自 v1 起从未跟版（已修到 v8）、QTS 与模板里的 `audit_locks.py` 仍 pin v5（内容与 v8 相同，已齐到 v8）。

## 项目结构

```
├── pyproject.toml      # 项目配置与依赖
├── ruff.toml           # ruff 规则
├── .pre-commit-config.yaml
├── .gitmessage         # commit 模板
├── CHANGELOG.md
├── scripts/            # audit_locks.py（锁文件漏洞门禁）/ bootstrap-audit.sh
│                       # check_eak_pins.py（消费点 pin 巡检）
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
| bandit 安全（HIGH） | 🔴 阻断（v8 起；`-lll`，中危不阻断） |
| 硬编码用户路径 | 🟡 **仅警告**（打印 `::warning::`，不失败） |

> 2026-11-01 历史：此前本表把 bandit 写成「高危=0」、硬编码路径写成「0 处」，属**假事实**——
> 那两步当时带 `|| true` 或只 warning，永远不会让 CI 变红。v8 已把 bandit 改为真阻断；
> 硬编码路径仍是警告（当前实测 0 处，但去留取决于是否要它阻断）。

`quality-gate.yml`（给下游用的公共门）的门禁口径：

| 步骤 | 口径 | 备注 |
| --- | --- | --- |
| `Python Security Scan (Bandit)` | 🔴 HIGH 即阻断 | v8 起；MEDIUM 不阻断（本地看用 `-ll`） |
| `Dependency Vulnerabilities (npm)` | 🔴 阻断在 `npm-audit-level` 阈值 | v8 起；默认 high，放松设 critical |
| `Python Tests (Pytest)` | 🔴 阻断 / 可 `run-pytest: off` 显式委托 | v6 起不再吞失败，v7 起可委托 |
| 其余（ruff / gitleaks / PHP lint） | 🔴 阻断 | — |
