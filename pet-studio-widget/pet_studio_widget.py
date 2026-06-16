"""Pet Studio desktop widget entrypoint.

This keeps the public command name aligned with the Pet Studio skill while
preserving `project_room_widget.py` as the compatibility implementation module.
"""

from __future__ import annotations

from project_room_widget import main

if __name__ == "__main__":
    main()
