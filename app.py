import streamlit as st
from PIL import Image
import pytesseract
import re

st.title("Estoppel Screenshot To-Do Checker")

uploaded_file = st.file_uploader("Upload Screenshot", type=["png", "jpg", "jpeg"])


# 🔍 Extract order number
def extract_order_number(text):
    match = re.search(r"#\d{2}-\d{5,}", text)
    return match.group() if match else "Unknown Order"


# 🧹 Clean address text
def clean_address(text):
    text = text.strip()

    # Remove unwanted words
    text = re.sub(r"\bproduct\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bestoppel letter\b", "", text, flags=re.IGNORECASE)

    # Keep only first 5 digits of ZIP
    text = re.sub(r"(\d{5})-\d{4}", r"\1", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# 🔍 Extract ONE address (reliable for OCR)
def extract_address(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    for i in range(len(lines)):
        line = lines[i]

        # Must contain numbers AND letters (filters phone numbers & junk)
        if re.search(r"\d+", line) and re.search(r"[A-Za-z]", line):

            street_line = line

            # Try to combine with city/state/zip line
            if i + 1 < len(lines):
                next_line = lines[i + 1]

                if re.search(r"\d{5}", next_line):
                    combined = f"{street_line} {next_line}"
                    return clean_address(combined)

            return clean_address(street_line)

    return None


# 🧠 Generate To-Do list
def generate_todo(address):
    todos = set()

    # Abbreviation rules (priority)
    replacements = {
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

    found_abbr = set()

    for abbr, full in replacements.items():
        if re.search(rf"\b{abbr}\b", address, re.IGNORECASE):
            todos.add(f"Spell out {full}")
            found_abbr.add(abbr)

    # State
    if re.search(r"\bFL\b", address):
        todos.add("Spell out Florida")

    # Casing (ignore abbreviations + FL)
    words = re.findall(r"\b[A-Z]{4,}\b", address)
    words = [w for w in words if w not in found_abbr and w != "FL"]

    if words:
        todos.add("Fix casing (use Title Case)")

    return list(todos)


# 🚀 MAIN APP
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Screenshot")

    extracted_text = pytesseract.image_to_string(image)

    order_number = extract_order_number(extracted_text)
    address = extract_address(extracted_text)

    st.subheader("To-Do List")

    if address:
        todos = generate_todo(address)

        st.markdown(f"### 📁 {order_number}")
        st.markdown(f"**📍 {address}**")

        if todos:
            for todo in todos:
                key = f"{order_number}-{todo}"
                checked = st.checkbox(todo, key=key)

                if checked:
                    st.markdown(f"~~{todo}~~")
        else:
            st.success("No issues found ✅")

    else:
        st.error("Address not detected")