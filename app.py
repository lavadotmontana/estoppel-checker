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


# 🔍 Extract address (SINGLE LINE FORMAT)
def extract_address(text):
    text = text.replace("\n", " ")

    # Match full address pattern
    match = re.search(
        r"(\d+\s+[A-Z\s]+,\s*[A-Z\s]+,\s*(Florida|FL)\s*\d{5}(-\d{4})?)",
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    address = match.group(1)

    # --- Clean it ---
    address = re.sub(r"(\d{5})-\d{4}", r"\1", address)  # trim ZIP+4
    address = re.sub(r"\bFL\b", "Florida", address, flags=re.IGNORECASE)
    address = re.sub(r"\s+", " ", address)

    return address.strip()


# 🧠 To-Do logic
def generate_todo(text):
    todos = set()

    # Abbreviation
    if re.search(r"\bPL\b", text):
        todos.add("Spell out Place")

    # State
    if re.search(r"\bFL\b", text, re.IGNORECASE):
        todos.add("Spell out Florida")

    # --- NEW: precise casing detection ---
    words = re.findall(r"\b[A-Z]{4,}\b", text)

    # Ignore things that shouldn't be flagged
    ignore = {"FL"}
    words = [w for w in words if w not in ignore]

    if words:
        word_list = ", ".join(words)
        todos.add(f"Fix casing: {word_list}")

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