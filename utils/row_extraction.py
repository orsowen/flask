import re

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

def split_valeur_and_unite(rows):
    for row in rows:
        if "valeur_and_unite" in row:
            match = re.match(r"^(\d+(?:[\.,]\d+)?)(?:\s*)([^\d\s].*)?$", row["valeur_and_unite"])
            if match:
                row["valeur"] = match.group(1).replace(',', '.')
                row["unité"] = match.group(2).strip() if match.group(2) else ""
    return rows

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
