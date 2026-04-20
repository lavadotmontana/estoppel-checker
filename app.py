import streamlit as st
from PIL import Image
import pytesseract
import re

st.title("Estoppel Screenshot To-Do Checker")

uploaded_file = st.file_uploader("Upload Screenshot", type=["png", "jpg", "jpeg"])


# 🔍 Extract file number like #26-10908455
def extract_file_number(text):
    match = re.search(r"#\d{2}-\d+", text)
    if match:
        return match.group()
    return "Unknown File"


# 🧠 Generate To-Do list
def generate_todo(text):
    todos = set()

    # 1. Casing
    if text.isupper():
        todos.add("Convert to Title Case")

    # 2. Abbreviations
    replacements = {
        r"\bCt\b": "Court",
        r"\bPl\b": "Place",
        r"\bRd\b": "Road",
        r"\bSt\b": "Street",
        r"\bDr\b": "Drive",
        r"\bLn\b": "Lane",
        r"\bBlvd\b": "Boulevard",
        r"\bAve\b": "Avenue",
        r"\bCir\b": "Circle"
    }

    for pattern, full in replacements.items():
        if re.search(pattern, text, re.IGNORECASE):
            todos.add(f"Spell out {full}")

    # 3. Directions
    if re.search(r"\b(nw|ne|sw|se|n|s|e|w)\b", text, re.IGNORECASE):
        todos.add("Ensure directions (N, S, E, W, etc.) are uppercase")

    # 4. State
    if re.search(r"\bFL\b", text):
        todos.add("Spell out Florida")

    # 5. Cleanup
    if "  " in text:
        todos.add("Remove extra spaces")

    if ",," in text:
        todos.add("Fix commas")

    return list(todos)


# 🚀 Main app
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image)

    extracted_text = pytesseract.image_to_string(image)

    file_number = extract_file_number(extracted_text)

    st.subheader("To-Do List")

    lines = extracted_text.split("\n")

    for i in range(len(lines)):
        line = lines[i]

        # Detect street line
        if re.search(r"\d+", line):

            full_address = line.strip()

            # Try to combine with next line (city/state/zip)
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if re.search(r"\d{5}", next_line):
                    full_address = f"{line.strip()} {next_line.strip()}"

            todos = generate_todo(full_address)

            if todos:
                # 📁 Smaller file number
                st.markdown(f"<h4>📁 {file_number}</h4>", unsafe_allow_html=True)

                # 📍 Full address
                st.markdown(f"**📍 {full_address}**")

                # ✅ Checklist
                for todo in todos:
                    key = f"{file_number}-{full_address}-{todo}"
                    checked = st.checkbox(todo, key=key)

                    if checked:
                        st.markdown(
                            f"<span style='color:green'><s>{todo}</s></span>",
                            unsafe_allow_html=True
                        )

                st.markdown("---")