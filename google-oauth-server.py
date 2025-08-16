import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/contacts.readonly", "https://www.googleapis.com/auth/calendar.readonly"]


def main():
  """Shows basic usage of the People API.
  Prints the name of the first 10 connections.
  """
  creds = None
  if os.path.exists(os.getenv("GOOGLE_TOKEN_FILE")):
    creds = Credentials.from_authorized_user_file(os.getenv("GOOGLE_TOKEN_FILE"), SCOPES)

  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          os.getenv("GOOGLE_CLIENT_SECRET_FILE"), 
          SCOPES,
          redirect_uri='http://localhost:8080'
      )
      creds = flow.run_local_server(port=8080, redirect_uri_trailing_slash=False)
    with open(os.getenv("GOOGLE_TOKEN_FILE"), "w") as token:
      token.write(creds.to_json())

  try:
    service = build("people", "v1", credentials=creds)

    # Call the People API
    print("List 10 connection names")
    results = (
        service.people()
        .connections()
        .list(
            resourceName="people/me",
            pageSize=10,
            personFields="names,emailAddresses",
        )
        .execute()
    )
    connections = results.get("connections", [])

    for person in connections:
      names = person.get("names", [])
      if names:
        name = names[0].get("displayName")
        print(name)
  except HttpError as err:
    print(err)


if __name__ == "__main__":
  main()