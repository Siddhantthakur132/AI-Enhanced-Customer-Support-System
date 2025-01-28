import gradio as gr
import requests

BASE_URL = "http://127.0.0.1:8000"  # Update with your FastAPI server's base URL

# Function to call the Save Issue endpoint
def save_issue(priority, tags):
    try:
        payload = {
            "priority": priority,
            "tags": [tag.strip() for tag in tags.split(",")],
        }
        response = requests.post(f"{BASE_URL}/save-issue/", json=payload)
        if response.status_code == 200:
            return response.text
        else:
            return f"Error: {response.text}"
    except Exception as e:
        return f"Error saving issue: {str(e)}"

# Gradio Interface
with gr.Blocks() as app:
    gr.Markdown("# Save Issue Dashboard")
    gr.Markdown("Enter the priority and tags to save a new issue.")

    issue_priority = gr.Textbox(label="Priority", placeholder="Enter issue priority (e.g., High, Medium, Low)")
    issue_tags = gr.Textbox(label="Tags", placeholder="Enter tags separated by commas (e.g., bug, UI, backend)")
    save_output = gr.Textbox(label="Save Issue Result", lines=10)
    
    save_btn = gr.Button("Save Issue")
    save_btn.click(save_issue, inputs=[issue_priority, issue_tags], outputs=save_output)

# Run the Gradio app
app.launch(server_name="127.0.0.1", server_port=7860)
