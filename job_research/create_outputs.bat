@echo off
setlocal enabledelayedexpansion

REM Ensure we're using the correct Python environment
call poetry env use python

REM Prompt user for input
set /p TITLE="Enter job title: "
set /p COMPANY="Enter company name: "

REM Create a temporary file for the description
echo Enter job description (Press Ctrl+Z and then Enter when finished):
type con > description_temp.txt

REM Read the entire content of the temporary file
set /p DESCRIPTION=<description_temp.txt

REM Remove the temporary file
del description_temp.txt

REM Escape special characters in the description
set "DESCRIPTION=!DESCRIPTION:^=^^!"
set "DESCRIPTION=!DESCRIPTION:&=^&!"
set "DESCRIPTION=!DESCRIPTION:|=^|!"
set "DESCRIPTION=!DESCRIPTION:<=^<!"
set "DESCRIPTION=!DESCRIPTION:>=^>!"
set "DESCRIPTION=!DESCRIPTION:^=^^!"

REM Run the Python script with the provided parameters and get the cost
call poetry run python -c "from main import JobSearchAssistant, USER_CONTEXT_FILE, USER_WANT_FILE; assistant = JobSearchAssistant(USER_CONTEXT_FILE, USER_WANT_FILE); assistant.create_outputs_from_params('%TITLE%', '%COMPANY%', r'%DESCRIPTION%'); print(f'total cost : {assistant.get_cost()} $USD')"

echo.
echo Outputs created successfully!

pause
