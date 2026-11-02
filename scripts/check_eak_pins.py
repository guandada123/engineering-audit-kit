#!/usr/bin/env python3
"""check_eak_pins.py —— 扫描本机所有 EAK 消费点，报告「pin 是否落后 / 镜像是否漂移」。

## 为什么要这个脚本（而不是在消费方 CI 里加门）

本仓被消费的方式有两种，风险完全不同：

1. **按 tag 拉取**（如 QuantTradingSystem 的 security-scan 用
   raw.githubusercontent.com/.../vN/scripts/audit_locks.py）——没有本地副本，
   版本号就写在文件里，不存在「以为在跑新版实际跑旧版」。
   它的风险是 **staleness**：EAK 修了判据，消费方仍停在老 tag，门禁悄悄变弱。
   → 用 diff 式门禁对此完全无效（v5 对 v5 永远相等，绿灯永远亮）。
2. **本地镜像**（如 Claw 的 .workbuddy/scripts/audit_locks.py）——风险是镜像漂移，
   即「文件在本地、内容却是老的」。→ 这类才该用 sha256 对比。

如果在消费方 CI 里加「pin 是否最新」检查，每次 EAK 发 tag 都会让别的仓库变红，
把多个仓库的发布节奏耦死；而这类门一旦误红，最容易被 `|| true` 掉 —— 又回到假绿灯。
所以本脚本定位于**单点巡检**：一处扫描全部消费点，产出人类可读摘要 + 机器可读 JSON，
由巡检或人工按需运行，不阻塞任何 PR。

## 判定与退出码

- `current`  —— 引用的 tag 等于本仓最新 tag（按 vN 数值比较），或镜像 sha256 一致
- `stale`    —— 引用的 tag 落后；或镜像与真源内容不同
- `unknown`  —— 引用的 tag 在本仓 tag 列表里不存在（拼错 / 未推送 / 未来 tag）

退出码：0=全部 current / 1=存在 stale 或 unknown / 2=无法判定（找不到 EAK 仓库或 git 不可用）

## 用法

    python3 scripts/check_eak_pins.py                # 扫 EAK 同级的全部仓库
    python3 scripts/check_eak_pins.py --root ~/WorkBuddy
    python3 scripts/check_eak_pins.py --json         # 机器可读
    python3 scripts/check_eak_pins.py --self-test    # 用临时夹具验证判定逻辑本身
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_SLUG = "guandada123/engineering-audit-kit"

# 两类显式引用形态。刻意只认这两种，避免把「README 里的历史 tag 表」误判成消费点。
RE_WORKFLOW = re.compile(
    r"uses:\s*" + re.escape(REPO_SLUG) + r"/\.github/workflows/(?P<file>[\w.\-]+)@(?P<tag>v\d+)"
)
RE_RAW = re.compile(
    r"raw\.githubusercontent\.com/" + re.escape(REPO_SLUG) + r"/(?P<tag>v\d+)/(?P<path>[\w./\-]+)"
)

TEXT_SUFFIXES = {".yml", ".yaml", ".md", ".json", ".toml", ".sh", ".py"}

# 本机镜像点：相对 EAK 仓库根的路径 -> 真源（相对 EAK 根）
MIRRORS = [
    ("../Claw/.workbuddy/scripts/audit_locks.py", "scripts/audit_locks.py"),
]

# 扫描时跳过的目录名/模式：历史快照与依赖目录不属于「现行消费点」
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".ruff_cache",
    ".mypy_cache",
    ".pytest_cache",
    "WorkBuddy_OLD",
    "_OLD",
    "_archive",
    "dist",
    "build",
}
SKIP_DIR_RE = re.compile(r"^(20\d\d-\d\d-\d\d-\d\d-\d\d-\d\d|\.claw-tracked-[a-z0-9]+)$")


def _tag_num(tag: str) -> int:
    """v12 -> 12。"""
    return int(tag.lstrip("v"))


def latest_tag(eak: Path) -> str | None:
    """返回本仓最大的 vN tag（按数值）。无 tag 返回 None。"""
    tags = all_tags(eak)
    return max(tags, key=_tag_num) if tags else None


def all_tags(eak: Path) -> list[str]:
    """本仓全部 vN tag（按数值升序）。git 不可用则返回空列表。"""
    try:
        out = subprocess.run(
            ["git", "-C", str(eak), "tag", "--list", "v*"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    tags = [t.strip() for t in out.splitlines() if re.fullmatch(r"v\d+", t.strip())]
    return sorted(tags, key=_tag_num)


def iter_files(root: Path):
    """遍历文本文件，跳过依赖目录与历史会话快照。"""
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in TEXT_SUFFIXES:
            continue
        parts = set(p.parts)
        if parts & SKIP_DIR_NAMES:
            continue
        if any(SKIP_DIR_RE.match(x) for x in p.parts):
            continue
        yield p


def scan_refs(root: Path, eak: Path) -> list[dict]:
    """扫描所有显式引用点，逐条判定 current / stale / unknown。"""
    newest = latest_tag(eak)
    found: dict[tuple, dict] = {}
    for p in iter_files(root):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in RE_WORKFLOW.finditer(line):
                key = (str(p), lineno, m.group("tag"))
                found.setdefault(
                    key,
                    {
                        "kind": "workflow_call",
                        "file": str(p),
                        "line": lineno,
                        "target": f"workflows/{m.group('file')}",
                        "tag": m.group("tag"),
                    },
                )
            for m in RE_RAW.finditer(line):
                key = (str(p), lineno, m.group("tag") + ":" + m.group("path"))
                found.setdefault(
                    key,
                    {
                        "kind": "raw_pin",
                        "file": str(p),
                        "line": lineno,
                        "target": m.group("path"),
                        "tag": m.group("tag"),
                    },
                )

    refs = sorted(found.values(), key=lambda r: (r["file"], r["line"]))
    known = set(all_tags(eak))
    for r in refs:
        if newest is None:
            r["status"] = "unknown"
            r["detail"] = "本仓 git tag 不可用"
        elif r["tag"] not in known:
            # 引用了本仓并不存在的 tag（拼错 / 未推送 / 预写未来版本）：拉取时必然 404，
            # 这不是「落后」而是「不存在」，单列 unknown 以免与 stale 混为一谈。
            r["status"] = "unknown"
            r["detail"] = f"tag 不存在（本仓有 {newest} 及更早）"
        elif _tag_num(r["tag"]) >= _tag_num(newest):
            r["status"] = "current"
            r["detail"] = f"最新 {newest}"
        else:
            r["status"] = "stale"
            r["detail"] = f"落后于最新 {newest}"
    return refs


def check_mirrors(eak: Path) -> list[dict]:
    """本地镜像 sha256 对比：镜像与真源必须逐字节一致。"""
    out: list[dict] = []
    for mirror_rel, source_rel in MIRRORS:
        mirror = (eak / mirror_rel).resolve()
        source = (eak / source_rel).resolve()
        item = {
            "kind": "mirror",
            "file": str(mirror),
            "line": 0,
            "target": source_rel,
            "tag": "",
        }
        if not mirror.exists():
            item.update(status="unknown", detail="镜像不存在（可能已改为按 tag 拉取）")
        elif not source.exists():
            item.update(status="unknown", detail="真源不存在")
        else:
            h_mirror = hashlib.sha256(mirror.read_bytes()).hexdigest()
            h_source = hashlib.sha256(source.read_bytes()).hexdigest()
            if h_mirror == h_source:
                item.update(status="current", detail=f"sha256 一致 {h_source[:12]}")
            else:
                item.update(
                    status="stale",
                    detail=f"sha256 不一致 镜像={h_mirror[:12]} 真源={h_source[:12]}",
                )
        out.append(item)
    return out


def _make_fixture(tmp: Path, tag: str, mirror_drift: bool) -> Path:
    """构造最小夹具：假 EAK 仓（带 v1/v2/v3 tag）+ 一个消费方文件 + 一个本地镜像。"""
    eak = tmp / "eak"
    (eak / "scripts").mkdir(parents=True)
    (eak / "scripts" / "audit_locks.py").write_text("print('1')\n", encoding="utf-8")
    quiet = {"capture_output": True, "text": True, "check": False}
    subprocess.run(["git", "-C", str(eak), "init", "-q"], **quiet)
    subprocess.run(["git", "-C", str(eak), "add", "-A"], **quiet)
    subprocess.run(
        [
            "git",
            "-C",
            str(eak),
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-qm",
            "fix",
        ],
        **quiet,
    )
    for t in ("v1", "v2", "v3"):
        subprocess.run(["git", "-C", str(eak), "tag", t], **quiet)
    consumer = tmp / "consumer"
    consumer.mkdir()
    (consumer / "ci.yml").write_text(
        "jobs:\n"
        "  q:\n"
        f"    uses: {REPO_SLUG}/.github/workflows/quality-gate.yml@{tag}\n"
        "    with: {run-python: on}\n",
        encoding="utf-8",
    )
    claw = tmp / "Claw" / ".workbuddy" / "scripts"
    claw.mkdir(parents=True)
    body = (
        "print('drifted')\n" if mirror_drift else (eak / "scripts" / "audit_locks.py").read_text()
    )
    (claw / "audit_locks.py").write_text(body, encoding="utf-8")
    return eak


def self_test() -> int:
    """验证判定逻辑本身：最新 tag 必须 current、旧 tag 必须 stale、
    不存在的 tag 必须 unknown、镜像漂移必须被抓到。"""
    cases = [
        ("v3", False, "current", "current"),
        ("v1", False, "stale", "current"),
        ("v3", True, "current", "stale"),
        # 引用一个本仓没有的 tag（拼错 / 未推送）：不是「落后」而是「不存在」，必须判 unknown
        ("v9", False, "unknown", "current"),
    ]
    failed = 0
    for tag, drift, want_ref, want_mirror in cases:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            eak = _make_fixture(tmp, tag, drift)
            refs = scan_refs(tmp, eak)
            mirrors = check_mirrors(eak)
        got_ref = refs[0]["status"] if refs else "none"
        got_mirror = mirrors[0]["status"] if mirrors else "none"
        ok = got_ref == want_ref and got_mirror == want_mirror
        failed += 0 if ok else 1
        print(
            f"{'PASS' if ok else 'FAIL'}  tag={tag} drift={drift} "
            f"-> ref={got_ref}(期望 {want_ref}) mirror={got_mirror}(期望 {want_mirror})"
        )
    print(f"\n自检：{'全部通过' if failed == 0 else f'{failed} 项失败'}")
    return 0 if failed == 0 else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="检查 EAK 各消费点的 pin 是否落后 / 镜像是否漂移")
    ap.add_argument("--root", default=None, help="扫描根目录（默认 EAK 的上一级目录）")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    ap.add_argument("--self-test", action="store_true", help="用临时夹具自检判定逻辑")
    ap.add_argument(
        "--no-mirrors",
        action="store_true",
        help="跳过本地镜像 sha256 对比（CI 里没有同级仓库时用）",
    )
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    eak = Path(__file__).resolve().parents[1]
    if not (eak / "scripts" / "audit_locks.py").exists():
        print(f"无法判定：{eak} 不像 EAK 仓库根", file=sys.stderr)
        return 2
    newest = latest_tag(eak)
    if newest is None:
        print("无法判定：拿不到本仓 git tag 列表", file=sys.stderr)
        return 2

    root = Path(args.root).expanduser().resolve() if args.root else eak.parent
    rows = scan_refs(root, eak) + ([] if args.no_mirrors else check_mirrors(eak))

    if args.json:
        print(
            json.dumps(
                {"latest": newest, "root": str(root), "items": rows}, ensure_ascii=False, indent=1
            )
        )
    else:
        print(f"EAK 最新 tag = {newest}    扫描根 = {root}\n")
        icon = {"current": "✅", "stale": "🔴", "unknown": "🟡"}
        for r in rows:
            loc = r["file"].replace(str(root) + "/", "")
            if r["line"]:
                loc += f":{r['line']}"
            print(
                f"{icon.get(r['status'], '?')} {r['status']:<7} {loc}  ->  {r['tag'] or '-'} ({r['detail']})"
            )
        n_stale = sum(1 for r in rows if r["status"] == "stale")
        n_unknown = sum(1 for r in rows if r["status"] == "unknown")
        print(
            f"\n合计 {len(rows)} 处：current {len(rows) - n_stale - n_unknown} / stale {n_stale} / unknown {n_unknown}"
        )

    return 1 if any(r["status"] != "current" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
