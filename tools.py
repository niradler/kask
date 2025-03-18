import subprocess

def run_kubectl(command: str) -> str:
    """Execute the generated kubectl command and return the output."""
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            return result.stdout or "(No output)"
        else:
            return f"Error: {result.stderr}"
    except Exception as e:
        return f"Failed to execute command: {str(e)}"