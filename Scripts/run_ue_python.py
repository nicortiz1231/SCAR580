#!/usr/bin/env python3
"""Execute a Python script inside the running Unreal Editor via remote execution."""
import sys
import time
from pathlib import Path

ENGINE_PY = Path(
    "/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python"
)
sys.path.insert(0, str(ENGINE_PY))

import remote_execution  # noqa: E402


def main():
    script = sys.argv[1] if len(sys.argv) > 1 else None
    if not script:
        print("Usage: run_ue_python.py /path/to/script.py")
        return 2

    script_path = Path(script).resolve()
    if not script_path.exists():
        print(f"Missing script: {script_path}")
        return 2

    config = remote_execution.RemoteExecutionConfig()
    remote = remote_execution.RemoteExecution(config)
    remote.start()

    deadline = time.time() + 8.0
    nodes = []
    while time.time() < deadline:
        nodes = remote.remote_nodes
        if nodes:
            break
        time.sleep(0.5)

    if not nodes:
        print("ERROR: No Unreal Editor Python remote nodes found.")
        print("Enable Edit ▸ Editor Preferences ▸ Python ▸ Enable Remote Execution")
        remote.stop()
        return 1

    node = nodes[0]
    node_id = node.get("node_id")
    print(f"Connecting to Unreal node: {node.get('node_name', node_id)} ({node_id})")
    remote.open_command_connection(node_id)

    # ExecuteFile mode runs the script path
    result = remote.run_command(
        str(script_path),
        unattended=True,
        exec_mode=remote_execution.MODE_EXEC_FILE,
        raise_on_failure=False,
    )
    print("RESULT:", result)
    success = False
    if isinstance(result, dict):
        success = bool(result.get("success", False))
        if result.get("result"):
            print(result.get("result"))
        if result.get("command_output"):
            print(result.get("command_output"))
    else:
        success = True

    remote.stop()
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
