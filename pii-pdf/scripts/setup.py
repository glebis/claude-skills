#!/usr/bin/env python3
"""Explicit, isolated dependency setup. Default execution only reports a plan."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

MODEL_URL = 'https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl'
SOURCE_FILES = frozenset({'pyproject.toml', 'README.md', 'src/pii_pdf/__init__.py', 'src/pii_pdf/__main__.py', 'src/pii_pdf/cli.py', 'src/pii_pdf/engine.py'})


RUN_ID = str(uuid.uuid4())
SEQ = 0

def emit(event, **fields):
    global SEQ
    SEQ += 1
    print(json.dumps(dict(schema_version='1.0', event=event, ts=datetime.datetime.now(datetime.timezone.utc).isoformat(), run_id=RUN_ID, seq=SEQ, **fields)), flush=True)


class SetupError(Exception):
    def __init__(self, message, code=3):
        super().__init__(message)
        self.code = code


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise SetupError(message)

def run(command):
    try:
        return subprocess.run([str(x) for x in command], capture_output=True, text=True, timeout=900)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SetupError('Could not run command: ' + type(exc).__name__, 5) from exc


def step(command):
    result = run(command)
    emit('step_result', command=[str(x) for x in command], ok=result.returncode == 0, returncode=result.returncode)
    if result.returncode:
        raise SetupError('Installation or verification command failed; run the reported command locally for detailed diagnostics.', 5)
    return result


def integrity(assets):
    source = assets / 'cli'
    manifest = assets / 'source.sha256'
    if source.is_symlink() or not source.is_dir() or manifest.is_symlink() or not manifest.is_file():
        raise SetupError('Visible CLI source directory or source.sha256 is missing or symlinked.')
    expected = {}
    for line in manifest.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2 or not re.fullmatch(r'[0-9a-fA-F]{64}', parts[0]):
            raise SetupError('Malformed source.sha256 entry.')
        name = parts[1].lstrip('*')
        if name not in SOURCE_FILES or name in expected:
            raise SetupError('Unexpected or duplicate source manifest path.')
        expected[name] = parts[0].lower()
    if set(expected) != SOURCE_FILES:
        raise SetupError('Source manifest does not cover the exact required source files.')
    found = set()
    for entry in source.rglob('*'):
        if entry.is_symlink():
            raise SetupError('Symlinks are not allowed in bundled source.')
        if entry.is_dir():
            if entry.relative_to(source).as_posix() not in {'src', 'src/pii_pdf'}:
                raise SetupError('Unexpected directory in bundled source.')
            continue
        name = entry.relative_to(source).as_posix()
        if not entry.is_file() or name not in SOURCE_FILES:
            raise SetupError('Unexpected file in bundled source.')
        found.add(name)
        if hashlib.sha256(entry.read_bytes()).hexdigest() != expected[name]:
            raise SetupError('Bundled source checksum mismatch: ' + name)
    if found != SOURCE_FILES:
        raise SetupError('Required bundled source files are missing.')
    emit('integrity', ok=True, files=len(found), source=str(source))
    return source


def probe_python(executable):
    result = run([executable, '-c', 'import json,sys,venv;print(json.dumps(list(sys.version_info[:3])))'])
    try:
        version = json.loads(result.stdout) if result.returncode == 0 else []
        valid = tuple(version) >= (3, 10)
    except (ValueError, TypeError):
        valid = False
        version = []
    if not valid:
        raise SetupError('Selected Python must be Python 3.10+ with the venv module.')
    return version


def probe_packages(python):
    code = "import importlib.metadata as m,json; names=['pii-pdf-lab','spacy','PyMuPDF','en-core-web-sm']; out={};\nfor n in names:\n try: out[n]=m.version(n)\n except m.PackageNotFoundError: out[n]=None\nprint(json.dumps(out))"
    result = run([python, '-c', code])
    if result.returncode:
        raise SetupError('Existing virtual environment cannot inspect installed package metadata.')
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise SetupError('Package probe returned invalid JSON.') from exc


def packages_ok(packages):
    pymupdf = packages.get('PyMuPDF') or ''
    match = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)', pymupdf)
    return packages.get('pii-pdf-lab') == '0.1.8' and bool(re.fullmatch(r'3\.8\.\d+', packages.get('spacy') or '')) and bool(match and (1, 26, 7) <= tuple(map(int, match.groups())) < (1, 27, 0))


def main(argv=None):
    parser = Parser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--plan', action='store_true', help='Report missing steps without changing anything (default).')
    mode.add_argument('--apply', action='store_true', help='Install missing dependencies into the isolated environment.')
    parser.add_argument('--venv', default='~/.local/share/pii-pdf/venv')
    parser.add_argument('--python', default=sys.executable)
    parser.add_argument('--model', choices=['en_core_web_sm'], default='en_core_web_sm')
    parser.add_argument('--system', choices=['auto', 'skip'], default='auto')
    args = parser.parse_args(argv)
    assets = Path(__file__).resolve().parents[1] / 'assets'
    source = integrity(assets)
    version = probe_python(args.python)
    target = Path(args.venv).expanduser().absolute()
    python = target / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    cli = target / ('Scripts/pii-pdf.exe' if os.name == 'nt' else 'bin/pii-pdf')
    exists = target.exists()
    if exists and (not (target / 'pyvenv.cfg').is_file() or not python.is_file()):
        raise SetupError('Target exists but is not a usable virtual environment; choose a new --venv path.')
    if exists and re.search(r'^include-system-site-packages\s*=\s*true\s*$', (target / 'pyvenv.cfg').read_text(encoding='utf-8'), re.MULTILINE | re.IGNORECASE):
        raise SetupError('Existing virtual environment exposes global packages; choose an isolated --venv path.')
    if exists:
        version = probe_python(str(python))
    packages = probe_packages(str(python)) if exists else {}
    pip_missing = exists and run([str(python), '-m', 'pip', '--version']).returncode != 0
    tesseract = shutil.which('tesseract')
    tess_ok = False
    if tesseract:
        tess = run([tesseract, '--version'])
        tess_ok = tess.returncode == 0 and 'tesseract' in (tess.stdout + tess.stderr).lower()
    eng_ok = False
    if tess_ok:
        languages = run([tesseract, '--list-langs'])
        eng_ok = languages.returncode == 0 and 'eng' in languages.stdout.splitlines()
    commands = []
    system_problem = None
    if not tess_ok and args.system == 'auto':
        if platform.system() == 'Darwin' and shutil.which('brew'):
            commands.append([shutil.which('brew'), 'install', 'tesseract'])
        elif platform.system() == 'Linux' and shutil.which('apt-get') and hasattr(os, 'geteuid') and os.geteuid() == 0:
            commands.append([shutil.which('apt-get'), 'install', '-y', 'tesseract-ocr', 'tesseract-ocr-eng'])
        else:
            system_problem = 'Install Tesseract manually (macOS: brew install tesseract; Debian/Ubuntu: apt-get install -y tesseract-ocr as root), then rerun. No installer or sudo is run automatically.'
    if tess_ok and not eng_ok and args.system == 'auto':
        if platform.system() == 'Linux' and shutil.which('apt-get') and hasattr(os, 'geteuid') and os.geteuid() == 0:
            commands.append([shutil.which('apt-get'), 'install', '-y', 'tesseract-ocr-eng'])
        else:
            system_problem = 'Tesseract English language data (eng) is missing. Repair the Tesseract installation using your package manager, verify tesseract --list-langs includes eng, then rerun.'
    if not exists:
        commands.append([args.python, '-m', 'venv', str(target)])
    if pip_missing:
        commands.append([str(python), '-m', 'ensurepip', '--upgrade'])
    if not packages_ok(packages):
        commands.append([str(python), '-m', 'pip', 'install', '--no-input', str(source), 'spacy>=3.8,<3.9', 'PyMuPDF>=1.26.7,<1.27'])
    elif not cli.is_file():
        commands.append([str(python), '-m', 'pip', 'install', '--no-input', '--force-reinstall', '--no-deps', str(source)])
    if packages.get('en-core-web-sm') != '3.8.0':
        commands.append([str(python), '-m', 'pip', 'install', '--no-input', MODEL_URL])
    emit('plan', apply=args.apply, venv=str(target), python_version=version, packages=packages, tesseract_ok=tess_ok, english_data_ok=eng_ok, commands=commands, system_problem=system_problem)
    if not args.apply:
        emit('complete', ok=True, mode='plan', changes_made=False, ready=not commands and tess_ok and eng_ok and not system_problem)
        return 0
    if system_problem:
        raise SetupError(system_problem)
    staging_path = None
    applied_commands = commands
    if any(str(source) in command for command in commands):
        staging_path = Path(tempfile.mkdtemp(prefix='pii-pdf-build-'))
        staged_source = staging_path / 'cli'
        shutil.copytree(source, staged_source)
        applied_commands = [[str(staged_source) if arg == str(source) else arg for arg in command] for command in commands]
        emit('staging', staging_path=str(staging_path), retained=True)
    for command in applied_commands:
        step(command)
    # Reprobe even when system installation was skipped; never claim full success without OCR.
    tesseract = shutil.which('tesseract')
    tess_ok = False
    if tesseract:
        result = run([tesseract, '--version'])
        tess_ok = result.returncode == 0 and 'tesseract' in (result.stdout + result.stderr).lower()
    if not tess_ok:
        emit('complete', ok=False, incomplete=True, reason='Tesseract is missing or failed its version check.', exit_code=4)
        return 4
    languages = run([tesseract, '--list-langs'])
    if languages.returncode != 0 or 'eng' not in languages.stdout.splitlines():
        emit('complete', ok=False, incomplete=True, reason='Tesseract English data is missing; repair your package-manager installation so --list-langs includes eng.', exit_code=4)
        return 4
    doctor = step([str(cli), 'doctor'])
    try:
        report = json.loads(doctor.stdout)
    except ValueError as exc:
        raise SetupError('Doctor did not return valid JSON.', 5) from exc
    if not isinstance(report, dict) or report.get('ok') is not True:
        raise SetupError('Doctor did not report ok=true.', 5)
    emit('complete', ok=True, mode='apply', tesseract_version_checked=True, english_data_checked=True, doctor=report, staging_path=str(staging_path) if staging_path else None)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except SetupError as exc:
        emit('error', ok=False, message=str(exc), exit_code=exc.code)
        sys.exit(exc.code)
    except Exception as exc:
        emit('error', ok=False, message='Unexpected setup failure: ' + type(exc).__name__, exit_code=5)
        sys.exit(5)
