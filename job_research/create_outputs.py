import os
import sys
import subprocess

def get_multiline_input(prompt):
    print(prompt)
    print("(Enter your input. Press Ctrl+Z and Enter on a new line to finish.)")
    return sys.stdin.read().strip()

if __name__ == "__main__":
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Activate the virtual environment using Poetry
    activate_command = ["poetry", "run", "python", "-c", "import sys; print(sys.executable)"]
    result = subprocess.run(activate_command, capture_output=True, text=True, cwd=current_dir)
    
    if result.returncode != 0:
        print("Error activating virtual environment. Make sure Poetry is installed and configured correctly.")
        print(result.stderr)
        input("Press Enter to exit...")
        sys.exit(1)

    python_executable = result.stdout.strip()

    # Run the main script using the activated environment
    main_script = [
        python_executable,
        "-c",
        f"""
import os
import sys
from main import JobSearchAssistant

current_dir = {repr(current_dir)}
user_context_file = os.path.join(current_dir, "user_context.json")
user_want_file = os.path.join(current_dir, "user_want.md")

assistant = JobSearchAssistant(user_context_file, user_want_file, verbose=True, max_workers=1)

title = input("Enter job title: ")
company = input("Enter enterprise name: ")
print("Enter job description:")
print("(Enter your input. Press Ctrl+Z and Enter on a new line to finish.)")
description = sys.stdin.read().strip()

assistant.create_outputs_from_params(title, company, description)

print("\\nOutputs created successfully. Press Enter to exit.")
input()
        """
    ]

    subprocess.run(main_script, cwd=current_dir)
