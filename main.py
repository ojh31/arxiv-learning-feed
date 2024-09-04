import base64
import os
from datetime import datetime, time, timedelta
from email.message import EmailMessage
from pathlib import Path

import feedparser
import yaml
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from jinja2 import Environment, FileSystemLoader

from scoring import score_entry

ROOT = Path(__file__).parent
# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def get_last_business_day():
    today = datetime.now().date()
    offset = max(1, (today.weekday() + 6) % 7 - 3)
    last_business_day = today - timedelta(days=offset)
    return datetime.combine(last_business_day, time.min)


def get_gmail_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when authorization completes for the first time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                ROOT / "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(ROOT / "token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def send_message(service, message):
    try:
        message = service.users().messages().send(userId="me", body=message).execute()
        print(f'Message Id: {message["id"]}')
        return message
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


def create_message(sender, to, subject, html_content):
    message = EmailMessage()
    message.set_content(html_content, subtype="html")
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return {"raw": raw_message}


def create_content(config: dict) -> str:
    # Parse the arXiv feed
    feed = feedparser.parse(config["url"])
    last_business_day = get_last_business_day()
    filtered_entries: list[feedparser.FeedParserDict] = [
        entry
        for entry in feed.entries
        if datetime(*entry.published_parsed[:6]) >= last_business_day
    ]

    # Prepare paper data
    papers = []
    for entry in filtered_entries:
        papers.append(
            {
                "title": entry.title,
                "authors": ", ".join(author.name for author in entry.authors),
                "summary": entry.summary,
                "link": entry.link,
                "score": score_entry(entry, config),
            }
        )
    papers = sorted(papers, key=lambda x: x["score"], reverse=True)
    print(f"Found {len(papers)} papers from {len(feed.entries)} entries")

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(ROOT))
    template = env.get_template("email_template.html")

    # Render the template with our data
    html_content = template.render(papers=papers)
    return html_content


def main():
    # Parse the yaml config
    with open(ROOT / "config.yaml", "r") as file:
        config = yaml.safe_load(file)
        print(config)
    try:
        html_content = create_content(config)
    except Exception as e:
        print(f"An error occurred: {e}")
        html_content = "<h1>An error occurred</h1>"
        html_content += f"<p>{e}</p>"

    # Get Gmail service
    service = get_gmail_service()

    # Create and send the message
    message = create_message(
        config["sender"], config["recipient"], config["subject"], html_content
    )
    send_message(service, message)


if __name__ == "__main__":
    main()
