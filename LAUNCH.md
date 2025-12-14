**Run the application without opening a terminal**

This repository includes simple launchers so you can start the app by double-clicking, without opening a Command Prompt or VS Code.

- `launchers/run_app.vbs` — Recommended for double-clicking. Uses `pythonw` to start `main.py` with no console window. Double-clicking this file runs the application hidden.
- `launchers/run_app.bat` — Batch file that runs `pythonw` when available, falls back to `python`. Double-clicking may open a console briefly while launching if `pythonw` is not present.
- `launchers/run_app.ps1` — PowerShell script that starts `pythonw` with hidden window. If your PowerShell execution policy prevents running scripts, you can right-click and run with `PowerShell -ExecutionPolicy Bypass -File launchers\run_app.ps1`.

Requirements & notes
- You must have Python installed and accessible on your `PATH` (either `pythonw` or `python`). If you use a virtual environment, create a shortcut that points to the venv's `pythonw.exe` instead.
- If you want a single native `.exe` file for distribution, consider using `pyinstaller`:

  ```powershell
  pip install pyinstaller
  pyinstaller --noconsole --onefile main.py
  ```

  The generated executable will be in the `dist` folder.

Usage examples
- Double-click `launchers\run_app.vbs` to start with no console window.
- Or double-click `launchers\run_app.bat` (best if `pythonw` exists on PATH).
- To run the PowerShell launcher from a command line with bypassed policy:

  ```powershell
  PowerShell -ExecutionPolicy Bypass -File launchers\run_app.ps1
  ```

If you'd like, I can also create a Windows shortcut (`.lnk`) that points to `pythonw` and set an icon, or build a single `.exe` using `pyinstaller` and add a simple script to produce it.
