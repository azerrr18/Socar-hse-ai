#First, download the dataset
import torch
import urllib.request
import zipfile
import os

zip_url = "https://github.com/ultralytics/assets/releases/download/v0.0.0/construction-ppe.zip"
folder = "Security"
zip_path = os.path.join(folder, "Security/construction-ppe.zip")

#create folder if doesn't exis
os.makedirs(folder, exist_ok=True)
if not os.path.exists(zip_path):
    urllib.request.urlretrieve(zip_url, zip_path)
    print("Downloaded dataset")
else:
    print("Dataset already exists")
extract_marker = os.path.join(folder,"construction-ppe")
if not os.path.exists(extract_marker):
    print("Extracting dataset")
    with zipfile.ZipFile(zip_path,'r') as zip_ref:
        zip_ref.extractall(folder)
    print("Done")
else:
    print("Dataset already extracted")

print(f"files in {folder}:")





