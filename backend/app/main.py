import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.v1.endpoints import chat
from app.services.data_loader import GoogleDriveLoader, GitHubLoader
from app.services.rag_service import rag_service_instance
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- Application Startup: Initializing Knowledge Base ---")
    personal_documents = []
    project_documents = []

    # --- Step 1: Load data from Google Drive (for Personal Info) ---
    print("\n[Phase 1/3] Loading personal documents from Google Drive...")
    folder_id = os.getenv("GOOGLE_DRIVE_CV_FOLDER_ID")
    if folder_id:
        # ... (same loading logic as before)
        gdrive_loader = GoogleDriveLoader(folder_id=folder_id)
        local_doc_paths = gdrive_loader.load_documents(save_dir=DATA_DIR)
        for path in local_doc_paths:
            if path.suffix == ".pdf": loader = PyMuPDFLoader(str(path))
            elif path.suffix == ".txt": loader = TextLoader(str(path), encoding='utf-8')
            else: continue
            personal_documents.extend(loader.load())
    
    # --- Step 2: Load data from GitHub (for Project Info) ---
    print("\n[Phase 2/3] Loading project documents from GitHub...")
    github_token = os.getenv("GITHUB_ACCESS_TOKEN")
    github_user = os.getenv("GITHUB_USERNAME")
    self_repo = os.getenv("SELF_REPO_NAME")
    if github_token and github_user:
        github_loader = GitHubLoader(access_token=github_token, username=github_user, self_repo_name=self_repo)
        github_docs = github_loader.load_repo_data()
        # Separate the "self" repo to be with personal info
        for doc in github_docs:
            if doc.metadata.get("source") == "self":
                personal_documents.append(doc)
            else:
                project_documents.append(doc)

    # --- Step 3: Build the separate RAG knowledge bases ---
    print("\n[Phase 3/3] Building the RAG knowledge bases...")
    rag_service_instance.build_knowledge_bases(
        personal_docs=personal_documents, 
        project_docs=project_documents
    )
            
    yield
    print("\n--- Application Shutdown ---")


app = FastAPI(title="AI Portfolio Assistant API", version="1.0.0", lifespan=lifespan)
app.include_router(chat.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome! Go to /docs for the API documentation."}