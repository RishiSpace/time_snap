import os
import requests
import zipfile
import subprocess
import sys

def download_tesseract():
    url = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w32-setup-v4.00.00.exe"
    local_filename = "tesseract-ocr-w32-setup-v4.00.00.exe"
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename

def install_tesseract(installer_path):
    subprocess.run([installer_path, '/S'], check=True)
    os.remove(installer_path)

def add_tesseract_to_path():
    tesseract_path = r"C:\Program Files\Tesseract-OCR"
    if tesseract_path not in os.environ['PATH']:
        os.environ['PATH'] += os.pathsep + tesseract_path
        with open(os.path.expanduser("~/.bashrc"), "a") as f:
            f.write(f'\nexport PATH=$PATH:{tesseract_path}')
        subprocess.run(['setx', 'PATH', os.environ['PATH']], check=True)

if __name__ == "__main__":
    installer_path = download_tesseract()
    install_tesseract(installer_path)
    add_tesseract_to_path()
