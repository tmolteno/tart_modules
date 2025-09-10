"""
  TART API handler class
  Tim Molteno 2017-2023 - tim@elec.ac.nz
  Max Scheel 2017 - max@max.ac.nz
"""

import hashlib
import json
import logging
import os
import shutil
import urllib.error
import urllib.parse
import urllib.request
import tempfile

import requests
from requests.adapters import HTTPAdapter
from tart.operation import settings
from tart.util import utc
from urllib3.util.retry import Retry

# Default timeout
TIMEOUT = 15.0

logger = logging.getLogger()


def sha256_checksum(filename, block_size=65536):
    sha256 = hashlib.sha256()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            sha256.update(block)
    return sha256.hexdigest()


def download_file(url, checksum=0, file_path=None):
    logger.info(f"Download_file({url}, {checksum}) -> {file_path}")

    # Download the file from `url` to a temporary file and save it locally under `file_path`:
    with urllib.request.urlopen(url) as response, tempfile.NamedTemporaryFile(delete=False) as temp_file:
        shutil.copyfileobj(response, temp_file)
    shutil.move(temp_file.name, file_path)

    if checksum:
        downloaded_checksum = sha256_checksum(file_path)
        if downloaded_checksum != checksum:
            logger.info(
                f"Removing file: Checksum failed\n{checksum}\n{downloaded_checksum}"
            )
            os.remove(file_path)


class APIhandler:
    def __init__(self, api_root):
        self.root = api_root
        self.token = None

    def url(self, path):
        return f"{self.root}/api/v1/{path}"

    def catalog_url(
        self,
        lon,  # degrees
        lat,
        catalog="https://tart.elec.ac.nz/catalog",
        datestr=None
    ):
        if datestr is None:
            datestr = utc.to_string(utc.now())
        return f"{catalog}/catalog?lat={lat}&lon={lon}&date={datestr}"

    def get(self, path):
        return self.get_url(self.url(path))

    def get_url(self, url):

        s = requests.Session()

        retries = Retry(total=5,
                        backoff_factor=1,
                        status_forcelist=[429, 500, 502, 503, 504])

        s.mount('https://', HTTPAdapter(max_retries=retries))

        r = s.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        return json.loads(r.text)


class AuthorizedAPIhandler(APIhandler):
    """
    This object allows an authorized API call.

    Example:

        from tart_tools.api_handler import AuthorizedAPIhandler

        if __name__ == '__main__':
            parser = argparse.ArgumentParser(description='Change telescope mode',
                            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
            parser.add_argument('--api', required=False, default='https://tart.elec.ac.nz/signal',
                            help="Telescope API server URL.")
            parser.add_argument('--pw', default='password', type=str, help='API password')
            parser.add_argument('--mode', type=str, required=True, help='New mode (vis/raw)')

            ARGS = parser.parse_args()

            api = AuthorizedAPIhandler(ARGS.api, ARGS.pw)

            resp = api.post_payload_with_token('mode', ARGS.mode)


    """

    def __init__(self, api_root, pw):
        APIhandler.__init__(self, api_root=api_root)
        self.pw = pw
        self.token = None
        self.refresh_token = None
        self.login()

    def login(self):
        payload_dict = {"username": "admin", "password": self.pw}
        resp_json = self.__post_payload("/auth", payload_dict=payload_dict)
        if "access_token" in resp_json:
            self.token = resp_json["access_token"]
            self.refresh_token = resp_json["refresh_token"]
        else:
            raise RuntimeError("Authorization failed. Wrong pw?")

    def refresh_access_token(self):
        r = requests.post(
            self.url("refresh"), headers=self.__get_refresh_header(), timeout=TIMEOUT
        )
        resp_json = json.loads(r.text)
        if "access_token" in resp_json:
            self.token = resp_json["access_token"]
            logger.info("refreshed token")

    def __post_payload(self, path, payload_dict):
        """ Currently only used for login() """
        r = requests.post(self.url(path), json=payload_dict, timeout=TIMEOUT)
        r.raise_for_status()
        return json.loads(r.text)

    def __get_header(self):
        if self.token is None:
            raise RuntimeError("login required")
        return {"Authorization": "JWT " + self.token}

    def __get_refresh_header(self):
        if self.refresh_token is None:
            raise RuntimeError("login required")
        return {"Authorization": "JWT " + self.refresh_token}

    # TODO: catch the requests result that corresponds to a failed login (authorization expired)
    # and re-authorize automatically.
    def put(self, path, **kwargs):
        r = requests.put(
            self.url(path), headers=self.__get_header(), timeout=TIMEOUT, **kwargs
        )
        if r.status_code in (requests.codes.unauthorized, requests.codes.internal_server_error):
            self.refresh_access_token()
            return self.put(path, **kwargs)
        logger.info(f"put response {r}")
        ret = json.loads(r.text)
        r.raise_for_status()
        return ret

    def post(self, path, **kwargs):
        r = requests.post(
            self.url(path), headers=self.__get_header(), timeout=TIMEOUT, **kwargs
        )
        if r.status_code in (requests.codes.unauthorized, requests.codes.internal_server_error):
            self.refresh_access_token()
            return self.post(path, **kwargs)
        logger.info(f"post response {r}")
        ret = json.loads(r.text)
        r.raise_for_status()
        return ret

        # #logger.info(r)
        # ret = json.loads(r.text)
        # if "status" in ret and "sub_status" in ret:
        #     if (ret["status"] == 401) and (ret["sub_status"] == 101):
        #         self.refresh_access_token()
        #         return self.post(path, **kwargs)
        # r.raise_for_status()
        # return ret

    def post_with_token(self, path):
        return self.post(path)

    def post_payload_with_token(self, path, payload_dict):
        return self.post(path, json=payload_dict)


def set_mode(api, mode):
    resp_json = api.post_with_token("mode/" + mode)
    return resp_json


def download_current_gain(api):
    gains = api.get("calibration/gain")
    return gains


def upload_gain(api, gain_dict):
    resp = api.post_payload_with_token("calibration/gain", gain_dict)
    logger.info("SUCCESS")
    return resp


def get_config(api):
    info = api.get("info")
    ant_pos = api.get("imaging/antenna_positions")
    return settings.from_api_json(info["info"], ant_pos)
