from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload
import io
from oauth2client.client import OAuth2Credentials
from django.conf import settings
import os


class GoogleDriveOperation:
    
    def __init__(self, client_id, client_secret, src_obj):
        self.notlinked = False

        if src_obj is None:
            self.notlinked = True
            return

        _creds = OAuth2Credentials(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=src_obj.drive_refresh_token,
            access_token=src_obj.drive_access_token,
            token_expiry=src_obj.drive_token_expiry,
            token_uri="https://oauth2.googleapis.com/token",
            user_agent=None
        )

        try:
            self._service = build('drive', 'v3', http=_creds.authorize(Http()))
        except:
            # TODO: REFRESH TOKEN
            self.notlinked = True
            return
        
    def get_all_files_info(self):
        
        """
        Extract all the files infomation
        """
        return self._service.files().list().execute()
    
    def get_file_info(self, file_id):
        
        """
        Extract infomation of the given file_id
        """
        return self._service.files().get(fileId=file_id).execute()
    
    def get_all_folders(self):
        
        """
        Extract all the folder information
        """
        _page_token = None
        return self._service.files().list(q="mimeType='application/vnd.google-apps.folder'",
                                          spaces='drive', fields='nextPageToken, files(id, name)',
                                          pageToken=_page_token).execute()
    
    def files_inside_folder(self, folder_id):
        
        """
        Extract all the files and folder information inside a folder using the given folder_id
        """
        _query = "'{}' in parents and trashed=false".format(folder_id)
        return self._service.files().list(q=_query).execute()
    
    def create(self, name, mime_type, parent=None):
        
        """
        Create folder or file
        
        parent - Id of the parent folder. Default is None
        name - Name of the folder
        mime_type - Type of the file/folder
        """
        
        if parent is None:
            _file_metadata = {
                'name': name,
                'mimeType': mime_type,
            }
        else:
            _file_metadata = {
                'name': name,
                'mimeType': mime_type,
                'parents': [parent]
            }
        
        return self._service.files().create(body=_file_metadata).execute()

    def upload(self, file_p, filename, mime_type="application/octet-stream", parent=None):

        """
        Upload file

        name = Name of the file
        source_location = absolutale location of the file where it is saved
        mime_type - Type of the file/folder
        parent - Id of the parent folder. Default is None
        """

        if parent is None:
                _file_metadata = {
                    'name': filename,
                }
        else:
                _file_metadata = {
                    'name': filename,
                    'parents': [parent]
                }

        # _media = MediaFileUpload(file_p, mimetype=mime_type, resumable=True)
        _media = MediaIoBaseUpload(fd=file_p, mimetype=mime_type, resumable=False)

        return self._service.files().create(body=_file_metadata, media_body=_media, fields='id').execute()

    def move(self, source_id, destination_id):
        
        """
        Move files or folders to the provided location
        source_id - Id of file or folder
        destination_id - Where to move ID of that folder
        """
        
        _file = self._service.files().get(fileId=source_id, fields='parents').execute()
        _previous_parents = ",".join(_file.get('parents'))
        
        _ack = self._service.files().update(fileId=source_id, addParents=destination_id, 
                                            removeParents=_previous_parents, fields='id, parents').execute()
        return _ack
    
    def download(self, file_id, file_info, export_to=None):

        """
        Download the given file_id file.
        file_id - ID of the file
        name - Name of the file
        """
        if export_to:
            export_to = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            _request = self._service.files().export_media(fileId=file_id, mimeType=export_to)
        else:
            _request = self._service.files().get_media(fileId=file_id)

        _fh = io.BytesIO()
        _downloader = MediaIoBaseDownload(_fh, _request)
        _done = False

        print("Starting download")
        while _done is False:
            _status, _done = _downloader.next_chunk()
            print("Download %d%%." % int(_status.progress() * 100))

        _fh.seek(0)

        file_name = os.path.join(settings.BASE_DIR, 'media', file_info['name']+".xlsx")
        with io.open(file_name, "wb") as f:
            _fh.seek(0)
            f.write(_fh.read())

        return _fh

    def delete(self, file_id):
        
        """
        Delete the file given in the file_id
        """
        self._service.files().delete(fileId=file_id).execute()
