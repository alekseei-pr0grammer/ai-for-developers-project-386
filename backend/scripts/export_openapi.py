"""Write the OpenAPI schema to a file without starting the server.

Usage: uv run python scripts/export_openapi.py ../frontend/openapi.json
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402

target = Path(sys.argv[1] if len(sys.argv) > 1 else "openapi.json")
target.write_text(json.dumps(app.openapi(), indent=2) + "\n")
print(f"OpenAPI schema written to {target}")
