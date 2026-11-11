"""Читает таблицу преподавателя без изменения исходного Excel-файла."""

from pathlib import Path

from openpyxl import load_workbook

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "data/Данные для постановки задачи.xlsx"


def read_data(path=SOURCE):
    sheet = load_workbook(path, data_only=True).worksheets[0]
    cols = (11, 12, 13)
    return {
        "initial_holdings": [sheet.cell(r, 10).value for r in (8, 11, 14)],
        "cash": 600,  # свободные средства заданы в текстовом условии
        "lots": [sheet.cell(r, 10).value//4 for r in (8, 11, 14)],
        "commission_percent": [round(100*sheet.cell(r, 4).value) for r in (13, 14, 15)],
        "minimum": [sheet.cell(r, 4).value for r in (23, 24, 25)],
        "probabilities": [[sheet.cell(r, c).value for r in (4, 5, 6)] for c in cols],
        "rates_percent": [
            [[round(100*sheet.cell(r+outcome, c).value) for r in (8, 11, 14)]
             for outcome in range(3)] for c in cols],
        "source": str(Path(path).name),
    }
