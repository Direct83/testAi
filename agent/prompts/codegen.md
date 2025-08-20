[SYSTEM]
Generate production-ready Python 3.11 code. Output ONLY a single JSON:
{
  "files": [
    {"path":"process_data.py","content":string},
    {"path":"tests/test_process_data.py","content":string},
    {"path":"README.md","content":string},
    {"path":"requirements.txt","content":string}
  ]
}
Constraints:
- Use pandas; openpyxl for .xlsx.
- CLI via argparse. Mean printed with 3 decimals.
- Exit codes: ok=0, invalid_args=1, missing_column=2, file_not_found=3.
- All code UTF-8, no placeholders or TODOs, no network calls.

[USER]
План (JSON):
{{PLAN_JSON}}
Сгенерируй файлы строго по схеме "files[]".

