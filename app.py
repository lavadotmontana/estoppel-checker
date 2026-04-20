import streamlit as st
from PIL import Image
import pytesseract
import re

st.title("Estoppel Screenshot To-Do Checker")

uploaded_file = st.file_uploader("Upload Screenshot", type=["png", "jpg", "jpeg"])


def fix_address(text):
    original = text
    todos = []

    # 1. Normalize casing (Title Case but keep directions uppercase)
    def smart_title(s):
        words = s.lower().split()
        directions = {"nw", "ne", "sw", "se", "n", "s", "e", "w"}
        result = []
        for w in words:
            if w in directions:
                result.append(w.upper())
            else:
                result.append(w.capitalize())
        return " ".join(result)

    if text.isupper():
        text = smart_title(text)
        todos.append("Convert to Title Case")

    # 2. Abbreviation replacements
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
            text = re.sub(pattern, full, text, flags=re.IGNORECASE)
            todos.append(f"Replace with '{full}'")

    # 3. State formatting (spell out)
    state_map = {
        "FL": "Florida",
        "TX": "Texas"
    }

    for abbr, full in state_map.items():
        if re.search(rf"\b{abbr}\b", text):
            text = re.sub(rf"\b{abbr}\b", full, text)
            todos.append(f"Spell out state '{full}'")

    # 4. Clean spacing
    if "  " in text:
        text = re.sub(r"\s+", " ", text)
        todos.append("Remove extra spaces")

    # 5. Fix commas
    if ",," in text:
        text = text.replace(",,", ",")
        todos.append("Fix commas")

    return original, text, todos


if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image)

    extracted_text = pytesseract.image_to_string(image)

    st.subheader("Results")

    for line in extracted_text.split("\n"):
        if re.search(r"\d+.*,", line):

            original, fixed, todos = fix_address(line)

            if todos:
                st.markdown(f"### 📍 Original")
                st.write(original)

                st.markdown(f"### ✅ Corrected")
                st.code(fixed)

                st.markdown("### 📝 To-Do")
                for t in todos:
                    st.write(f"- [ ] {t}")

                st.markdown("---")