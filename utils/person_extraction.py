import pandas as pd

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
