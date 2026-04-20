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

    text = re.sub(
        r",\s*Estoppel Letter\s+([A-Z]+,)",
        r", \1",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(r"\bestoppel letter\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bflrida\b", "Florida", text, flags=re.IGNORECASE)
    text = re.sub(r"\bFL\b", "Florida", text, flags=re.IGNORECASE)
    text = re.sub(r"(\d{5})-\d{4}", r"\1", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# 🔍 Extract address
def extract_address(text):
    text = text.replace("\n", " ")

    match = re.search(
        r"(\d+\s+[A-Z\s]+,\s*[A-Z\s]+,\s*(Florida|FL)\s*\d{5}(-\d{4})?)",
        text,
        re.IGNORECASE
    )

    return clean_address(match.group(1)) if match else None


# 🧠 Generate To-Do
def generate_todo(text):
    todos = set()

    if re.search(r"\bPL\b", text):
        todos.add("Spell out Place")

    if re.search(r"\bFL\b", text, re.IGNORECASE):
        todos.add("Spell out Florida")

    words = re.findall(r"\b[A-Z]{4,}\b", text)
    words = [w for w in words if w != "FL"]

    if words:
        todos.add(f"Fix casing: {', '.join(words)}")

    return list(todos)


# 🔍 Check missing fields (FIXED)
def check_missing_fields(text):
    missing = []

    def field_missing(label):
        pattern = rf"{label}\s*(.*)"
        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            return True

        value = match.group(1).strip()
        value = value.split("\n")[0].strip()

        # 🔥 KEY FIX: treat placeholder text as empty
        if value == "" or value.lower() == label.lower():
            return True

        return False

    fields = {
        "Owner Name": "Owner Name",
        "County": "County",
        "Municipality": "Municipality",
        "Property Id": "Property Id",
        "Buyer Name": "Buyer Name",
        "Need By Date": "Need By Date",
        "Closing Date": "Closing Date"
    }

    for key, label in fields.items():
        if field_missing(key):
            missing.append(f"Missing {label}")

    return missing


# 🚀 MAIN
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image)

    text = pytesseract.image_to_string(image)

    file_number = extract_file_number(text)
    address = extract_address(text)
    todos = generate_todo(address) if address else []
    missing_fields = check_missing_fields(text)

    st.subheader("Results")

    # Address
    if address:
        st.markdown(f"### 📁 {file_number}")
        st.markdown(f"**📍 {address}**")

        if todos:
            st.subheader("To-Do List")
            for todo in todos:
                key = f"{file_number}-{todo}"
                if st.checkbox(todo, key=key):
                    st.markdown(f"~~{todo}~~")
        else:
            st.success("No address issues found ✅")
    else:
        st.error("Address not detected")

    # Missing fields
    if missing_fields:
        st.subheader("⚠️ Missing Required Fields")
        for item in missing_fields:
            st.warning(item)