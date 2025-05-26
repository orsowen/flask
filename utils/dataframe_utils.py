from validation_utils import is_number_like, is_unit_like

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
