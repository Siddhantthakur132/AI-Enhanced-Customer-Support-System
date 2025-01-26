import re
import pandas as pd
from collections import Counter

# Function to read Google Sheets
def read_google_sheet():
    import gspread
    api_key = "AIzaSyDNcV0rmf7yr5hrgJIzwQQEX5B5GhFMA4A"
    sheet_id = "1955249M_RUnbomqFcGOMJDnxrtwjQpfXFdvDUt5GsAw"
    gc = gspread.api_key(api_key)
    sh = gc.open_by_key(sheet_id)
    worksheet = sh.sheet1
    data = worksheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    return df

# Preprocessing the dataset
def count_tags(df_en):
    return len(df_en['tags'])

# Issue Escalation Logic
def should_escalate(incoming_issue):
    if incoming_issue["priority"] == "high":
        tags_combined = " ".join([incoming_issue[f"tag_{i+1}"] for i in range(9)])
        keywords = ["Disruption", "urgent", "issue", "refund", "Failure", "Outage", "Incident", "Crash", "Breach", "Critical"]
        for key in keywords:
            if re.search(r'\b' + re.escape(key.lower()) + r'\b', tags_combined.lower()):
                return True
    return False

def adjust_priority_based_on_severity(incoming_issue):
    severity_keywords = ["Critical", "Emergency", "High"]
    tags_combined = " ".join([incoming_issue[f"tag_{i+1}"] for i in range(9)])
    if any(kw.lower() in tags_combined.lower() for kw in severity_keywords):
        if incoming_issue["priority"] == "medium":
            incoming_issue["priority"] = "high"
    return incoming_issue

def escalation_score(incoming_issue):
    tags_combined = " ".join(incoming_issue["tags"])
    score = sum(1 for key in ["Disruption", "Failure", "Outage", "Incident", "Urgent"] if key.lower() in tags_combined.lower())
    return score

def process_and_escalate_issues(df):
    escalated_rows = []
    for index, row in df.iterrows():
        issue = row.to_dict()
        if should_escalate(issue):
            issue["escalated"] = True
            issue = adjust_priority_based_on_severity(issue)
            issue["escalation_score"] = escalation_score(issue)
        else:
            issue["escalated"] = False
            issue["escalation_score"] = escalation_score(issue)
        escalated_rows.append(issue)

    return pd.DataFrame(escalated_rows)
