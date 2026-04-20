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


# 🧹 Clean address
def clean_address(text):
    text = text.strip()

    # Remove junk words
    text = re.sub(r"\bproduct\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bestoppel letter\b", "", text, flags=re.IGNORECASE)

    # Fix common OCR mistake: Flrida → Florida
    text = re.sub(r"\bflrida\b", "Florida", text, flags=re.IGNORECASE)

    # Fix ZIP (remove +4)
    text = re.sub(r"(\d{5})-\d{4}", r"\1", text)

    # Normalize spacing
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# 🔍 Extract address (based on your known format)
def extract_address(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    for i in range(len(lines)):
        line = lines[i]

        # Street line: starts with number
        if re.match(r"^\d+", line):

            street = line.rstrip(",")

            # Next line should contain ZIP
            if i + 1 < len(lines):
                next_line = lines[i + 1]

                if re.search(r"\d{5}", next_line):
                    return clean_address(f"{street} {next_line}")

            return clean_address(street)

    return None


# 🧠 Generate To-Do list
def generate_todo(address):
    todos = set()

    # Abbreviations
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

    # State (handle Florida OR misspelling)
    if re.search(r"\bfl\b", address, re.IGNORECASE):
        todos.add("Spell out Florida")

    if re.search(r"\bflorida\b", address, re.IGNORECASE) is False:
        if re.search(r"flrida", address, re.IGNORECASE):
            todos.add("Correct spelling of Florida")

    # Casing (ignore abbreviations)
    words = re.findall(r"\b[A-Z]{4,}\b", address)
    words = [w for w in words if w not in found_abbr and w != "FL"]

    if words:
        todos.add("Fix casing (use Title Case)")

    return list(todos)


# 🚀 MAIN
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image)

    text = pytesseract.image_to_string(image)

    order_number = extract_order_number(text)
    address = extract_address(text)

    st.subheader("To-Do List")

    if address:
        todos = generate_todo(address)

        st.markdown(f"### 📁 {order_number}")
        st.markdown(f"**📍 {address}**")

        if todos:
            for todo in todos:
                key = f"{order_number}-{todo}"
                if st.checkbox(todo, key=key):
                    st.markdown(f"~~{todo}~~")
        else:
            st.success("No issues found ✅")

    else:
        st.error("Address not detected")