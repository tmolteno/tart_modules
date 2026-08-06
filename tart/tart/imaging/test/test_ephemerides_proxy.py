import datetime
import json
import socket
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import numpy as np

from tart.imaging import ephemerides_proxy
from tart.util import utc


class MockJSONRPCServer:
    """A minimal JSON-RPC 2.0 server used to test the client.

    Records every request it receives and answers based on the method:
    'get_ephemeris' returns a result, 'rpc_error' returns a JSON-RPC error
    response, and 'http_error' returns an HTTP 500 with a JSON-RPC error
    body.
    """

    def __init__(self):
        self.requests = []
        self._server = HTTPServer(("127.0.0.1", 0), self._handler_factory())
        self.port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def url(self):
        return f"http://127.0.0.1:{self.port}/rpc/gps"

    def start(self):
        self._thread.start()

    def stop(self):
        self._server.shutdown()
        self._server.server_close()

    def _handler_factory(self):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers["Content-Length"])
                request = json.loads(self.rfile.read(length).decode("utf-8"))
                outer.requests.append(request)
                outer.respond(request, self)

            def log_message(self, *args):
                pass

        return Handler

    def respond(self, request, handler):
        method = request["method"]
        params = request["params"]
        if method == "get_ephemeris":
            sv = params[1] if isinstance(params, list) else params.get("sv")
            result = {"svprn": sv, "toe": 345600.0}
        elif method == "rpc_error":
            self._send(
                handler,
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "boom"},
                    "id": request["id"],
                },
            )
            return
        elif method == "http_error":
            self._send(
                handler,
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": "method not found"},
                    "id": request["id"],
                },
                status=500,
            )
            return
        else:
            result = None
        self._send(
            handler, {"jsonrpc": "2.0", "result": result, "id": request["id"]}
        )

    @staticmethod
    def _send(handler, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)


def _closed_port():
    """Return a localhost port that nothing is listening on."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class TestEphemeridesProxy(unittest.TestCase):
    def setUp(self):
        self.ep = ephemerides_proxy.EphemeridesProxy.Instance()
        try:
            self.ep.server.get_ephemeris(
                utc.utc_datetime(2013, 9, 21, 0, 59, 3).isoformat(), 1
            )
        except Exception:
            self.skipTest("Ephemeris server (localhost:8876) not available")

    def test_proxying(self):
        t = utc.utc_datetime(2013, 9, 21, 0, 59, 3)
        sv = 21
        for i in range(100):
            t = t + datetime.timedelta(seconds=1.0)
            pos = self.ep.get_sv_position(t, sv)
            pos_remote = self.ep.get_remote_position(t, sv)
            diff = np.array(pos) - np.array(pos_remote)
            dr = np.sqrt(diff.dot(diff))
            if dr > 3.0:
                print("test_proxying %i %s %f %s %s" % (i, t, dr, pos, pos_remote))
            self.assertLess(dr, 3.0)  # Maximum difference of 3 meters

    # TODO sp3 orbit interpolation from the precise sp3 positions
    # Eg at ftp://cddis.gsfc.nasa.gov/pub/gps/products/1172/
    # or ftp://nfs.kasi.re.kr/glonass/products/1355/
    # And compare against predicted files. There is a BUG in
    # the ephemeris file.

    # def test_all_positions(self):
    # t = utc.utc_datetime(2012, 10, 31, 0, 2, 2)
    # for i in range(0,10):
    # t = t + datetime.timedelta(seconds=100.0)
    # pos = self.ep.get_sv_positions(t)

    def test_cache_jump(self):
        t1 = utc.utc_datetime(2013, 9, 21, 0, 59, 3)
        t = utc.utc_datetime(2013, 9, 21, 0, 59, 3)
        sv = 21
        p1 = self.ep.get_sv_position(t1, sv)
        for i in range(100):
            t = t + datetime.timedelta(seconds=1.0)
            p2 = self.ep.get_sv_position(t, sv)
            diff = np.array(p2) - np.array(p1)
            dr = np.sqrt(diff.dot(diff))
            if dr > 1000:
                print("test_cache_jump %i %s %f" % (i, p2, dr))
            self.assertLess(dr, 3000.0 * (i + 1))

    def test_sp3_proxying(self):
        t = utc.utc_datetime(2013, 9, 21, 0, 59, 3)
        sv = 21
        for i in range(100):
            t = t + datetime.timedelta(seconds=1.0)
            pos = self.ep.get_sv_position_sp3(t, sv)
            pos_remote = self.ep.get_remote_position(t, sv)
            diff = np.array(pos) - np.array(pos_remote)
            dr = np.sqrt(diff.dot(diff))
            if dr > 1.0:
                print("test_sp3_proxying %i %s %f %s %s" % (i, t, dr, pos, pos_remote))
            self.assertLess(dr, 1.0)  # Maximum difference of 1 meters


class TestServerProxy(unittest.TestCase):
    """Unit tests for the in-house JSON-RPC 2.0 client (ServerProxy)."""

    def setUp(self):
        self.server = MockJSONRPCServer()
        self.server.start()
        self.proxy = ephemerides_proxy.ServerProxy(self.server.url())

    def tearDown(self):
        self.server.stop()

    def test_request_wire_format(self):
        """Requests must match the JSON-RPC 2.0 format that jsonrpclib used."""
        self.proxy.get_ephemeris("2013-09-21T00:59:03+00:00", 21)
        request = self.server.requests[-1]
        self.assertEqual(request["jsonrpc"], "2.0")
        self.assertEqual(request["method"], "get_ephemeris")
        self.assertEqual(request["params"], ["2013-09-21T00:59:03+00:00", 21])
        self.assertEqual(request["id"], 1)

    def test_positional_params_and_incrementing_ids(self):
        self.proxy.get_ephemeris("a", 1)
        self.proxy.get_interp_points("b")
        self.assertEqual(self.server.requests[0]["id"], 1)
        self.assertEqual(self.server.requests[1]["id"], 2)
        self.assertEqual(self.server.requests[1]["method"], "get_interp_points")
        self.assertEqual(self.server.requests[1]["params"], ["b"])

    def test_keyword_params(self):
        self.proxy.get_ephemeris(date="2013-09-21T00:59:03+00:00", sv=21)
        request = self.server.requests[-1]
        self.assertEqual(
            request["params"],
            {"date": "2013-09-21T00:59:03+00:00", "sv": 21},
        )

    def test_result(self):
        result = self.proxy.get_ephemeris("2013-09-21T00:59:03+00:00", 21)
        self.assertEqual(result, {"svprn": 21, "toe": 345600.0})

    def test_rpc_error_raises_protocol_error(self):
        with self.assertRaises(ephemerides_proxy.ProtocolError) as cm:
            self.proxy.rpc_error()
        self.assertEqual(cm.exception.code, -32000)
        self.assertEqual(cm.exception.message, "boom")

    def test_http_error_raises_protocol_error(self):
        with self.assertRaises(ephemerides_proxy.ProtocolError) as cm:
            self.proxy.http_error()
        self.assertEqual(cm.exception.code, -32601)

    def test_connection_refused_raises(self):
        proxy = ephemerides_proxy.ServerProxy(
            f"http://127.0.0.1:{_closed_port()}/rpc/gps"
        )
        with self.assertRaises(OSError):
            proxy.get_ephemeris("2013-09-21T00:59:03+00:00", 21)
