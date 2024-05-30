def htmlTableHeader(keys: list):
    items = [f"<th>{key}</th>" for key in keys]
    return f"<thead><tr>{''.join(items)}</tr></thead>"

def htmlTableRow(data: dict):
    items = [f"<td>{value}</td>" for value in data.values()]
    return f"<tr>{''.join(items)}</tr>"

def htmlTable(data: list):
    keys = list(data[0].keys())
    rows = [htmlTableRow(row) for row in data]
    return f"<table class='table>{htmlTableHeader(keys)}{''.join(rows)}</table>"