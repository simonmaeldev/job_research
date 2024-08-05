import tkinter as tk
from tkinter import messagebox
from main import JobSearchAssistant, USER_CONTEXT_FILE, USER_WANT_FILE

def create_outputs():
    title = title_entry.get()
    company = company_entry.get()
    description = description_text.get("1.0", tk.END).strip()

    if not title or not company or not description:
        messagebox.showerror("Error", "All fields are required!")
        return

    assistant = JobSearchAssistant(USER_CONTEXT_FILE, USER_WANT_FILE)
    assistant.create_outputs_from_params(title, company, description)
    messagebox.showinfo("Success", f"Outputs created for job '{title}' at '{company}'")

# Create the main window
root = tk.Tk()
root.title("Create Resume and Cover Letter")

# Create and pack the input fields
tk.Label(root, text="Job Title:").pack()
title_entry = tk.Entry(root, width=50)
title_entry.pack()

tk.Label(root, text="Company:").pack()
company_entry = tk.Entry(root, width=50)
company_entry.pack()

tk.Label(root, text="Job Description:").pack()
description_text = tk.Text(root, width=50, height=10)
description_text.pack()

# Create and pack the submit button
submit_button = tk.Button(root, text="Create Outputs", command=create_outputs)
submit_button.pack()

# Start the GUI event loop
root.mainloop()
