# 🛠️ Build & Run Guide (Smart File Organizer Pro)

## 1. Automatic Virtual Environment (venv) Enforcement
The application is configured to **always run inside the project's `venv` automatically**:
- When you run `python organizer.py` or `python cli.py`, [utils/venv_utils.py](file:///r:/filenameedit/utils/venv_utils.py) automatically checks if the script is running inside `venv`. If not, it seamlessly re-launches the process using `venv\Scripts\python.exe`.
- You can also run the convenience batch scripts:
  - **`run.bat`**: Double-click or run to launch the GUI inside `venv`.
  - **`run_cli.bat`**: Run CLI commands directly (e.g. `run_cli.bat --list-profiles`).

---

## 2. Dependencies Setup
If you need to re-install packages inside `venv`:
```cmd
.\venv\Scripts\pip.exe install -r requirements.txt
```

---

## 3. Building Standalone Windows Executable (.exe)

To bundle everything into a single standalone `.exe` using PyInstaller inside `venv`:

```cmd
.\venv\Scripts\pyinstaller.exe --noconfirm --onefile --windowed --name "AnimeOrganizerPro" --icon=icon.ico organizer.py
```

The output standalone executable will be created in the **`dist/`** folder:
```text
dist\AnimeOrganizerPro.exe
```