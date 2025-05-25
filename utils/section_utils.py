import re
import pandas as pd

def detect_section_starts(df):
    starts = []
    n_cols = df.shape[1]
    center_col = n_cols // 2  # integer division for center index

    for i in range(len(df) - 1):
        row1 = df.iloc[i]
        row2 = df.iloc[i + 1]
        # Get non-empty cells and their column indices
        non_empty_cells = [(idx, str(cell).strip().lower()) for idx, cell in enumerate(row1) if str(cell).strip()]
        texts1 = [text for idx, text in non_empty_cells]
        texts2 = [str(cell).strip().lower() for cell in row2 if str(cell).strip()]

        # Primary condition (existing)
        if len(texts1) == 1 and \
           any("anteriorité" in text for text in texts2) and \
           any("valeurs usuelles" in text for text in texts2):
            starts.append(i)

        # Fallback condition: single non-empty cell near center (±2 columns)
        elif len(texts1) == 1:
            col_idx = non_empty_cells[0][0]
            if abs(col_idx - center_col) <= 2:
                starts.append(i)

    # Remove duplicates and sort the list
    starts = sorted(set(starts))
    return starts



def find_edite_le_date(df):
    rows = df[df.apply(lambda row: row.astype(str).str.contains("edité le", case=False).any(), axis=1)]
    for _, row in rows.iterrows():
        for cell in row:
            cell_str = str(cell).strip()
            if re.match(r"\d{2}/\d{2}/\d{4}", cell_str):
                return cell_str
    return ""

def remove_empty_columns(df):
    return df.loc[:, df.apply(lambda col: col.astype(str).str.strip().replace('', pd.NA).notna().any())]
