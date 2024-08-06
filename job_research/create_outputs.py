import os
import sys
from main import JobSearchAssistant

def get_multiline_input(prompt):
    print(prompt)
    print("(Enter your input. Press Ctrl+Z and Enter on a new line to finish.)")
    return sys.stdin.read().strip()

if __name__ == "__main__":
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct paths relative to the current script
    user_context_file = os.path.join(current_dir, "user_context.json")
    user_want_file = os.path.join(current_dir, "user_want.md")

    # Create JobSearchAssistant instance
    assistant = JobSearchAssistant(user_context_file, user_want_file, verbose=True, max_workers=1)

    # Get input from user
    title = input("Enter job title: ")
    company = input("Enter enterprise name: ")
    description = get_multiline_input("Enter job description:")

    # Call create_outputs_from_params
    assistant.create_outputs_from_params(title, company, description)

    print("\nOutputs created successfully. Press Enter to exit.")
    input()
