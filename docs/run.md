# `run.py` — Application Entry Point

## Purpose

`run.py` is the single entry point for the entire application. Its only job is to launch the Streamlit UI by invoking `streamlit run app.py` as a subprocess. This means the user only ever needs to run one command: `python run.py`.

---

## Full File

```python
"""
Application entry point — launches the Streamlit UI.
"""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    app = Path(__file__).parent / "app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app)], check=True)
```

---

## Line-by-Line Breakdown

### Imports

```python
import subprocess
```
The standard library module used to spawn a child process. `subprocess.run` blocks until the child process exits, which means the terminal stays attached to the Streamlit server for the lifetime of the app.

```python
import sys
```
Used to get the path to the current Python interpreter via `sys.executable`. This is important because it ensures the subprocess uses the same Python environment (and therefore the same installed packages) as the parent process.

```python
from pathlib import Path
```
Used to construct the absolute path to `app.py` in a cross-platform way.

---

### `if __name__ == "__main__":`

```python
if __name__ == "__main__":
```
Standard Python guard that ensures this block only runs when the file is executed directly (`python run.py`), not when it is imported as a module. This prevents accidental side effects if `run.py` were ever imported elsewhere.

---

### Resolving `app.py`

```python
app = Path(__file__).parent / "app.py"
```

- `__file__` — the absolute path to `run.py` itself
- `.parent` — the directory containing `run.py`, i.e. the project root
- `/ "app.py"` — appends `app.py` to that directory

The result is the absolute path to `app.py`, regardless of what directory the user runs the command from. This is more robust than a relative path like `"app.py"`, which would break if the user ran `python path/to/run.py` from a different working directory.

---

### Launching Streamlit

```python
subprocess.run([sys.executable, "-m", "streamlit", "run", str(app)], check=True)
```

This is equivalent to running the following in the terminal:

```bash
python -m streamlit run /absolute/path/to/app.py
```

- `sys.executable` — the full path to the active Python interpreter (e.g. `.venv/Scripts/python.exe`). Using this instead of the string `"python"` guarantees the correct virtual environment is used.
- `"-m", "streamlit"` — runs Streamlit as a module, which is more reliable than relying on the `streamlit` command being on `PATH`.
- `"run", str(app)` — tells Streamlit to serve `app.py`.
- `check=True` — raises a `CalledProcessError` if the subprocess exits with a non-zero status code, surfacing errors clearly instead of silently failing.

Streamlit automatically opens the app in the default browser at `http://localhost:8501` when the server starts.
