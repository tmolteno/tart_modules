"""
Offline tests for the tart_download_data script.

Regression tests for tmolteno/tart_modules#4 ("Add a --file CLI option to
tart_download_data"):

* ``--file`` must be honoured at the default ``--n -1``. It used to be
  applied only when ``--n`` was exactly 1, so the switch was silently
  ignored in the case the issue cares about. Per the issue, ``--file`` is
  equivalent to ``--n 1`` plus renaming the output, so it also stops after
  the single download.
* ``--n > 1`` together with ``--file`` is still rejected.
* the default ``--n -1`` keeps following the feed: the tool re-polls after
  pausing instead of returning (this is deliberate - see README NEWS "Add
  --n option ... to stop after n downloads (used to grab the latest raw
  file)").
* a positive ``--n`` still stops after that many downloads.

No network access: APIhandler (the HTTP client) and download_file are
replaced with fakes.
"""
#
# Copyright (c) Tim Molteno 2026. tim@elec.ac.nz
#

import hashlib
import logging
import os
import sys
import tempfile
import unittest
import urllib.parse
from unittest import mock

from tart_tools.scripts import tart_download_data

API = "https://tart.example.invalid/signal"


class StopPolling(BaseException):
    """Escapes the endless polling loop.

    Deliberately a BaseException (like KeyboardInterrupt): the script swallows
    plain Exceptions, and unlike KeyboardInterrupt it does not make pytest
    abort the whole test session.
    """


RAW_ENTRY = {
    "filename": "raw_2023-11-15_21_13_29.516643.hdf",
    "checksum": "0" * 64,
}
VIS_ENTRY = {
    "filename": "vis_2023-11-15_21_13_29.516643.hdf",
    "checksum": "1" * 64,
}


def entry(name):
    return {"filename": name, "checksum": "2" * 64}


def urllib_url(filename):
    return urllib.parse.urljoin(API + "/", filename)


class FakeAPI:
    """Stands in for APIhandler: serves a fixed listing and counts polls."""

    def __init__(self, raw=None, vis=None, max_polls=None):
        self.raw = list(raw or [])
        self.vis = list(vis or [])
        self.max_polls = max_polls
        self.polls = 0

    def get(self, path):
        if self.max_polls is not None and self.polls >= self.max_polls:
            # Break out of the deliberately endless polling loop; nothing in
            # the script may swallow this.
            raise StopPolling("test: stop polling")
        self.polls += 1
        if path == "raw/data":
            return list(self.raw)
        if path == "vis/data":
            return list(self.vis)
        raise AssertionError(f"unexpected endpoint {path}")


