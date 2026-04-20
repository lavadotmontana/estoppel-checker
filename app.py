import streamlit as st
from PIL import Image
import pytesseract
import re

st.title("Estoppel Screenshot To-Do Checker")

uploaded_file = st.file_uploader("Upload Screenshot", type=["png", "jpg", "jpeg"])


def generate_todo(text):
    todos = set()

    # 1. Casing
    if text.isupper():
        todos.add("Convert address to Title Case")

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
            todos.add(f"Spell out '{full}' (no abbreviations)")

    # 3. Directions
    if re.search(r"\b(nw|ne|sw|se|n|s|e|w)\b", text, re.IGNORECASE):
        todos.add("Ensure directions (N, S, E, W, NW, etc.) are uppercase")

    # 4. State formatting (Florida only for now)
    if re.search(r"\bFL\b", text):
        todos.add("Spell out state (Florida)")

    # 5. Formatting cleanup
    if "  " in text:
        todos.add("Remove extra spaces")

    if ",," in text:
        todos.add("Fix extra commas")

    # 6. Structure check
    if not re.search(r".+,\s.+,\s.+\d{5}", text):
        todos.add("Ensure format: City, State ZIP")

    return list(todos)


if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image)

    extracted_text = pytesseract.image_to_string(image)

    st.subheader("To-Do List")

    lines = extracted_text.split("\n")

    for line in lines:
        if re.search(r"\d+.*,", line):  # detect address-like lines

            todos = generate_todo(line)

            if todos:
                st.markdown(f"**📍 {line}**")

                for todo in todos:
                    st.checkbox(todo, key=f"{line}-{todo}")

                st.markdown("---")