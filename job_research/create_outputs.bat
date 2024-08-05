@echo off
setlocal enabledelayedexpansion

REM Prompt user for input
set /p TITLE="Enter job title: "
set /p COMPANY="Enter company name: "
set /p DESCRIPTION="Enter job description: "

REM Run the Python script with the provided parameters
python -c "from main import JobSearchAssistant, USER_CONTEXT_FILE, USER_WANT_FILE; assistant = JobSearchAssistant(USER_CONTEXT_FILE, USER_WANT_FILE); assistant.create_outputs_from_params('%TITLE%', '%COMPANY%', '%DESCRIPTION%')"

echo.
echo Outputs created successfully!
pause
