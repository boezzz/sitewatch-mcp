import os
import io
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pickle
from pathlib import Path

class GoogleDriveConnector:
    """Connect to Google Drive and manage resume files"""
    
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        self.creds = None
        self.service = None
        self.token_file = 'token.pickle'
        self.credentials_file = 'credentials.json'
        
        # Resume file extensions
        self.resume_extensions = ['.pdf', '.docx', '.doc', '.txt']
        
    def authenticate(self) -> bool:
        """Authenticate with Google Drive API"""
        try:
            # Check if we have valid credentials
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    self.creds = pickle.load(token)
            
            # If credentials are invalid or don't exist, get new ones
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        print("❌ Google Drive credentials not found!")
                        print("📋 Please follow these steps:")
                        print("1. Go to https://console.cloud.google.com/")
                        print("2. Create a new project or select existing one")
                        print("3. Enable Google Drive API")
                        print("4. Create credentials (OAuth 2.0 Client ID)")
                        print("5. Download credentials.json and place it in this directory")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    self.creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_file, 'wb') as token:
                    pickle.dump(self.creds, token)
            
            # Build the service
            self.service = build('drive', 'v3', credentials=self.creds)
            print("✅ Successfully authenticated with Google Drive!")
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def list_resume_files(self, folder_name: str = None) -> List[Dict]:
        """List resume files from Google Drive"""
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            # Build query to find resume files
            query_parts = []
            
            # File type filter
            mime_types = [
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
                "text/plain"
            ]
            mime_query = " or ".join([f"mimeType='{mime}'" for mime in mime_types])
            query_parts.append(f"({mime_query})")
            
            # Name filter for resume files
            name_query = " or ".join([
                "name contains 'resume'",
                "name contains 'cv'",
                "name contains 'curriculum'",
                "name contains 'profile'"
            ])
            query_parts.append(f"({name_query})")
            
            # Folder filter
            if folder_name:
                folder_id = self._get_folder_id(folder_name)
                if folder_id:
                    query_parts.append(f"'{folder_id}' in parents")
            
            # Combine all query parts
            query = " and ".join(query_parts)
            
            # Search for files
            results = self.service.files().list(
                q=query,
                pageSize=50,
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, parents)"
            ).execute()
            
            files = results.get('files', [])
            
            if not files:
                print("📁 No resume files found in Google Drive")
                return []
            
            print(f"📄 Found {len(files)} potential resume files:")
            for i, file in enumerate(files, 1):
                size_mb = int(file.get('size', 0)) / (1024 * 1024) if file.get('size') else 0
                print(f"{i}. {file['name']} ({size_mb:.1f} MB)")
            
            return files
            
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return []
    
    def _get_folder_id(self, folder_name: str) -> Optional[str]:
        """Get folder ID by name"""
        try:
            results = self.service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
                fields="files(id, name)"
            ).execute()
            
            folders = results.get('files', [])
            if folders:
                return folders[0]['id']
            
            return None
            
        except Exception as e:
            print(f"❌ Error finding folder: {e}")
            return None
    
    def download_file(self, file_id: str, file_name: str) -> Optional[str]:
        """Download a file from Google Drive"""
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            # Create temp directory if it doesn't exist
            temp_dir = Path("temp_downloads")
            temp_dir.mkdir(exist_ok=True)
            
            # Determine file extension
            file_ext = Path(file_name).suffix.lower()
            if not file_ext:
                # Default to .pdf if no extension
                file_ext = '.pdf'
            
            # Create local file path
            local_path = temp_dir / f"resume_{file_id}{file_ext}"
            
            # Download the file
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    print(f"📥 Downloading: {int(status.progress() * 100)}%")
            
            # Save to local file
            with open(local_path, 'wb') as f:
                f.write(fh.getvalue())
            
            print(f"✅ Downloaded: {local_path}")
            return str(local_path)
            
        except Exception as e:
            print(f"❌ Error downloading file: {e}")
            return None
    
    def search_resumes_by_keywords(self, keywords: List[str]) -> List[Dict]:
        """Search for resume files using keywords"""
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            # Build search query with keywords
            keyword_query = " or ".join([f"name contains '{keyword}'" for keyword in keywords])
            
            # File type filter
            mime_types = [
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
                "text/plain"
            ]
            mime_query = " or ".join([f"mimeType='{mime}'" for mime in mime_types])
            
            # Combine queries
            query = f"({keyword_query}) and ({mime_query})"
            
            results = self.service.files().list(
                q=query,
                pageSize=20,
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            print(f"❌ Error searching files: {e}")
            return []
    
    def get_recent_resumes(self, days: int = 30) -> List[Dict]:
        """Get recently modified resume files"""
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            from datetime import datetime, timedelta
            
            # Calculate date threshold
            threshold_date = (datetime.now() - timedelta(days=days)).isoformat() + 'Z'
            
            # File type filter
            mime_types = [
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
                "text/plain"
            ]
            mime_query = " or ".join([f"mimeType='{mime}'" for mime in mime_types])
            
            # Build query
            query = f"({mime_query}) and modifiedTime > '{threshold_date}'"
            
            results = self.service.files().list(
                q=query,
                pageSize=20,
                orderBy="modifiedTime desc",
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            print(f"❌ Error getting recent files: {e}")
            return []
    
    def cleanup_temp_files(self):
        """Clean up temporary downloaded files"""
        try:
            temp_dir = Path("temp_downloads")
            if temp_dir.exists():
                for file in temp_dir.glob("*"):
                    file.unlink()
                temp_dir.rmdir()
                print("🧹 Cleaned up temporary files")
        except Exception as e:
            print(f"⚠️ Could not clean up temp files: {e}")

def setup_google_drive():
    """Setup instructions for Google Drive integration"""
    print("🔧 Google Drive Setup Instructions:")
    print("=" * 50)
    print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
    print("2. Create a new project or select an existing one")
    print("3. Enable the Google Drive API:")
    print("   - Go to 'APIs & Services' > 'Library'")
    print("   - Search for 'Google Drive API'")
    print("   - Click 'Enable'")
    print("4. Create credentials:")
    print("   - Go to 'APIs & Services' > 'Credentials'")
    print("   - Click 'Create Credentials' > 'OAuth 2.0 Client IDs'")
    print("   - Choose 'Desktop application'")
    print("   - Download the JSON file")
    print("5. Rename the downloaded file to 'credentials.json'")
    print("6. Place it in this project directory")
    print("7. Run the application - it will open a browser for authentication")
    print("=" * 50) 