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


# 🧹 Clean address
def clean_address(text):
    text = text.strip()

    # Remove junk words
    text = re.sub(r"\bproduct\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bestoppel letter\b", "", text, flags=re.IGNORECASE)

    # Fix common OCR typo
    text = re.sub(r"\bflrida\b", "Florida", text, flags=re.IGNORECASE)

    # Trim ZIP+4 → ZIP
    text = re.sub(r"(\d{5})-\d{4}", r"\1", text)

    # Clean spacing
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# 🔍 Extract ONE address (like your original, but safer)
def extract_address(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    for i in range(len(lines)):
        line = lines[i]

        # must have number + letters (avoids phone/order #)
        if re.search(r"\d+", line) and re.search(r"[A-Za-z]", line):

            # ignore obvious junk lines
            if "status" in line.lower():
                continue

            street = line

            # try combine with next line if it has ZIP
            if i + 1 < len(lines):
                next_line = lines[i + 1]

                if re.search(r"\d{5}", next_line):
                    return clean_address(f"{street} {next_line}")

            return clean_address(street)

    return None


# 🧠 To-Do logic (clean + minimal)
def generate_todo(text):
    todos = set()

    # Abbreviations
    if re.search(r"\bpl\b", text, re.IGNORECASE):
        todos.add("Spell out Place")

    # State
    if re.search(r"\bfl\b", text, re.IGNORECASE):
        todos.add("Spell out Florida")

    # Casing (real words only)
    words = re.findall(r"\b[A-Z]{4,}\b", text)
    words = [w for w in words if w not in ["FL"]]

    if words:
        todos.add("Fix casing (use Title Case)")

    return list(todos)


# 🚀 MAIN
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image)

    text = pytesseract.image_to_string(image)

    file_number = extract_file_number(text)
    address = extract_address(text)

    st.subheader("To-Do List")

    if address:
        todos = generate_todo(address)

        st.markdown(f"### 📁 {file_number}")
        st.markdown(f"**📍 {address}**")

        if todos:
            for todo in todos:
                key = f"{file_number}-{todo}"
                if st.checkbox(todo, key=key):
                    st.markdown(f"~~{todo}~~")
        else:
            st.success("No issues found ✅")

    else:
        st.error("Address not detected")