from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse
import requests
import pandas as pd
from pymongo import MongoClient
import logging
from models.IssueEscalation import process_and_escalate_issues
from models.AutomateResponse import generate_automated_response
from models.SentimentAnalysis import get_sentiment

# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client["issue_management"]
issues_collection = db["issues"]

# Zapier Webhook
ZAPIER_WEBHOOK_URL = "https://hooks.zapier.com/hooks/catch/your-webhook-id/"

# Helper functions
def send_to_zapier(data):
    try:
        response = requests.post(ZAPIER_WEBHOOK_URL, json=data)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error sending data to Zapier: {e}")
        raise HTTPException(status_code=500, detail="Failed to send data to Zapier.")

def save_to_mongodb(issue_data):
    try:
        issues_collection.insert_one(issue_data)
        logger.info("Issue saved to MongoDB successfully.")
    except Exception as e:
        logger.error(f"Failed to save issue to MongoDB: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save issue to MongoDB.")

# Input model
class Issue(BaseModel):
    priority: str
    tags: list[str]

@app.get("/issue-escalation/", response_class=PlainTextResponse)
def issue_escalation_endpoint():
    df = pd.read_csv("issues.csv")  # Replace with your actual data source
    escalated_issues = process_and_escalate_issues(df.head(10))

    result = ""
    for issue in escalated_issues.to_dict(orient="records"):
        result += f"Issue ID: {issue.get('issue_id', 'N/A')}\n"
        result += f"Priority: {issue['priority']}\n"
        result += f"Tags: {issue['tags']}\n"
        result += f"Escalated: {'Yes' if issue['escalated'] else 'No'}\n"
        result += f"Escalation Score: {issue['escalation_score']}\n\n"

        send_to_zapier(issue)

    return result

def send_email_via_zapier(email_payload):
    response = requests.post(ZAPIER_WEBHOOK_URL, json=email_payload)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Zapier email failed")
    return response.json()

@app.get("/automated-response/", response_class=PlainTextResponse)
def automated_response_endpoint():
    df = pd.read_csv("issues.csv")
    responses = []
    for _, row in df.head(10).iterrows():
        issue = row.to_dict()
        response = generate_automated_response(issue)
        responses.append(f"Issue ID: {issue.get('issue_id', 'N/A')}\nResponse: {response}\n\n")
        send_to_zapier({"issue_id": issue.get("issue_id", "N/A"), "response": response})

    return "".join(responses)

@app.get("/sentiment-analysis/", response_class=PlainTextResponse)
def sentiment_analysis_endpoint():
    df = pd.read_csv("issues.csv")
    results = []
    for _, row in df.head(10).iterrows():
        sentiment = get_sentiment(row["subject"], row["body"])
        results.append(f"Issue ID: {row.get('issue_id', 'N/A')}\nSentiment: {sentiment}\n\n")
        send_to_zapier({"issue_id": row.get("issue_id", "N/A"), "sentiment": sentiment})

    return "".join(results)

@app.post("/save-issue/", response_class=PlainTextResponse)
def save_issue_endpoint(issue: Issue):
    issue_data = {
        "priority": issue.priority,
        "tags": issue.tags,
        "sentiment": get_sentiment(issue.priority, ", ".join(issue.tags)),
        "automated_response": generate_automated_response(issue.dict()),
        "escalated": False,
        "escalation_score": 0
    }

    save_to_mongodb(issue_data)

    email_payload = {
        "to": "samwathaproject@gmail.com",
        "subject": "Issue Report",
        "message": f"{issue_data}"
    }

    send_email_via_zapier(email_payload)

    return (
        f"Issue processed and saved successfully\n"
        f"Priority: {issue_data['priority']}\n"
        f"Tags: {', '.join(issue_data['tags'])}\n"
        f"Sentiment: {issue_data['sentiment']}\n"
        f"Automated Response: {issue_data['automated_response']}\n"
    )
