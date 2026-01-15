import os
import requests
import zipfile
from io import BytesIO


GITHUB_RELEASE_URL = "xxx"  
DESTINATION_FOLDER = "./data" # save the results folder inside the "data" folder (data/results).
os.makedirs(DESTINATION_FOLDER, exist_ok=True)

print("Downloading pre-computed results...")
response = requests.get(GITHUB_RELEASE_URL, stream=True)

if response.status_code == 200:
    print("Download complete. Extracting files...")
    with zipfile.ZipFile(BytesIO(response.content), 'r') as zip_ref:
        zip_ref.extractall(DESTINATION_FOLDER)
    
    print(f"Files extracted to: {DESTINATION_FOLDER}")
else:
    print(f"Failed to download file. HTTP Status Code: {response.status_code}")