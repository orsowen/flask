import re

def correct_units(text):
    if isinstance(text, str):
        text = text.replace("’", "'").replace("`", "'").strip()
        text = re.sub(r"\bI+mm['’`]?[\.;:]?", "/mm³", text)
        text = re.sub(r"/mm['’`\;\?:\.]?\b", "/mm³", text)
        text = re.sub(r"um'['’`\;\?:\.]?", "µm³", text)
        text = re.sub(r'(\d+\.?\d*)\s*gd[lL]', r'\1 g/dL', text)
        text = re.sub(r'gd[lL]', 'g/dL', text)
        text = re.sub(r'(\d+\.?\d*)\s*mg[JLjl]', r'\1 mg/L', text)
        text = re.sub(r'mg[JLjl]', 'mg/L', text)
        text = re.sub(r'(/mm³)[\'’`\;\?:\.]', r'\1', text)
        text = re.sub(r'(µm³)[\'’`\;\?:\.]', r'\1', text)
        return text
    return text
