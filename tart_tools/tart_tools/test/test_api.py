"""
Test the AuthorizedAPIhandler

"""
#
# Copyright (c) Tim Molteno 2023. tim@elec.ac.nz
#


import unittest
import time

from tart_tools.api_handler import AuthorizedAPIhandler



class TestApi(unittest.TestCase):

    def setUp(self):
        self.api = 'https://tart.elec.ac.nz/signal'
        self.pw = 'sharkbait'
        
    def test_auth(self):
        # Test the expiration of the auth token and that it is refreshed correctly
        api = AuthorizedAPIhandler(self.api, self.pw)
        resp = api.post_with_token(f"mode/vis")
        for i in range(11):
            time.sleep(120)
            resp = api.post_with_token(f"mode/vis")
            print(f"response {resp}")
            
        self.assertAlmostEqual(resp, 0)
