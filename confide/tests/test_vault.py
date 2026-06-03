"""Offline, fully-mocked tests for confide:vault — the THREE LOCKS storage checker.

Every system call is MOCKED: subprocess (fdesetup), shutil.which (sops/age), and
os.path.exists (age key / store paths). NO real system state is touched. NO destructive
command (fdesetup enable / hdiutil / rm / sops --encrypt) is ever invoked by --check or
lock_status — these tests fail if one would run.
"""
import os
import sys
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "vault", "scripts"))
import vault as V  # noqa: E402


# --------------------------------------------------------------------------
# Helpers — build mocks for the three probes.
# --------------------------------------------------------------------------
def _fake_run(filevault="On"):
    """A subprocess.run replacement that ONLY answers read-only probes.

    Records every argv it sees in `calls` so tests can assert no destructive
    command was attempted.
    """
    calls = []

    def runner(argv, *a, **k):
        calls.append(list(argv))
        joined = " ".join(argv)
        # Only the read-only status probe is allowed to "succeed".
        if "fdesetup" in joined and "status" in joined:
            out = f"FileVault is {filevault}.\n"
            return mock.Mock(returncode=0, stdout=out, stderr="")
        # Anything else: pretend it does nothing (but the assertions below
        # guarantee a destructive command is never even constructed).
        return mock.Mock(returncode=0, stdout="", stderr="")

    runner.calls = calls
    return runner


DESTRUCTIVE_TOKENS = ("enable", "hdiutil", "rm", "--encrypt", "age-keygen", "trash", "diskutil")


def _assert_no_destructive(calls):
    for argv in calls:
        joined = " ".join(argv)
        # fdesetup status is the only fdesetup call allowed.
        if "fdesetup" in joined:
            assert "status" in joined, f"non-status fdesetup call: {argv}"
        for tok in DESTRUCTIVE_TOKENS:
            assert tok not in joined, f"destructive token {tok!r} in probe call: {argv}"


# --------------------------------------------------------------------------
# lock_status structure + all-green case
# --------------------------------------------------------------------------
def test_lock_status_all_green():
    runner = _fake_run(filevault="On")
    with mock.patch.object(V.subprocess, "run", runner), \
         mock.patch.object(V.shutil, "which", lambda name: "/usr/bin/" + name), \
         mock.patch.object(V.os.path, "exists", lambda p: True):
        st = V.lock_status()

    # structure
    assert set(st.keys()) == {"device", "store", "perfile"}
    assert isinstance(st["device"], dict)
    assert isinstance(st["store"], dict)
    assert isinstance(st["perfile"], dict)

    # device
    assert st["device"]["filevault"] is True
    # store present (a configured store path exists, mocked True)
    assert st["store"]["present"] is True
    # perfile all good
    assert st["perfile"]["sops"] is True
    assert st["perfile"]["age"] is True
    assert st["perfile"]["key"] is True

    _assert_no_destructive(runner.calls)


def test_lock_status_all_absent():
    runner = _fake_run(filevault="Off")
    with mock.patch.object(V.subprocess, "run", runner), \
         mock.patch.object(V.shutil, "which", lambda name: None), \
         mock.patch.object(V.os.path, "exists", lambda p: False):
        st = V.lock_status()

    assert st["device"]["filevault"] is False
    assert st["store"]["present"] is False
    assert st["perfile"]["sops"] is False
    assert st["perfile"]["age"] is False
    assert st["perfile"]["key"] is False

    _assert_no_destructive(runner.calls)


# --------------------------------------------------------------------------
# checklist renderer — fix command for every ✗
# --------------------------------------------------------------------------
def test_checklist_all_green_has_no_fix_commands():
    runner = _fake_run(filevault="On")
    with mock.patch.object(V.subprocess, "run", runner), \
         mock.patch.object(V.shutil, "which", lambda name: "/usr/bin/" + name), \
         mock.patch.object(V.os.path, "exists", lambda p: True):
        st = V.lock_status()
    text = V.render_checklist(st)
    assert "✓" in text  # ✓ present
    assert "✗" not in text  # no ✗


def test_checklist_renders_fix_command_for_every_cross():
    runner = _fake_run(filevault="Off")
    with mock.patch.object(V.subprocess, "run", runner), \
         mock.patch.object(V.shutil, "which", lambda name: None), \
         mock.patch.object(V.os.path, "exists", lambda p: False):
        st = V.lock_status()

    items = V.checklist_items(st)
    crossed = [it for it in items if not it["ok"]]
    assert crossed, "expected some failing items in all-absent case"
    for it in crossed:
        assert it.get("fix"), f"failing item has no fix command: {it}"

    text = V.render_checklist(st)
    # the rendered text must contain a fix command for each ✗ item
    for it in crossed:
        assert it["fix"] in text, f"fix not rendered: {it['fix']}"

    # the canonical fix commands appear
    assert "fdesetup enable" in text
    assert "age-keygen" in text
    assert "hdiutil create" in text


