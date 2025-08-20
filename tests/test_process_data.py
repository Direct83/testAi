# -*- coding: utf-8 -*-
import sys
import subprocess
from pathlib import Path

import pandas as pd


def run_cli(tmp_path: Path, args: list[str]):
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "process_data.py"
    cmd = [sys.executable, str(script)] + args
    return subprocess.run(cmd, capture_output=True, text=True)


def test_csv_success_mean_formatting(tmp_path: Path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("Price\n10\n20\n30\n", encoding="utf-8")

    result = run_cli(tmp_path, ["--input", str(csv_path), "--column", "Price"])

    assert result.returncode == 0
    assert result.stdout == "20.000\n"
    assert result.stderr == ""


def test_xlsx_success_rounding(tmp_path: Path):
    xlsx_path = tmp_path / "data.xlsx"
    df = pd.DataFrame({"Price": [1.2349, 1.2345]})
    df.to_excel(xlsx_path, index=False, engine="openpyxl")

    result = run_cli(tmp_path, ["--input", str(xlsx_path), "--column", "Price"])

    assert result.returncode == 0
    assert result.stdout == "1.235\n"
    assert result.stderr == ""


def test_missing_column_returns_code_2(tmp_path: Path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("Cost\n10\n20\n", encoding="utf-8")

    result = run_cli(tmp_path, ["--input", str(csv_path), "--column", "Price"])

    assert result.returncode == 2
    assert "Колонка \"Price\" не найдена" in result.stderr
    assert result.stdout == ""


def test_file_not_found_code_3(tmp_path: Path):
    missing = tmp_path / "missing.xlsx"

    result = run_cli(tmp_path, ["--input", str(missing), "--column", "Price"])

    assert result.returncode == 3
    assert "Файл не найден" in result.stderr
    assert result.stdout == ""


def test_missing_required_argument_column_code_1(tmp_path: Path):
    # Provide only --input; parser should fail before checking file existence
    dummy_path = tmp_path / "data.csv"

    result = run_cli(tmp_path, ["--input", str(dummy_path)])

    assert result.returncode == 1
    assert "usage:" in result.stderr.lower()
    assert "--column" in result.stderr
    assert result.stdout == ""


def test_mixed_values_ignore_non_numeric(tmp_path: Path):
    csv_path = tmp_path / "mixed.csv"
    csv_path.write_text("Price\n10\nN/A\n20x\n30.5\n", encoding="utf-8")

    result = run_cli(tmp_path, ["--input", str(csv_path), "--column", "Price"])

    assert result.returncode == 0
    assert result.stdout == "20.250\n"
    assert result.stderr == ""


def test_decimal_comma_normalization(tmp_path: Path):
    csv_path = tmp_path / "commas.csv"
    csv_path.write_text("Price\n10,5\n20,5\n", encoding="utf-8")

    result = run_cli(tmp_path, ["--input", str(csv_path), "--column", "Price"])

    assert result.returncode == 0
    assert result.stdout == "15.500\n"
    assert result.stderr == ""


def test_empty_dataset_no_numeric_values_code_1(tmp_path: Path):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("Price\n", encoding="utf-8")

    result = run_cli(tmp_path, ["--input", str(csv_path), "--column", "Price"])

    assert result.returncode == 1
    assert "нет числовых значений" in result.stderr.lower()
    assert result.stdout == ""


def test_header_with_spaces_trimmed(tmp_path: Path):
    csv_path = tmp_path / "spaced.csv"
    csv_path.write_text(" Price \n5\n7\n", encoding="utf-8")

    result = run_cli(tmp_path, ["--input", str(csv_path), "--column", "Price"])

    assert result.returncode == 0
    assert result.stdout == "6.000\n"
    assert result.stderr == ""


def test_unsupported_extension_code_1(tmp_path: Path):
    txt_path = tmp_path / "data.txt"
    txt_path.write_text("", encoding="utf-8")

    result = run_cli(tmp_path, ["--input", str(txt_path), "--column", "Price"])

    assert result.returncode == 1
    assert "Неподдерживаемый формат файла" in result.stderr
    assert result.stdout == ""
