import streamlit as st
from PIL import Image
import pytesseract
import re

st.title("Estoppel Screenshot To-Do Checker")

uploaded_file = st.file_uploader("Upload Screenshot", type=["png", "jpg", "jpeg"])


# 🔍 Extract Order Number (anchored to SAVEORDER line)
def extract_order_number(text):
    match = re.search(r"SAVEORDER.*?(#?\d{2}-\d{5,})", text, re.IGNORECASE)
    return match.group(1) if match else "Unknown Order"


# 🔍 Extract Address (between order line and Status)
def extract_address_block(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    capture = False
    address_lines = []

    for line in lines:

        # Start after SAVEORDER line
        if re.search(r"SAVEORDER", line, re.IGNORECASE):
            capture = True
            continue

        # Stop at Status
        if re.search(r"Status:", line, re.IGNORECASE):
            break

        if capture:
            address_lines.append(line)

    return " ".join(address_lines) if address_lines else None


# 🧠 To-Do logic (clean + no noise)
def generate_todo(address):
    todos = []
    address = address.strip()

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

    found_abbr = set()

    # Specific rules first
    for abbr, full in abbreviations.items():
        if re.search(rf"\b{abbr}\b", address, re.IGNORECASE):
            todos.append(f"Spell out {full}")
            found_abbr.add(abbr)

    # State
    if re.search(r"\bFL\b", address):
        todos.append("Spell out Florida")

    # Casing (ignore abbreviations)
    words = re.findall(r"\b[A-Z]{4,}\b", address)
    words = [w for w in words if w not in found_abbr and w != "FL"]

    if words:
        todos.append("Fix casing (use Title Case)")

    return list(set(todos))


# 🚀 Main app
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Screenshot")

    extracted_text = pytesseract.image_to_string(image)

    order_number = extract_order_number(extracted_text)
    address = extract_address_block(extracted_text)

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
        st.error("Could not detect address block")