"""python -m chaser_agent runs the chaser command, so it works before the package is reinstalled."""

from chaser_agent.chaser_cli import main

raise SystemExit(main())
