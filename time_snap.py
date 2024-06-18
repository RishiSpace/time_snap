import pyautogui
import pytesseract
from PIL import ImageGrab, Image, ImageTk
import customtkinter as ctk
from datetime import datetime
import spacy
import threading
import time
import os
import re
import sys
import sqlite3
from io import BytesIO

# Global Variables
db_path = "screenshot_monitor.db"
images = []  # Store paths to all screenshots in the form of IDs
stop_thread = False

# Define OCR engine path
pytesseract.pytesseract.tesseract_cmd = r"D:\Program Files\Tesseract-OCR\tesseract.exe"  # Update path if needed

# Load spaCy model for NER
nlp = spacy.load("en_core_web_sm")

# Create SQLite database and tables if they don't exist
def initialize_database():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS screenshots (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            image BLOB,
            ocr_text TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_screenshot_to_db(screenshot, timestamp, ocr_text):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    img_byte_arr = BytesIO()
    screenshot.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    c.execute('''
        INSERT INTO screenshots (timestamp, image, ocr_text) 
        VALUES (?, ?, ?)
    ''', (timestamp, img_byte_arr, ocr_text))
    conn.commit()
    images.append(c.lastrowid)
    conn.close()

def take_screenshot():
    global images
    # Capture screenshot and extract timestamp
    screenshot = ImageGrab.grab()
    timestamp = str(datetime.now()).replace(":", "-")

    # Perform OCR
    text = pytesseract.image_to_string(screenshot)

    # Save screenshot and OCR text to database
    save_screenshot_to_db(screenshot, timestamp, text)

def capture_screenshots():
    while not stop_thread:
        take_screenshot()
        time.sleep(5)  # Delay between captures

def on_closing():
    global stop_thread
    stop_thread = True
    root.destroy()
    sys.exit()

# Create the GUI
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.title("Time Snap GUI")
root.protocol("WM_DELETE_WINDOW", on_closing)

# Slider for image navigation
slider = ctk.CTkSlider(root, from_=0, to=100, orientation='horizontal')
slider.pack(pady=10)

# Label to display screenshot
image_label = ctk.CTkLabel(root)
image_label.pack(pady=10)

def update_image(index):
    if images:
        index = int(index) % len(images)
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT image FROM screenshots WHERE id=?', (images[index],))
        img_data = c.fetchone()[0]
        conn.close()
        img = Image.open(BytesIO(img_data))
        img = img.resize((600, 400), Image.LANCZOS)
        img = ImageTk.PhotoImage(img)
        image_label.configure(image=img)
        image_label.image = img

slider.configure(command=lambda x: update_image(slider.get()))

# Search bar and button
search_bar = ctk.CTkEntry(root, placeholder_text="Enter keyword to search")
search_bar.pack(pady=10)

def search_button_command():
    keyword = search_bar.get()
    if keyword:
        search_text(keyword)

search_button = ctk.CTkButton(root, text="Search", command=search_button_command)
search_button.pack(pady=10)

def search_text(keyword):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        SELECT id, timestamp, ocr_text FROM screenshots WHERE ocr_text LIKE ?
    ''', ('%' + keyword + '%',))
    matches = c.fetchall()
    conn.close()

    if matches:
        screenshot_id, timestamp, ocr_text = matches[0]

        # Convert screenshot_id to integer (since it should be integer)
        screenshot_id = int(screenshot_id)

        # Find the index of screenshot_id in images
        try:
            index = images.index(screenshot_id)
        except ValueError:
            # Handle case where screenshot_id is not found in images
            # For example, display a message or default image
            return

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT image FROM screenshots WHERE id=?', (screenshot_id,))
        img_data = c.fetchone()[0]
        conn.close()
        img = Image.open(BytesIO(img_data))
        img = img.resize((600, 400), Image.LANCZOS)
        img = ImageTk.PhotoImage(img)
        image_label.configure(image=img)
        image_label.image = img
        # Update slider to point to the correct image
        slider.set(index)
    else:
        # Handle case where no matches are found
        # For example, display a message or default image
        pass


# Initialize the database
initialize_database()

# Start the screenshot capture thread
thread = threading.Thread(target=capture_screenshots)
thread.start()

root.mainloop()
