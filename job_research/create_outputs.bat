import os
import subprocess
import sys

def run_poetry_command(command):
    try:
        result = subprocess.run(f"poetry {command}", shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running poetry command: {e}")
        return None

def main():
    # Ensure we're using the correct Python environment
    run_poetry_command("env use python")

    # Prompt user for input
    title = input("Enter job title: ")
    company = input("Enter company name: ")
    print("Enter job description (Press Enter twice when finished):")
    
    description = []
    while True:
        line = input()
        if line == "":
            break
        description.append(line)
    description = "\n".join(description)

    # Run the Python script with the provided parameters and get the cost
    command = f'''run python -c "from main import JobSearchAssistant, USER_CONTEXT_FILE, USER_WANT_FILE; assistant = JobSearchAssistant(USER_CONTEXT_FILE, USER_WANT_FILE); assistant.create_outputs_from_params('{title}', '{company}', r'''{description}'''); print(f'total cost : {{assistant.get_cost()}} $USD')"'''
    
    result = run_poetry_command(command)
    
    if result:
        print("\nOutputs created successfully!")
    else:
        print("\nFailed to create outputs.")

    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
