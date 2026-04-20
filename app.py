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

    # Remove unwanted words
    text = re.sub(r"\bproduct\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bestoppel letter\b", "", text, flags=re.IGNORECASE)

    # Fix OCR typo
    text = re.sub(r"\bflrida\b", "Florida", text, flags=re.IGNORECASE)

    # Trim ZIP+4
    text = re.sub(r"(\d{5})-\d{4}", r"\1", text)

    # Normalize spacing
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# 🔍 STRICT address extraction
def extract_address(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    for i in range(len(lines) - 1):
        street = lines[i]
        city = lines[i + 1]

        # ✅ STREET must:
        # start with number + contain street word
        if not re.match(r"^\d+\s+.*", street):
            continue

        if not re.search(r"(Street|St|Road|Rd|Place|Pl|Ave|Lane|Ln|Drive|Dr|Blvd|Circle|Cir)", street, re.IGNORECASE):
            continue

        # ❌ filter junk
        if any(x in street.lower() for x in ["saveorder", "status", "assigned"]):
            continue

        # ✅ CITY must:
        # look like "Pensacola, FL 32506"
        if not re.search(r"[A-Za-z]+,\s*[A-Za-z]{2,}\s*\d{5}", city):
            continue

        if any(x in city.lower() for x in ["saveorder", "status", "assigned"]):
            continue

        return clean_address(f"{street} {city}")

    return None


# 🧠 To-Do logic
def generate_todo(text):
    todos = set()

    if re.search(r"\bpl\b", text, re.IGNORECASE):
        todos.add("Spell out Place")

    if re.search(r"\bfl\b", text, re.IGNORECASE):
        todos.add("Spell out Florida")

    words = re.findall(r"\b[A-Z]{4,}\b", text)
    words = [w for w in words if w != "FL"]

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