from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import pickle
import os

class GoogleDriveManager:
    """
    Manages Google Drive operations for the certificate generator.
    """
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, credentials_path='credentials.json', token_path='token.pickle'):
        """
        Initialize the Google Drive manager with credentials.
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = None
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Handle the authentication flow with Google Drive API."""
        try:
            if os.path.exists(self.token_path):
                with open(self.token_path, 'rb') as token:
                    self.creds = pickle.load(token)
            
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES)
                    self.creds = flow.run_local_server(port=8080)
                
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.creds, token)
            
            self.service = build('drive', 'v3', credentials=self.creds)
        
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            raise
    
    def create_folder(self, folder_name):
        """
        Create a folder in Google Drive.
        
        Args:
            folder_name (str): Name of the folder to create
            
        Returns:
            str: ID of the created folder
        """
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            file = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            # Set folder permissions to anyone with the link can view
            self.service.permissions().create(
                fileId=file.get('id'),
                body={
                    'type': 'anyone',
                    'role': 'reader'
                }
            ).execute()
            
            return file.get('id')
        
        except Exception as e:
            print(f"Error creating folder: {str(e)}")
            raise
    
    def upload_file(self, file_name, file_stream, mime_type, folder_id):
        """
        Upload a file to Google Drive.
        
        Args:
            file_name (str): Name of the file to create in Drive
            file_stream (io.BytesIO): File stream containing the file data
            mime_type (str): MIME type of the file
            folder_id (str): ID of the folder to upload to
            
        Returns:
            str: Shareable link to the uploaded file
        """
        try:
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            
            media = MediaIoBaseUpload(
                file_stream,
                mimetype=mime_type,
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink',
            ).execute()
            
            # Set file permissions to anyone with the link can view
            self.service.permissions().create(
                fileId=file.get('id'),
                body={
                    'type': 'anyone',
                    'role': 'reader'
                }
            ).execute()
            
            return file.get('webViewLink')
        
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            raise