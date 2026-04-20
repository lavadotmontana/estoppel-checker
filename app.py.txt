import streamlit as st
from PIL import Image
import pytesseract
import re

st.title("Estoppel Screenshot To-Do Checker")

uploaded_file = st.file_uploader("Upload Screenshot", type=["png", "jpg", "jpeg"])

def generate_todo(text):
    todos = []

    if text.isupper():
        todos.append("Convert to Title Case")

    if re.search(r"\bPL\b", text):
        todos.append('Replace "PL" with "Place"')

    if re.search(r"\bCt\b", text):
        todos.append('Replace "Ct" with "Court"')

    return todos

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image)

    text = pytesseract.image_to_string(image)

    st.subheader("To-Do List")

    for line in text.split("\n"):
        if re.search(r"\d+.*,", line):
            todos = generate_todo(line)

            if todos:
                st.markdown(f"**{line}**")
                for t in todos:
                    st.write(f"- [ ] {t}")
                st.markdown("---")