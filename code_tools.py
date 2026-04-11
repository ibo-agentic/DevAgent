#subprocess lets python run other programs and commands. we'll use it to run python code
import subprocess
import os

def write_file(filepath, content):
    # Why: saves code written by the LLM to an actual file
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{filepath}' written successfully!"
    except Exception as e:
        return f"Error writing file: {e}"

def run_code(filepath):
    # Why: actually executes the Python file and returns the output
    try:
        result = subprocess.run(
            ["python", filepath],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return f"Output:\n{result.stdout}"
        else:
            return f"Error:\n{result.stderr}"
    except Exception as e:
        return f"Error running code: {e}"