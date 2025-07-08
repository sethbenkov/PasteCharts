import os
import base64
import uuid
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class SlidesHandler:
    SCOPES = ['https://www.googleapis.com/auth/presentations']

    def __init__(self, slides_id, client_secret_file):
        self.slides_id = slides_id
        self.creds = self._get_credentials(client_secret_file)
        self.service = build('slides', 'v1', credentials=self.creds)

    def _get_credentials(self, client_secret_file):
        creds = None
        token_path = 'token.json'
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secret_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        return creds

    def paste_image(self, image_path, page_number, position, size):
        """
        Pastes an image to a specific location on a slide.
        """
        try:
            # Get the presentation to find the correct page object ID
            presentation = self.service.presentations().get(presentationId=self.slides_id).execute()
            pages = presentation.get('slides', [])
            
            if not (0 < page_number <= len(pages)):
                print(f"Error: Page number {page_number} is out of range.")
                return

            page_object_id = pages[page_number - 1].get('objectId')

            # Encode the image to a base64 data URL
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            data_url = f'data:image/png;base64,{encoded_string}'

            # Generate a unique ID for the image object
            image_id = str(uuid.uuid4())

            # Define image properties
            image_properties = {
                'pageObjectId': page_object_id,
                'size': {
                    'height': {'magnitude': size['height'], 'unit': 'PT'},
                    'width': {'magnitude': size['width'], 'unit': 'PT'}
                },
                'transform': {
                    'scaleX': 1,
                    'scaleY': 1,
                    'translateX': position['x'],
                    'translateY': position['y'],
                    'unit': 'PT'
                }
            }

            # Create the request
            requests = [
                {
                    'createImage': {
                        'objectId': image_id,
                        'url': data_url,
                        'elementProperties': image_properties
                    }
                }
            ]

            body = {'requests': requests}
            response = self.service.presentations().batchUpdate(
                presentationId=self.slides_id,
                body=body).execute()
            
            print(f"Successfully pasted image {image_path} to slide {page_number}.")
            
        except HttpError as err:
            print(f"Error pasting image: {err}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
