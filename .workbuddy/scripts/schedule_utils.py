#!/usr/bin/env python3
"""调度稳态工具（精简版 - 依赖 Claw 的主 utils）
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CLAW_SCRIPTS = Path.home() / "WorkBuddy" / "Claw" / ".workbuddy" / "scripts"

def main():
    if len(sys.argv) < 3:
        print("用法: schedule_utils.py check|done --name <任务名>")
        sys.exit(1)

    action = sys.argv[1]
    name = None
    for i, arg in enumerate(sys.argv):
        if arg == "--name" and i + 1 < len(sys.argv):
            name = sys.argv[i + 1]

    if not name:
        print("缺少 --name 参数")
        sys.exit(1)

    # 委托给 Claw 的 schedule_utils
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "claw_schedule",
        str(CLAW_SCRIPTS / "schedule_utils.py")
    )
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        getattr(mod, action)(name)
        print(f"✅ schedule_utils.{action}('{name}') 完成")
    else:
        print("⚠️ Claw schedule_utils 不可用，跳过调度锁")
        sys.exit(0)

if __name__ == "__main__":
    main()
