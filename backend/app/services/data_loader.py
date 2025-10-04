import os
import io
from pathlib import Path
from github import Github
from langchain.docstore.document import Document
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# --- Configuration ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
GOOGLE_CREDS_PATH = BASE_DIR / "google_credentials.json"
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# --- Google Drive Loader ---
class GoogleDriveLoader:
    def __init__(self, folder_id: str):
        if not folder_id:
            raise ValueError("Google Drive folder ID is required.")
        self.folder_id = folder_id
        self.service = self._authenticate()
    
    def _authenticate(self):
        if not GOOGLE_CREDS_PATH.exists():
            raise FileNotFoundError(f"Google credentials file not found at {GOOGLE_CREDS_PATH}.")
        creds = service_account.Credentials.from_service_account_file(GOOGLE_CREDS_PATH, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        print("Successfully authenticated with Google Drive API.")
        return service

    def load_documents(self, save_dir: Path) -> list[Path]:
        """
        Finds all PDFs and Google Docs in the folder, downloads them, and returns their local paths.
        """
        downloaded_paths = []
        try:
            # Query for both PDFs and Google Docs
            query = f"'{self.folder_id}' in parents and (mimeType='application/pdf' or mimeType='application/vnd.google-apps.document')"
            results = self.service.files().list(q=query, fields="files(id, name, mimeType)").execute()
            items = results.get('files', [])

            if not items:
                print(f"No relevant documents found in Google Drive folder ID: {self.folder_id}")
                return []

            save_dir.mkdir(parents=True, exist_ok=True)

            for item in items:
                file_id = item['id']
                file_name = item['name']
                mime_type = item['mimeType']
                print(f"Found document: '{file_name}'...")

                if mime_type == 'application/pdf':
                    save_path = save_dir / f"{file_id}.pdf"
                    self._download_binary_file(file_id, save_path)
                elif mime_type == 'application/vnd.google-apps.document':
                    save_path = save_dir / f"{file_id}.txt"
                    self._export_google_doc(file_id, save_path)
                
                downloaded_paths.append(save_path)
            
            return downloaded_paths

        except Exception as e:
            print(f"An error occurred while downloading from Google Drive: {e}")
            return []

    def _download_binary_file(self, file_id: str, save_path: Path):
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        with open(save_path, 'wb') as f:
            fh.seek(0)
            f.write(fh.read())
        print(f" -> Saved to '{save_path}'")

    def _export_google_doc(self, file_id: str, save_path: Path):
        request = self.service.files().export_media(fileId=file_id, mimeType='text/plain')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        with open(save_path, 'w', encoding='utf-8') as f:
            fh.seek(0)
            f.write(fh.getvalue().decode())
        print(f" -> Exported and saved to '{save_path}'")


# --- GitHub Loader ---

class GitHubLoader:
    # --- ADDED A WHITELIST OF RELEVANT README SECTIONS ---
    ALLOWED_README_SECTIONS = [
        "features", "key features", "overview", "introduction", "about the project",
        "technology stack", "tech stack", "built with", "technologies used",
        "architecture", "how it works", "project structure"
    ]

    def __init__(self, access_token: str, username: str, self_repo_name: str = None):
        if not access_token or not username:
            raise ValueError("GitHub access token and username are required.")
        self.github = Github(access_token)
        self.username = username
        self.self_repo_name = self_repo_name

    def _parse_readme_for_relevant_content(self, repo) -> str:
        """
        Downloads the README.md, parses it, and extracts content only from
        whitelisted sections.
        """
        try:
            readme_content = repo.get_readme().decoded_content.decode('utf-8')
            relevant_content = []
            
            # Split the README into sections based on '##' headings
            sections = readme_content.split('\n## ')
            
            for section in sections:
                # The first part before any '##' is the main project description
                if '## ' not in readme_content and sections.index(section) == 0:
                    lines = section.split('\n')
                    # Find the first real paragraph (skip title, badges, etc.)
                    for line in lines:
                        if line.strip() and not line.strip().startswith(('#', '[', '!')):
                             relevant_content.append(line.strip())
                             break # Just take the first descriptive paragraph
                    continue

                # For all other sections, check the heading
                section_lines = section.split('\n')
                heading = section_lines[0].strip().lower()

                # Check if the heading is in our whitelist
                if any(allowed in heading for allowed in self.ALLOWED_README_SECTIONS):
                    print(f"    -> Extracting relevant section: '{heading}'")
                    # Join the rest of the lines in the section, stripping extra whitespace
                    content_body = "\n".join(line for line in section_lines[1:] if line.strip())
                    relevant_content.append(f"### {heading.title()}\n{content_body}")

            return "\n\n".join(relevant_content) if relevant_content else ""
        except Exception as e:
            # It's common for repos to not have a README, so we handle this gracefully
            # print(f"    -> Could not process README for {repo.name}: {e}")
            return ""


    def load_repo_data(self) -> list[Document]:
        """
        Fetches public repo data and intelligently parsed README content,
        and formats it into a list of LangChain Documents.
        """
        print(f"Fetching repository data for user '{self.username}' from GitHub...")
        repo_docs = []
        try:
            user = self.github.get_user(self.username)
            for repo in user.get_repos(sort="updated"):
                if not repo.private:
                    print(f"  -> Processing repo: {repo.name}")
                    
                    # Core project info is always included
                    core_info = f"""
                    Repository Name: {repo.name}
                    Description: {repo.description}
                    Primary Language: {repo.language}
                    Topics: {', '.join(repo.get_topics())}
                    """
                    
                    # Intelligently parse the README for additional, high-value context
                    readme_summary = self._parse_readme_for_relevant_content(repo)
                    
                    # Combine core info with the clean README summary
                    full_content = core_info.strip()
                    if readme_summary:
                        full_content += f"\n\n--- Key Information from README ---\n{readme_summary}"

                    doc_metadata = {"source": "github_project", "repo_name": repo.name, "url": repo.html_url}
                    if self.self_repo_name and repo.name == self.self_repo_name:
                        doc_metadata["source"] = "self"
                        print(f"    -> Tagged as self-repository.")

                    repo_docs.append(Document(page_content=full_content, metadata=doc_metadata))
            
            print(f"Successfully fetched and processed data for {len(repo_docs)} public repositories.")
            return repo_docs

        except Exception as e:
            print(f"An error occurred while fetching from GitHub: {e}")
            return []