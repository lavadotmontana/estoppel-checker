import streamlit as st
from PIL import Image
import pytesseract
import re

st.title("Estoppel Screenshot To-Do Checker")

uploaded_file = st.file_uploader("Upload Screenshot", type=["png", "jpg", "jpeg"])


# 🔍 Extract file number
def extract_file_number(text):
    match = re.search(r"#\s*\d{2}-\d+", text)
    return match.group().replace(" ", "") if match else "Unknown File"


# 🧹 Clean address
def clean_address(text):
    text = text.strip()

    # Remove "Estoppel Letter" only when between street and city
    text = re.sub(
        r",\s*Estoppel Letter\s+([A-Z]+,)",
        r", \1",
        text,
        flags=re.IGNORECASE
    )

    # Backup removal
    text = re.sub(r"\bestoppel letter\b", "", text, flags=re.IGNORECASE)

    # Fix OCR typo
    text = re.sub(r"\bflrida\b", "Florida", text, flags=re.IGNORECASE)

    # Convert FL → Florida
    text = re.sub(r"\bFL\b", "Florida", text, flags=re.IGNORECASE)

    # Trim ZIP+4 → ZIP
    text = re.sub(r"(\d{5})-\d{4}", r"\1", text)

    # Normalize spacing
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# 🔍 Extract address (single-line pattern)
def extract_address(text):
    text = text.replace("\n", " ")

    match = re.search(
        r"(\d+\s+[A-Z\s]+,\s*[A-Z\s]+,\s*(Florida|FL)\s*\d{5}(-\d{4})?)",
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    return clean_address(match.group(1))


# 🧠 Generate To-Do list
def generate_todo(text):
    todos = set()

    # Abbreviation
    if re.search(r"\bPL\b", text):
        todos.add("Spell out Place")

    # State
    if re.search(r"\bFL\b", text, re.IGNORECASE):
        todos.add("Spell out Florida")

    # Casing detection (specific words)
    words = re.findall(r"\b[A-Z]{4,}\b", text)

    ignore = {"FL"}
    words = [w for w in words if w not in ignore]

    if words:
        todos.add(f"Fix casing: {', '.join(words)}")

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