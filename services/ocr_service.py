import numpy as np
import easyocr
import pandas as pd
import time

from utils.text_correction import correct_units
from utils.dataframe_utils import merge_number_and_unit_columns
from utils.person_extraction import find_title_and_name
from utils.row_extraction import extract_champ_valeur_and_others, split_valeur_and_unite, add_etat_to_rows

from utils.ocr_processing import (
    process_ocr_results, assign_columns, assign_rows, build_grid, trim_after_laboratoire
)
from utils.section_utils import detect_section_starts, find_edite_le_date, remove_empty_columns
from utils.row_cleaning_utils import clean_single_text_rows, merge_rows, combine_last_two_columns

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
