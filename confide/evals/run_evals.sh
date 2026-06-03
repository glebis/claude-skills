#!/usr/bin/env bash
# CONFIDE plugin eval suite — run all unit tests + integration + trigger evals.
set -e
cd "$(dirname "$0")/.."
echo "== unit/behaviour tests (TDD) =="; python3 -m pytest tests/ -q
echo "== integration eval (anon→red pipeline) =="; python3 evals/integration_eval.py
echo "== trigger eval =="; python3 evals/trigger_eval.py
echo "== ALL EVALS PASSED =="
