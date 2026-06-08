@echo off
REM activate_env.bat - activate parent .venv when run from the modal_app folder (CMD)
IF EXIST "..\.venv\Scripts\activate.bat" (
    CALL "..\.venv\Scripts\activate.bat"
) ELSE (
    ECHO Error: ..\.venv\Scripts\activate.bat not found.
    ECHO Make sure the virtualenv is at ..\.venv or adjust this file.
    PAUSE
)
