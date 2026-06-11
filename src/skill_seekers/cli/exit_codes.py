"""Standard CLI exit codes (Phase 5c).

Single home for the exit-code conventions every command already follows
informally:

- ``EXIT_SUCCESS`` (0): command completed.
- ``EXIT_ERROR`` (1): runtime failure.
- ``EXIT_VALIDATION`` (2): bad arguments / failed validation (matches
  argparse's own ``parser.error`` exit code).
- ``EXIT_INTERRUPT`` (130): interrupted by SIGINT / KeyboardInterrupt
  (128 + SIGINT, the shell convention).
"""

EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_VALIDATION = 2
EXIT_INTERRUPT = 130
