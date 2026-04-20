import streamlit as st
from PIL import Image
import pytesseract
import re

st.title("Estoppel Screenshot To-Do Checker")

uploaded_file = st.file_uploader("Upload Screenshot", type=["png", "jpg", "jpeg"])


# 🔍 Extract file number
def extract_file_number(text):
    match = re.search(r"#\d{2}-\d+", text)
    return match.group() if match else "Unknown File"


# 🧠 Core logic: smarter To-Do generator
def generate_todo(address):
    todos = []
    address_clean = address.strip()

    # --- Abbreviation rules (SPECIFIC - highest priority) ---
    abbreviations = {
        "CT": "Court",
        "PL": "Place",
        "RD": "Road",
        "ST": "Street",
        "DR": "Drive",
        "LN": "Lane",
        "BLVD": "Boulevard",
        "AVE": "Avenue",
        "CIR": "Circle"
    }

    found_abbreviations = set()

    for abbr, full in abbreviations.items():
        if re.search(rf"\b{abbr}\b", address_clean, re.IGNORECASE):
            todos.append(f"Spell out {full}")
            found_abbreviations.add(abbr)

    # --- State rule (SPECIFIC) ---
    if re.search(r"\bFL\b", address_clean):
        todos.append("Spell out Florida")

    # --- Casing rule (GENERAL - but smarter) ---
    words = re.findall(r"\b[A-Z]{3,}\b", address_clean)

    # Remove abbreviations from casing check
    words = [w for w in words if w not in found_abbreviations and w != "FL"]

    if words:
        todos.append("Fix casing (use Title Case)")

    # --- Direction rule ---
    if re.search(r"\b(nw|ne|sw|se|n|s|e|w)\b", address_clean, re.IGNORECASE):
        todos.append("Ensure directions (N, S, E, W) are uppercase")

    # --- Cleanup rules ---
    if "  " in address_clean:
        todos.append("Remove extra spaces")

    if ",," in address_clean:
        todos.append("Fix commas")

    return list(set(todos))  # remove duplicates safely


# ⚡ Cache OCR to prevent timeouts
@st.cache_data(show_spinner=True)
def run_ocr(image):
    return pytesseract.image_to_string(image)


# 🚀 Main app
if uploaded_file:
    image = Image.open(uploaded_file)

    # Optional: resize for faster OCR
    image = image.resize((1200, 1200))

    st.image(image, caption="Uploaded Screenshot")

    extracted_text = run_ocr(image)
    file_number = extract_file_number(extracted_text)

    st.subheader("To-Do List")

    lines = [line.strip() for line in extracted_text.split("\n") if line.strip()]

    for i, line in enumerate(lines):

        # Detect address-like line
        if re.search(r"\d+", line):

            full_address = line

            # Combine with next line if zip present
            if i + 1 < len(lines) and re.search(r"\d{5}", lines[i + 1]):
                full_address += f" {lines[i + 1]}"

            todos = generate_todo(full_address)

            if todos:
                st.markdown(f"### 📁 {file_number}")
                st.markdown(f"**📍 {full_address}**")

                for todo in todos:
                    key = f"{file_number}-{full_address}-{todo}"
                    checked = st.checkbox(todo, key=key)

                    if checked:
                        st.markdown(f"~~{todo}~~")

                st.divider()