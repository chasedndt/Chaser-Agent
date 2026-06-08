from datetime import datetime, timezone

def run_log_header(name: str) -> str:
    return f"# Run Log — {name}\n\nCreated: {datetime.now(timezone.utc).isoformat()}\n"