# --------------------------------------------------------------------------
# --check is read-only: no destructive call ever made
# --------------------------------------------------------------------------
def test_check_cli_is_read_only():
    runner = _fake_run(filevault="On")
    with mock.patch.object(V.subprocess, "run", runner), \
         mock.patch.object(V.shutil, "which", lambda name: "/usr/bin/" + name), \
         mock.patch.object(V.os.path, "exists", lambda p: True):
        report = V.main(["--check"])

    assert "device" in report and "store" in report and "perfile" in report
    _assert_no_destructive(runner.calls)


def test_default_action_is_check_and_read_only():
    runner = _fake_run(filevault="Off")
    with mock.patch.object(V.subprocess, "run", runner), \
         mock.patch.object(V.shutil, "which", lambda name: None), \
         mock.patch.object(V.os.path, "exists", lambda p: False):
        report = V.main([])  # no args => default --check
    assert "device" in report
    _assert_no_destructive(runner.calls)


def test_lock_status_makes_no_destructive_call_directly():
    # Even called directly (no CLI), probes are read-only.
    runner = _fake_run(filevault="On")
    with mock.patch.object(V.subprocess, "run", runner), \
         mock.patch.object(V.shutil, "which", lambda name: "/usr/bin/" + name), \
         mock.patch.object(V.os.path, "exists", lambda p: True):
        V.lock_status()
    _assert_no_destructive(runner.calls)


# --------------------------------------------------------------------------
# store: must flag cloud-synced locations
# --------------------------------------------------------------------------
def test_store_inside_icloud_is_flagged_unsafe():
    # A store path that lives inside an iCloud/Dropbox tree must be reported unsafe.
    runner = _fake_run(filevault="On")
    icloud = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/RED")
    with mock.patch.object(V.subprocess, "run", runner), \
         mock.patch.object(V.shutil, "which", lambda name: "/usr/bin/" + name), \
         mock.patch.object(V.os.path, "exists", lambda p: True):
        st = V.lock_status(store_path=icloud)
    assert st["store"]["present"] is True
    assert st["store"]["cloud_synced"] is True
    assert st["store"]["safe"] is False
    _assert_no_destructive(runner.calls)


def test_store_outside_cloud_is_safe():
    runner = _fake_run(filevault="On")
    local = os.path.expanduser("~/CONFIDE-RED")
    with mock.patch.object(V.subprocess, "run", runner), \
         mock.patch.object(V.shutil, "which", lambda name: "/usr/bin/" + name), \
         mock.patch.object(V.os.path, "exists", lambda p: True):
        st = V.lock_status(store_path=local)
    assert st["store"]["cloud_synced"] is False
    assert st["store"]["safe"] is True
    _assert_no_destructive(runner.calls)


# --------------------------------------------------------------------------
# --init-age: never overwrites an existing key; needs explicit flag
# --------------------------------------------------------------------------
def test_init_age_refuses_to_overwrite_existing_key():
    runner = _fake_run(filevault="On")
    with mock.patch.object(V.subprocess, "run", runner), \
         mock.patch.object(V.shutil, "which", lambda name: "/usr/bin/" + name), \
         mock.patch.object(V.os.path, "exists", lambda p: True):  # key already exists
        res = V.init_age(confirm=True)
    assert res["created"] is False
    assert "exists" in res["reason"].lower()
    # must NOT have run age-keygen
    _assert_no_destructive(runner.calls)


def test_init_age_without_confirm_only_prints_command():
    runner = _fake_run(filevault="On")
    with mock.patch.object(V.subprocess, "run", runner), \
         mock.patch.object(V.shutil, "which", lambda name: "/usr/bin/" + name), \
         mock.patch.object(V.os.path, "exists", lambda p: False):  # no key yet
        res = V.init_age(confirm=False)  # dry run: print only
    assert res["created"] is False
    assert "age-keygen" in res["command"]
    _assert_no_destructive(runner.calls)


# --------------------------------------------------------------------------
# --init-store: prints the command, NEVER executes without confirmation
# --------------------------------------------------------------------------
def test_init_store_prints_command_does_not_execute():
    runner = _fake_run(filevault="On")
    with mock.patch.object(V.subprocess, "run", runner), \
         mock.patch.object(V.shutil, "which", lambda name: "/usr/bin/" + name), \
         mock.patch.object(V.os.path, "exists", lambda p: False):
        res = V.init_store("/Users/me/CONFIDE-RED.dmg", confirm=False)
    assert res["executed"] is False
    assert "hdiutil create" in res["command"]
    assert "AES-256" in res["command"]
    _assert_no_destructive(runner.calls)
