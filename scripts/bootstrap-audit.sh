#!/usr/bin/env bash
set -euo pipefail

# 使用方法： ./scripts/bootstrap-audit.sh <repo-path>
REPO="${1:-.}"

pushd "$REPO" >/dev/null

# 1) 通用忽略与编辑器规范
if [ ! -f .editorconfig ]; then
  cp "$(dirname "$0")/../configs/.editorconfig" .editorconfig || true
fi

if [ ! -f .gitattributes ]; then
  cp "$(dirname "$0")/../configs/.gitattributes" .gitattributes || true
fi

# 2) PR 模板
mkdir -p .github
if [ ! -f .github/PULL_REQUEST_TEMPLATE.md ]; then
  cp "$(dirname "$0")/../.github/PULL_REQUEST_TEMPLATE.md" .github/PULL_REQUEST_TEMPLATE.md || true
fi

# 3) 引用质量门工作流（可在根仓库中通过 workflow_call 重用）
mkdir -p .github/workflows
if [ ! -f .github/workflows/quality-gate.yml ]; then
  cp "$(dirname "$0")/../.github/workflows/quality-gate.yml" .github/workflows/quality-gate.yml || true
fi

echo "Audit bootstrap complete for $REPO"