class TestTartDownloadData(unittest.TestCase):

    def setUp(self):
        self.workdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.workdir.cleanup)
        self.downloads = []
        self.sleeps = []
        self.api = None
        # main() installs a handler on the root logger on every call; keep
        # the suite output (and the handlers other tests rely on) stable.
        root = logging.getLogger()
        saved_handlers = root.handlers[:]
        saved_level = root.level

        def restore():
            for handler in root.handlers[:]:
                root.removeHandler(handler)
            for handler in saved_handlers:
                root.addHandler(handler)
            root.setLevel(saved_level)

        self.addCleanup(restore)

    def fake_download(self, url, checksum, file_path):
        self.downloads.append((url, checksum, file_path))

    def run_main(self, *extra, raw=None, vis=None, max_polls=5):
        """Run tart_download_data.main() against fakes; returns nothing.

        Records the fake API on self.api, downloads on self.downloads and
        sleep() calls on self.sleeps, so the state is available even when
        main() is broken out of with an exception. max_polls caps the number
        of polls so that a regression to "never returns" fails instead of
        hanging the test run.
        """
        self.api = FakeAPI(raw=raw, vis=vis, max_polls=max_polls)
        argv = [
            "tart_download_data",
            "--api", API,
            "--dir", self.workdir.name,
        ] + list(extra)
        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch.object(
                tart_download_data, "APIhandler", return_value=self.api
            ),
            mock.patch.object(
                tart_download_data, "download_file",
                side_effect=self.fake_download,
            ),
            mock.patch.object(
                tart_download_data.time, "sleep", side_effect=self.sleeps.append
            ),
        ):
            return tart_download_data.main()

    def downloaded_names(self):
        return [os.path.basename(path) for _, _, path in self.downloads]

    # --- tmolteno/tart_modules#4 ------------------------------------------

    def test_file_honoured_at_default_n(self):
        """--file must name the output at the default --n -1 (issue #4)."""
        self.run_main("--raw", "--file", "test.hdf",
                      raw=[RAW_ENTRY, VIS_ENTRY])
        self.assertEqual(self.downloaded_names(), ["test.hdf"])
        self.assertEqual(self.api.polls, 1)
        # No "Pausing." sleep: --file implies --n 1, so the tool stopped.
        self.assertEqual(self.sleeps, [])

    def test_file_honoured_with_explicit_n_one(self):
        """--n 1 --file test.hdf behaves the same way."""
        self.run_main("--raw", "--n", "1", "--file", "test.hdf",
                      raw=[RAW_ENTRY])
        self.assertEqual(self.downloaded_names(), ["test.hdf"])
        self.assertEqual(self.api.polls, 1)
        self.assertEqual(self.sleeps, [])

    def test_file_names_the_requested_path(self):
        """The rename applies to the whole path inside --dir."""
        self.run_main("--vis", "--file", "test.hdf", vis=[VIS_ENTRY])
        (url, _checksum, path), = self.downloads
        self.assertEqual(path, os.path.join(self.workdir.name, "test.hdf"))
        self.assertEqual(url, urllib_url(VIS_ENTRY["filename"]))

    def test_file_rejected_with_multi_file_n(self):
        """--n > 1 together with --file is still a hard error."""
        with self.assertRaises(RuntimeError) as ctx:
            self.run_main("--raw", "--n", "3", "--file", "test.hdf",
                          raw=[RAW_ENTRY])
        self.assertIn("--n > 1", str(ctx.exception))
        self.assertEqual(self.downloads, [])

    def test_matching_existing_file_is_skipped(self):
        """Re-running with --file is idempotent (checksum match = skip)."""
        path = os.path.join(self.workdir.name, "test.hdf")
        payload = b"already downloaded"
        with open(path, "wb") as fp:
            fp.write(payload)
        checksum = hashlib.sha256(payload).hexdigest()
        self.run_main("--raw", "--file", "test.hdf",
                      raw=[dict(RAW_ENTRY, checksum=checksum)])
        self.assertEqual(self.downloads, [])
        self.assertEqual(self.api.polls, 1)

    # --- loop-exit behaviour ---------------------------------------------

    def test_positive_n_stops_after_n_downloads(self):
        """--n N downloads N files and returns (the loop still exits)."""
        names = [f"raw_{i:05d}.hdf" for i in range(4)]
        self.run_main("--raw", "--n", "2", raw=[entry(n) for n in names])
        self.assertEqual(self.downloaded_names(), names[:2])
        self.assertEqual(self.api.polls, 1)
        self.assertEqual(self.sleeps, [])

    def test_default_n_keeps_polling(self):
        """The default --n -1 is a poller: it must not return after one pass."""
        with self.assertRaises(StopPolling):
            self.run_main("--raw", raw=[RAW_ENTRY], max_polls=3)
        # Three completed polls and three "Pausing." sleeps: no break at -1.
        self.assertEqual(self.api.polls, 3)
        self.assertEqual(len(self.sleeps), 3)
        # Without --file the telescope's own name is preserved.
        self.assertEqual(self.downloaded_names(), [RAW_ENTRY["filename"]] * 3)

    def test_n_zero_still_polls(self):
        """A non-positive --n never stops (same as the default)."""
        with self.assertRaises(StopPolling):
            self.run_main("--raw", "--n", "0", raw=[], max_polls=3)
        self.assertEqual(self.api.polls, 3)
        self.assertEqual(len(self.sleeps), 3)


if __name__ == "__main__":
    unittest.main()
