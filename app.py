import streamlit as st
from PIL import Image
import pytesseract
import re
from datetime import datetime

st.title("Estoppel Screenshot To-Do Checker")

uploaded_file = st.file_uploader("Upload Screenshot", type=["png", "jpg", "jpeg"])


# 🔍 Extract file number
def extract_file_number(text):
    match = re.search(r"#\s*\d{2}-\d+", text)
    return match.group().replace(" ", "") if match else "Unknown File"


# 🧹 Clean address
def clean_address(text):
    text = text.strip()

    text = re.sub(r",\s*Estoppel Letter\s+([A-Z]+,)", r", \1", text, flags=re.IGNORECASE)
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


# 🧠 To-Do list
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


# 🔥 NEW FIELD VALIDATION (robust)
def check_fields(text):
    issues = []
    t = text.lower()

    # --- Owner Name ---
    # If we DON'T see a real person name anywhere → missing
    if not re.search(r"\b[a-z]+ [a-z]+\b", text):
        issues.append("Missing Owner Name")

    # --- Property ID ---
    # Only check if placeholder still exists
    if "propertyid" in t or "property id" in t:
        # but ensure no real ID pattern exists
        if not re.search(r"\d{2}-", text):
            issues.append("Missing Property Id")

    # --- County ---
    if "escambia" not in t:
        issues.append("Missing County")

    # --- Municipality ---
    if "county" not in t:
        issues.append("Missing Municipality")

    # --- Buyer Name ---
    # Look specifically for Buyer Name + real name
    if not re.search(r"buyer name\s+[a-z]+\s+[a-z]+", text, re.IGNORECASE):
        issues.append("Missing Buyer Name")

    # --- Dates ---
    dates = re.findall(r"\d{2}/\d{2}/\d{4}", text)

    if len(dates) < 2:
        issues.append("Missing Need By Date")
        issues.append("Missing Closing Date")
    else:
        today = datetime.today()

        try:
            need_by = datetime.strptime(dates[0], "%m/%d/%Y")
            closing = datetime.strptime(dates[1], "%m/%d/%Y")

            if need_by < today:
                issues.append("Need By Date is in the past")

            if closing < today:
                issues.append("Closing Date is in the past")

        except:
            issues.append("Date format issue")

    return issues


# 🚀 MAIN
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image)

    text = pytesseract.image_to_string(image)

    file_number = extract_file_number(text)
    address = extract_address(text)
    todos = generate_todo(address) if address else []
    issues = check_fields(text)

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

    # Field Issues
    if issues:
        st.subheader("⚠️ Field Issues")
        for item in issues:
            st.warning(item)