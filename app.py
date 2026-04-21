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


# 🔍 Extract block after label (handles next-line values)
def extract_block(text, label):
    pattern = rf"{label}([\s\S]{0,50})"
    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return ""

    block = match.group(1)
    lines = [l.strip() for l in block.split("\n") if l.strip()]

    return lines


# 🔍 Field validation (NO DATES)
def check_fields(text):
    issues = []

    # --- Owner Name ---
    owner_lines = extract_block(text, "Owner Name")
    owner_text = " ".join(owner_lines)

    if (
        owner_text == "" or
        owner_text.lower() == "owner name" or
        len(re.findall(r"[A-Za-z]+", owner_text)) < 2
    ):
        issues.append("Missing Owner Name")

    # --- Property ID ---
    prop_lines = extract_block(text, "Property Id")
    prop_text = " ".join(prop_lines).lower()

    if (
        prop_text == "" or
        prop_text in ["propertyid", "property id"] or
        not re.search(r"\d", prop_text)
    ):
        issues.append("Missing Property Id")

    # --- Buyer Name ---
    buyer_lines = extract_block(text, "Buyer Name")
    buyer_text = " ".join(buyer_lines)

    if (
        buyer_text == "" or
        buyer_text.lower() == "buyer name" or
        len(re.findall(r"[A-Za-z]+", buyer_text)) < 2
    ):
        issues.append("Missing Buyer Name")

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