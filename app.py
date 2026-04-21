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


# 🔥 FIELD VALIDATION (FINAL)
def check_fields(text):
    issues = []

    # --- Owner Name ---
    owner_match = re.search(r"Owner Name\s*(.*)", text, re.IGNORECASE)
    owner = owner_match.group(1).strip() if owner_match else ""

    if (
        owner == "" or
        owner.lower() == "owner name" or
        len(re.findall(r"[A-Za-z]+", owner)) < 2
    ):
        issues.append("Missing Owner Name")

    # --- Property ID ---
    prop_match = re.search(r"Property Id\s*(.*)", text, re.IGNORECASE)
    prop = prop_match.group(1).strip() if prop_match else ""

    if (
        prop == "" or
        prop.lower() in ["propertyid", "property id"] or
        not re.search(r"\d", prop)
    ):
        issues.append("Missing Property Id")

    # --- Buyer Name ---
    buyer_match = re.search(r"Buyer Name\s*(.*)", text, re.IGNORECASE)
    buyer = buyer_match.group(1).strip() if buyer_match else ""

    if (
        buyer == "" or
        buyer.lower() == "buyer name" or
        len(re.findall(r"[A-Za-z]+", buyer)) < 2
    ):
        issues.append("Missing Buyer Name")

    # --- Dates ---
    def validate_date(label):
        match = re.search(rf"{label}\s*(.*)", text, re.IGNORECASE)
        value = match.group(1).strip() if match else ""

        # Clean OCR junk
        value = re.sub(r"[^\d/]", "", value)

        if value == "" or value.lower() == label.lower():
            return f"Missing {label}"

        if not re.match(r"\d{2}/\d{2}/\d{4}", value):
            return f"{label} format invalid"

        try:
            date_obj = datetime.strptime(value, "%m/%d/%Y")
            if date_obj < datetime.today():
                return f"{label} is in the past"
        except:
            return f"{label} format invalid"

        return None

    need_issue = validate_date("Need By Date")
    closing_issue = validate_date("Closing Date")

    if need_issue:
        issues.append(need_issue)

    if closing_issue:
        issues.append(closing_issue)

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