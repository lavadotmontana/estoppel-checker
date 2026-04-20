import streamlit as st
from PIL import Image
import pytesseract
import re

st.title("Estoppel Screenshot To-Do Checker")

uploaded_file = st.file_uploader("Upload Screenshot", type=["png", "jpg", "jpeg"])


# 🔍 Extract file number (more forgiving)
def extract_file_number(text):
    match = re.search(r"#?\d{2}-\d{5,}", text)
    return match.group() if match else "Unknown File"


# 🧠 To-Do logic (clean + prioritized)
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

    # ✅ Specific rules first
    for abbr, full in abbreviations.items():
        if re.search(rf"\b{abbr}\b", address, re.IGNORECASE):
            todos.append(f"Spell out {full}")
            found_abbr.add(abbr)

    # State
    if re.search(r"\bFL\b", address):
        todos.append("Spell out Florida")

    # ✅ Smarter casing (ignore abbreviations)
    words = re.findall(r"\b[A-Z]{4,}\b", address)
    words = [w for w in words if w not in found_abbr and w != "FL"]

    if words:
        todos.append("Fix casing (use Title Case)")

    # Cleanup
    if "  " in address:
        todos.append("Remove extra spaces")

    if ",," in address:
        todos.append("Fix commas")

    return list(set(todos))


# 🔍 Find BEST address (not all lines)
def extract_best_address(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    for i in range(len(lines)):
        line = lines[i]

        # Look for street number
        if re.search(r"\d{3,}", line):

            # Try to combine with next line if ZIP exists
            if i + 1 < len(lines) and re.search(r"\d{5}", lines[i + 1]):
                return f"{line} {lines[i + 1]}"

            return line

    return None


# 🚀 Main app
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Screenshot")

    extracted_text = pytesseract.image_to_string(image)

    file_number = extract_file_number(extracted_text)
    address = extract_best_address(extracted_text)

    st.subheader("To-Do List")

    if address:
        todos = generate_todo(address)

        st.markdown(f"### 📁 {file_number}")
        st.markdown(f"**📍 {address}**")

        if todos:
            for todo in todos:
                key = f"{file_number}-{todo}"
                checked = st.checkbox(todo, key=key)

                if checked:
                    st.markdown(f"~~{todo}~~")
        else:
            st.success("No issues found ✅")

    else:
        st.error("No address detected")