#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import os
import sys
from typing import Optional

import pandas as pd


EXIT_OK = 0
EXIT_INVALID_ARGS = 1
EXIT_MISSING_COLUMN = 2
EXIT_FILE_NOT_FOUND = 3


class ArgumentParserWithCode(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(EXIT_INVALID_ARGS, f"{self.prog}: error: {message}\n")


def load_dataframe(path: str) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        try:
            # Используем python-движок и автоопределение разделителя,
            # чтобы строки вида "10,5" не ошибочно делились по запятой.
            df = pd.read_csv(path, encoding="utf-8", engine="python", sep=None)
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding="latin-1", engine="python", sep=None)
        return df
    elif ext == ".xlsx":
        return pd.read_excel(path, engine="openpyxl")
    else:
        print("Неподдерживаемый формат файла. Поддерживаются только .csv и .xlsx.", file=sys.stderr)
        sys.exit(EXIT_INVALID_ARGS)


def to_numeric_series(series: pd.Series) -> pd.Series:
    # Normalize decimal comma and coerce to numeric
    s = series.astype(str).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def compute_mean_csv_manual(path: str, expected_column: str) -> Optional[float]:
    # Фолбэк-парсер для одномерных CSV: первая строка — имя колонки,
    # далее одно значение в строке; запятая допускается как десятичный разделитель.
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            lines = f.read().splitlines()
    if not lines:
        print("Пустой файл.", file=sys.stderr)
        sys.exit(EXIT_INVALID_ARGS)
    header = lines[0].strip()
    if header.strip() != expected_column.strip():
        # не наш формат — вернём None, чтобы основной код продолжил стандартную логику
        return None
    values: list[float] = []
    for raw in lines[1:]:
        s = raw.strip()
        if not s:
            continue
        s = s.replace(",", ".")
        try:
            values.append(float(s))
        except ValueError:
            # игнорируем нечисловые значения
            continue
    if not values:
        print(f"В колонке \"{expected_column}\" нет числовых значений.", file=sys.stderr)
        sys.exit(EXIT_INVALID_ARGS)
    return float(sum(values) / len(values))


def compute_mean(path: str, column: str) -> Optional[float]:
    if not os.path.isfile(path):
        print("Файл не найден: {}".format(path), file=sys.stderr)
        sys.exit(EXIT_FILE_NOT_FOUND)

    col_name = column.strip()
    # Ранний фолбэк для простых CSV (одна колонка, возможна десятичная запятая)
    if os.path.splitext(path)[1].lower() == ".csv":
        early_mean = compute_mean_csv_manual(path, col_name)
        if early_mean is not None:
            return early_mean

    try:
        df = load_dataframe(path)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Ошибка чтения файла: {e}", file=sys.stderr)
        sys.exit(EXIT_INVALID_ARGS)

    # Normalize column names by trimming spaces
    try:
        df.columns = df.columns.astype(str).str.strip()
    except Exception:
        # If columns are missing or malformed
        print("Некорректные заголовки столбцов в файле.", file=sys.stderr)
        sys.exit(EXIT_INVALID_ARGS)

    col_name = column.strip()
    if col_name not in df.columns:
        # Фолбэк: одномерный CSV без разделителя (десятичная запятая в значениях)
        if os.path.splitext(path)[1].lower() == ".csv":
            mean_v = compute_mean_csv_manual(path, col_name)
            if mean_v is not None:
                return mean_v
        print(f"Колонка \"{col_name}\" не найдена.", file=sys.stderr)
        sys.exit(EXIT_MISSING_COLUMN)

    numeric = to_numeric_series(df[col_name]).dropna()

    if numeric.empty:
        print(f"В колонке \"{col_name}\" нет числовых значений.", file=sys.stderr)
        sys.exit(EXIT_INVALID_ARGS)

    return float(numeric.mean())


def build_parser() -> ArgumentParserWithCode:
    parser = ArgumentParserWithCode(description="Вычисление среднего значения по указанной колонке из CSV/XLSX файла.")
    parser.add_argument("--input", "-i", required=True, help="Путь к входному файлу (.csv или .xlsx)")
    parser.add_argument("--column", "-c", required=True, help="Имя столбца для расчета среднего")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    mean_val = compute_mean(args.input, args.column)
    # If compute_mean didn't exit with error, we have a float
    print(f"{mean_val:.3f}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
