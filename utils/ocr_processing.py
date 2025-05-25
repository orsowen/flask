def process_ocr_results(results):
    return [{
        'x_center': (min(pt[0] for pt in bbox) + max(pt[0] for pt in bbox)) / 2,
        'x_min': min(pt[0] for pt in bbox),
        'x_max': max(pt[0] for pt in bbox),
        'y_center': (min(pt[1] for pt in bbox) + max(pt[1] for pt in bbox)) / 2,
        'y_min': min(pt[1] for pt in bbox),
        'y_max': max(pt[1] for pt in bbox),
        'text': text
    } for bbox, text, conf in results]

def assign_columns(elements, threshold=60):
    columns = []
    for el in sorted(elements, key=lambda e: e['x_center']):
        for col in columns:
            if abs(el['x_center'] - col['x_center']) < threshold and \
               not (el['x_max'] < col['x_min'] or el['x_min'] > col['x_max']):
                col['blocks'].append(el)
                col['x_min'] = min(col['x_min'], el['x_min'])
                col['x_max'] = max(col['x_max'], el['x_max'])
                col['x_center'] = (col['x_min'] + col['x_max']) / 2
                el['col'] = col['blocks'][0]['col']
                break
        else:
            col_index = len(columns)
            el['col'] = col_index
            columns.append({'x_center': el['x_center'], 'x_min': el['x_min'], 'x_max': el['x_max'], 'blocks': [el]})
    return elements

def assign_rows(elements, threshold=20):
    rows_y = []
    for el in sorted(elements, key=lambda e: e['y_center']):
        if not any(abs(el['y_center'] - ry) < threshold for ry in rows_y):
            rows_y.append(el['y_center'])
    for el in elements:
        el['row'] = min(range(len(rows_y)), key=lambda i: abs(el['y_center'] - rows_y[i]))
    return elements

def build_grid(elements):
    max_row = max(el['row'] for el in elements) + 1
    max_col = max(el['col'] for el in elements) + 1
    grid = [['' for _ in range(max_col)] for _ in range(max_row)]
    for el in elements:
        prev = grid[el['row']][el['col']]
        grid[el['row']][el['col']] = (prev + ' ' + el['text']).strip()
    return grid

def trim_after_laboratoire(df):
    keyword = "laboratoire d'analyses medicale"
    for i in reversed(range(len(df))):
        row_text = " ".join(str(cell).lower() for cell in df.iloc[i] if str(cell).strip())
        if keyword in row_text:
            return df.iloc[:i].reset_index(drop=True)
    return df
