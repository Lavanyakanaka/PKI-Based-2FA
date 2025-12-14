from pathlib import Path


def assert_no_crlf(path: Path):
    data = path.read_bytes()
    assert b"\r" not in data, f"Found CRLF in {path}"


def test_scripts_have_no_crlf():
    repo_root = Path('.')
    files = [repo_root / 'scripts' / 'run_uvicorn.sh', repo_root / 'scripts' / 'run_cron.sh', repo_root / 'scripts' / 'entrypoint.sh', repo_root / 'scripts' / 'check_health.py', repo_root / 'cron' / 'totp_cron']
    for p in files:
        assert p.exists(), f"Missing file: {p}"
        assert_no_crlf(p)
