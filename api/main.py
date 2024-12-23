import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import qrcode
import base64
from io import BytesIO
import requests
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

app = FastAPI()

# CORS middleware to allow communication with frontend
origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,  
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GitHub API Configuration
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")
REPO_OWNER = os.getenv("mounamahfd")  # Your GitHub username
REPO_NAME = "qr-codes-repo"  # Name of the repository you created
BRANCH_NAME = "main"  # The branch where you'll store the QR codes
COMMITTER_NAME = "GitHub Actions"
COMMITTER_EMAIL = "github-actions@github.com"

# GitHub API URL to commit files to repository
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents"

# Define the input model for FastAPI to handle the URL
class QRRequest(BaseModel):
    url: str
    
def upload_to_github(file_name, image_data):
    # GitHub API URL to check for file existence in a repository
    url = f"{GITHUB_API_URL}/{file_name}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    # Get the current file content (if any) to create a new commit
    response = requests.get(url, headers=headers)

    if response.status_code == 404:
        # Directory doesn't exist, so we will attempt to create it by adding a .gitkeep file
        print("Directory doesn't exist, creating it now.")
        
        # Create a temporary file in the qr_codes directory to create the directory on GitHub
        temp_file_name = "qr_codes/.gitkeep"  # Using .gitkeep to create the directory
        commit_data = {
            "message": "Create qr_codes directory",
            "content": base64.b64encode(b"").decode("utf-8"),  # Empty content for the .gitkeep file
            "branch": BRANCH_NAME,
        }

        # Attempt to create the directory by uploading a .gitkeep file
        response = requests.put(f"{GITHUB_API_URL}/{temp_file_name}", headers=headers, json=commit_data)

        if response.status_code != 200 and response.status_code != 201:
            print(f"Error creating directory in GitHub: {response.text}")
            raise Exception(f"Error creating directory in GitHub: {response.text}")

        print("Directory created successfully.")
    
    # Now proceed to upload the actual QR code image
    commit_data = {
        "message": f"Add QR code for {file_name}",
        "content": image_data,
        "branch": BRANCH_NAME,
    }

    # Make the actual file upload request
    response = requests.put(url, headers=headers, json=commit_data)

    if response.status_code != 200 and response.status_code != 201:
        print(f"Error uploading file to GitHub: {response.text}")
        raise Exception(f"Error uploading file to GitHub: {response.text}")

    return f"https://{REPO_OWNER}.github.io/{REPO_NAME}/{file_name}"



# Function to check if the URL is valid using regular expressions
def is_valid_url(url: str) -> bool:
    parsed_url = urlparse(url)
    # Regular expression to validate URL format
    return bool(parsed_url.netloc) and bool(parsed_url.scheme) and re.match(r'^[a-zA-Z0-9.-]+$', parsed_url.netloc)

# Function to sanitize the URL and generate a safe file name
def sanitize_url(url: str) -> str:
    """
    Sanitize the URL to create a valid file name by removing invalid characters
    and replacing them with valid ones.
    """
    # Remove 'http://' or 'https://'
    sanitized_url = url.split('//')[-1]
    
    # Replace all non-alphanumeric characters (except for dots and hyphens) with underscores
    sanitized_url = re.sub(r'[^a-zA-Z0-9.-]', '_', sanitized_url)
    
    # Remove trailing slash if exists
    sanitized_url = sanitized_url.rstrip('/')
    
    return sanitized_url

@app.post("/generate-qr/")
async def generate_qr(request: QRRequest):
    # Debug: Log the URL received
    print(f"Received URL: {request.url}")

    try:
        if not is_valid_url(request.url):
            raise HTTPException(status_code=400, detail="Invalid URL")

        # Sanitize the URL to ensure it forms a valid file name
        sanitized_url = sanitize_url(request.url)

        # Create the file name with sanitized URL
        file_name = f"qr_codes/{sanitized_url}.png"

        # Debug: Log the file name
        print(f"Generated file name: {file_name}")

        # Generate QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(request.url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Save QR Code to BytesIO object
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        # Convert the image to base64 to upload to GitHub
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

        # Upload to GitHub
        github_url = upload_to_github(file_name, img_base64)

        return {"qr_code_url": github_url}
    
    except Exception as e:
        # Log the exception for better debugging
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
