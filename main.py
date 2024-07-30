import base64
import os
from email.message import EmailMessage

import feedparser
import yaml
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from jinja2 import Environment, FileSystemLoader

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


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
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
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


def main():
    # Parse the yaml config
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
        print(config)

    # Parse the arXiv feed
    feed = feedparser.parse(config["url"])

    # Prepare paper data
    papers = []
    for entry in feed.entries:
        papers.append(
            {
                "title": entry.title,
                "authors": ", ".join(author.name for author in entry.authors),
                "summary": entry.summary,
                "link": entry.link,
            }
        )

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("email_template.html")

    # Render the template with our data
    html_content = template.render(papers=papers)

    # Get Gmail service
    service = get_gmail_service()

    # Create and send the message
    message = create_message(
        config["sender"], config["recipient"], config["subject"], html_content
    )
    send_message(service, message)


if __name__ == "__main__":
    main()
