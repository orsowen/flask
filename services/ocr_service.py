import numpy as np
import easyocr
import pandas as pd
import time
import re

from utils.ocr_processing import (
    process_ocr_results, assign_columns, assign_rows, build_grid, trim_after_laboratoire
)
from utils.section_utils import detect_section_starts, find_edite_le_date, remove_empty_columns
from utils.row_cleaning_utils import clean_single_text_rows, merge_rows, combine_last_two_columns

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

def is_number_like(value):
    if not isinstance(value, str):
        return False
    cleaned = value.replace(" ", "").replace(",", ".")
    return bool(re.match(r'^\d+(\.\d+)?$', cleaned.strip()))

def is_unit_like(value):
    if not isinstance(value, str):
        return False
    units = ['g/dL', 'mg/L', 'µm³', 'mm³', '%', 'x10⁶', 'x10³', 'g/L', 'pg', 'fL', 'µL', 'g/L', '/mm³']
    return any(unit in value for unit in units) or bool(re.match(r'^[a-zA-Zµ/°³²%]+$', value.strip()))

def merge_number_and_unit_columns(df):
    df = df.copy()
    for row_idx in range(len(df)):
        for col_idx in range(len(df.columns) - 1):
            current_val = df.iat[row_idx, col_idx]
            next_val = df.iat[row_idx, col_idx + 1]
            if (isinstance(current_val, str) and isinstance(next_val, str) and
                is_number_like(current_val) and is_unit_like(next_val) and next_val.strip()):
                merged = f"{current_val.strip()} {next_val.strip()}"
                df.iat[row_idx, col_idx] = merged
                df.iat[row_idx, col_idx + 1] = ""
    return df
def find_title_and_name(df):
    for i in range(len(df)):
        row = df.iloc[i]
        for j in range(len(row)):
            cell = str(row[j]).strip().lower()
            if cell in ['mr', 'mme', 'mrs', 'madame', 'monsieur']:
                # Take all cells after the title cell in the same row
                name_parts = []
                for k in range(j + 1, len(row)):
                    val = row[k]
                    if pd.notna(val) and str(val).strip():
                        name_parts.append(str(val).strip())
                name = " ".join(name_parts)
                return {
                    "title": row[j].strip(),
                    "name": name
                }
    return {}

def extract_champ_valeur_and_others(table_dict):
    extracted = []
    for row in table_dict[1:]:  # Skip the first row
        row_result = {}
        non_empty_cells = [row[key].strip() for key in sorted(row.keys(), key=int) if isinstance(row[key], str) and row[key].strip()]

        if not non_empty_cells:
            continue

        row_result['champ'] = non_empty_cells[0]

        if len(non_empty_cells) > 1:
            row_result['valeur_and_unite'] = non_empty_cells[1]

            if len(non_empty_cells) > 2:
                for i, val in enumerate(non_empty_cells[2:-1]):
                    row_result[f"anteriorite {i + 1}"] = val
                row_result['Valeurs_usuelles'] = non_empty_cells[-1]

        extracted.append(row_result)

    return extracted
def add_etat_to_rows(rows):
    for row in rows:
        try:
            valeur = float(row.get("valeur", "").replace(",", "."))
            ref = row.get("Valeurs usuelles", "").strip()

            # Match pattern like "4.5 - 11.0" or "12-17"
            match = re.match(r"(\d+(?:[.,]\d+)?)\s*[-–]\s*(\d+(?:[.,]\d+)?)", ref)
            if match:
                low = float(match.group(1).replace(',', '.'))
                high = float(match.group(2).replace(',', '.'))

                if low <= valeur <= high:
                    row["etat"] = "bonne"
                else:
                    row["etat"] = "anormale"
        except:
            row["etat"] = "inconnu"
    return rows
def split_valeur_and_unite(rows):
    for row in rows:
        if "valeur_and_unite" in row:
            match = re.match(r"^(\d+(?:[\.,]\d+)?)(?:\s*)([^\d\s].*)?$", row["valeur_and_unite"])
            if match:
                row["valeur"] = match.group(1).replace(',', '.')
                row["unité"] = match.group(2).strip() if match.group(2) else ""
    return rows

class OcrService:
    def __init__(self, image_pil):
        self.image_np = np.array(image_pil)
        self.reader = easyocr.Reader(['fr'], gpu=True)

    def analyse(self):
        start_time = time.time()
        results = self.reader.readtext(self.image_np)

        for i, (bbox, text, conf) in enumerate(results):
            corrected_text = correct_units(text)
            results[i] = (bbox, corrected_text, conf)

        elements = process_ocr_results(results)
        elements = assign_columns(elements)
        elements = assign_rows(elements)

        df = pd.DataFrame(build_grid(elements))
        df.columns = [f'Col {i+1}' for i in range(df.shape[1])]
        df = trim_after_laboratoire(df)

        section_starts = detect_section_starts(df)
        section_starts.append(len(df))

        final_output = {
            "edite_le_date": find_edite_le_date(df),
            "tables": {}
        }
        # Add the MR/Mme extraction 
        person_info = find_title_and_name(df)
        if person_info:
            final_output["person_info"] = person_info
        for i in range(len(section_starts) - 1):
            start, end = section_starts[i], section_starts[i + 1]
            table_df = df.iloc[start:end].reset_index(drop=True)

            section_key = None
            for cell in table_df.iloc[0]:
                if isinstance(cell, str) and cell.strip():
                    section_key = cell.strip()
                    break
            if not section_key:
                section_key = f"Section_{i+1}"

            table_df = table_df.iloc[1:].reset_index(drop=True)
            table_df = remove_empty_columns(table_df)
            table_df = clean_single_text_rows(table_df)
            table_df = merge_rows(table_df)
            table_df = combine_last_two_columns(table_df)
            table_df = remove_empty_columns(table_df)
            table_df.columns = list(range(len(table_df.columns)))

            for col_idx in range(1, len(table_df.columns)):
                table_df[col_idx] = table_df[col_idx].apply(correct_units)

            table_df = merge_number_and_unit_columns(table_df)

            table_dict = table_df.to_dict(orient='records')
            structured_rows = extract_champ_valeur_and_others(table_dict)
            structured_rows = split_valeur_and_unite(structured_rows)
            structured_rows = add_etat_to_rows(structured_rows)

            final_output["tables"][section_key] = structured_rows

        final_output["temps"] = round(time.time() - start_time, 2)
        return final_output
