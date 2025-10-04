import os
from pathlib import Path

# The root directory of the project
ROOT_DIR = Path(__file__).parent

# Define the file and folder structure
STRUCTURE = {
    "backend": {
        "app": {
            "api": {
                "v1": {
                    "__init__.py": None,
                    "endpoints": {
                        "__init__.py": None,
                        "chat.py": "# API endpoint for the chatbot"
                    }
                }
            },
            "core": {
                "__init__.py": None,
                "config.py": "# Configuration settings"
            },
            "services": {
                "__init__.py": None,
                "data_loader.py": "# Logic for fetching data from sources",
                "llm_service.py": "# Logic for interacting with the LLM",
                "rag_service.py": "# Core RAG pipeline logic"
            },
            "schemas": {
                "__init__.py": None,
                "chat_schemas.py": "# Pydantic schemas for API I/O"
            },
            "__init__.py": None,
            "main.py": "# FastAPI application entry point"
        },
        "data": {
            ".gitkeep": ""
        },
        ".env": "GOOGLE_API_KEY=\n",
        ".gitignore": "# Python gitignore content\n__pycache__/\n*.pyc\n.env\nvenv/\ndata/",
        "requirements.txt": "fastapi\nuvicorn[standard]\npython-dotenv\n"
    },
    "frontend": {
        # We will initialize the Next.js app separately,
        # but we can create placeholders for key files/dirs.
        "public": {".gitkeep": ""},
        "src": {
            "app": {".gitkeep": ""},
            "components": {
                "ui": {
                     "Chatbot.tsx": "// New component for the AI chat interface"
                }
            },
            "data": {".gitkeep": ""}
        },
    },
    "README.md": "# AI-Powered Personal Portfolio"
}

def create_structure(base_path, structure_dict):
    """Recursively creates files and folders."""
    for name, content in structure_dict.items():
        current_path = base_path / name
        if isinstance(content, dict):
            print(f"Creating directory: {current_path}")
            current_path.mkdir(parents=True, exist_ok=True)
            create_structure(current_path, content)
        else:
            if not current_path.exists():
                print(f"Creating file: {current_path}")
                with open(current_path, "w") as f:
                    if content is not None:
                        f.write(content + "\n")

if __name__ == "__main__":
    print("Setting up project structure...")
    create_structure(ROOT_DIR, STRUCTURE)
    print("\nProject structure created successfully!")
    print("Next steps:")
    print("1. Set up the Next.js frontend in the 'frontend' directory.")
    print("2. Set up a Python virtual environment in the 'backend' directory and run 'pip install -r requirements.txt'.")