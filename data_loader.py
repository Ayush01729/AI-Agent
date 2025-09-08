import pandas as pd

def load_excel(path: str, sheet_name: str = None):
    xls = pd.ExcelFile(path)
    sheet = sheet_name or xls.sheet_names[0]
    df = pd.read_excel(path, sheet_name=sheet)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def dataframe_to_text(df: pd.DataFrame, max_rows: int = None) -> str:
    view = df if max_rows is None else df.head(max_rows)
    rows = []
    for _, row in view.iterrows():
        row_dict = {col: str(val) for col, val in row.items() if pd.notna(val)}
        rows.append(" | ".join([f"{k}: {v}" for k, v in row_dict.items()]))
    return "\n".join(rows)
