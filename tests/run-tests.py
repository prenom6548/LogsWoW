#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run every test. No dependencies, no network: `python3 tests/run-tests.py`."""

import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main():
    # The fixture is generated rather than committed stale, so a change to
    # its shape can never silently disagree with the tests that read it.
    subprocess.check_call([sys.executable, os.path.join(HERE, "make_fixture.py")])
    sys.path.insert(0, ROOT)
    loader = unittest.TestLoader()
    suite = loader.discover(HERE, pattern="test_*.py", top_level_dir=ROOT)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
