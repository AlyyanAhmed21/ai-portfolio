import os
from pathlib import Path
from dotenv import load_dotenv

# This is important! It loads the variables from your .env file
# so os.getenv() can find them.
load_dotenv()

# We need to add the 'app' directory to Python's path
# to be able to import from our app.services module.
import sys
sys.path.append(str(Path(__file__).resolve().parent / 'app'))

from services.data_loader import GoogleDriveLoader

def main():
    """
    Tests the GoogleDriveLoader functionality.
    """
    print("--- Testing Google Drive Loader ---")
    
    # Load the folder ID from the environment variable
    folder_id = os.getenv("GOOGLE_DRIVE_CV_FOLDER_ID")
    
    if not folder_id:
        print("ERROR: GOOGLE_DRIVE_CV_FOLDER_ID not found in .env file.")
        return

    print(f"Using Google Drive Folder ID: {folder_id}")

    try:
        # Initialize our loader
        loader = GoogleDriveLoader(folder_id=folder_id)

        # Define where to save the downloaded CV
        # We'll use the 'backend/data' directory we created
        save_location = Path(__file__).resolve().parent / "data" / "downloaded_cv.pdf"
        
        # Run the download method
        downloaded_path = loader.load_latest_cv(save_path=save_location)

        if downloaded_path and downloaded_path.exists():
            print(f"\nSUCCESS: Test completed. CV is at {downloaded_path}")
        else:
            print("\nFAILURE: Test completed, but file was not downloaded.")

    except Exception as e:
        print(f"\nAn unexpected error occurred during the test: {e}")

if __name__ == "__main__":
    main()