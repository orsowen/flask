import pandas as pd

def clean_single_text_rows(df):
    cleaned_rows = []
    for idx, row in df.iterrows():
        if idx < 1:
            cleaned_rows.append(row)
            continue
        non_empty = row.apply(lambda x: str(x).strip() != "")
        if non_empty.sum() == 1:
            new_row = pd.Series([""] * len(row), index=row.index)
            new_row.iloc[0] = row[non_empty].values[0]
            cleaned_rows.append(new_row)
        else:
            cleaned_rows.append(row)
    return pd.DataFrame(cleaned_rows)

def has_overlapping_filled_cells(row1, row2, columns):
    for col in columns:
        if str(row1[col]).strip() != "" and str(row2[col]).strip() != "":
            return True
    return False

def merge_rows(df):
    merged_rows = []
    skip = False
    for i in range(len(df)):
        if skip:
            skip = False
            continue
        row = df.iloc[i].copy()
        if i >= 2 and i + 1 < len(df):
            next_row = df.iloc[i + 1]
            if not has_overlapping_filled_cells(row, next_row, df.columns):
                for col in df.columns:
                    if str(row[col]).strip() == "" and str(next_row[col]).strip() != "":
                        row[col] = next_row[col]
                skip = True
        merged_rows.append(row)
    return pd.DataFrame(merged_rows)

def combine_last_two_columns(df):
    if len(df.columns) < 2:
        return df
    i, j = df.columns[-2], df.columns[-1]
    for idx, row in df.iterrows():
        val_i, val_j = str(row[i]).strip(), str(row[j]).strip()
        if is_number(val_i) and is_number(val_j):
            df.at[idx, i] = f"{val_i} - {val_j}"
            df.at[idx, j] = ""
    return df

def is_number(s):
    try:
        float(s.replace(',', '.'))
        return True
    except:
        return False
