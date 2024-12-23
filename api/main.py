from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import qrcode
import requests
import os
import base64
from io import BytesIO
from dotenv import load_dotenv

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

# Helper function to upload image to GitHub
def upload_to_github(file_name, image_data):
    url = f"{GITHUB_API_URL}/{file_name}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    # Get the current file content (if any) to create a new commit
    response = requests.get(url, headers=headers)
    sha = response.json().get("sha", None)  # Retrieve the sha if file exists

    # Prepare the commit data
    commit_data = {
        "message": f"Add QR code for {file_name}",
        "content": image_data,
        "branch": BRANCH_NAME,
    }

    if sha:
        commit_data["sha"] = sha

    response = requests.put(url, headers=headers, json=commit_data)

    if response.status_code != 201 and response.status_code != 200:
        raise Exception(f"Error uploading file to GitHub: {response.text}")

    return f"https://{REPO_OWNER}.github.io/{REPO_NAME}/{file_name}"
@app.post("/generate-qr/")
async def generate_qr(url: str):
    # Validate URL format
    if not url.startswith("http://") and not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid URL. Please provide a URL starting with http:// or https://")
    
    try:
        # QR code generation logic
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        file_name = f"qr_codes/{url.split('//')[-1]}.png"

        # Upload to GitHub
        github_url = upload_to_github(file_name, img_base64)
        
        return {"qr_code_url": github_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
