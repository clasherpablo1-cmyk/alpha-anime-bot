# -*- coding: utf-8 -*-
"""
tests/test_mongo.py — Unit tests for MongoDB Atlas Manager & Circuit Breaker.
"""

import asyncio
import os
import sys
import unittest
from pathlib import Path

# Add root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.mongo_manager import MongoCircuitBreaker, MongoManager
from config import config


class TestMongoManager(unittest.IsolatedAsyncioTestCase):
    def test_circuit_breaker_logic(self):
        cb = MongoCircuitBreaker(failure_threshold=3, cooldown_seconds=1.0)
        self.assertTrue(cb.allow_request())
        self.assertFalse(cb.is_open)

        # 2 failures
        cb.record_failure(Exception("Fail 1"))
        cb.record_failure(Exception("Fail 2"))
        self.assertFalse(cb.is_open)
        self.assertTrue(cb.allow_request())

        # 3rd failure trips the breaker
        cb.record_failure(Exception("Fail 3"))
        self.assertTrue(cb.is_open)

        # Success resets
        cb.record_success()
        self.assertFalse(cb.is_open)
        self.assertEqual(cb.failure_count, 0)

    async def test_mongo_graceful_fallback(self):
        original_uri = config.MONGODB_URI
        try:
            config.MONGODB_URI = ""
            mgr = MongoManager()
            # When unconfigured, should not fail or crash
            self.assertFalse(mgr.is_configured)
            res = await mgr.connect()
            self.assertFalse(res)

            # Upserts should return False safely without throwing exceptions
            self.assertFalse(await mgr.upsert_user({"id": 12345}))
            self.assertFalse(await mgr.upsert_anime({"code": 1}))
            self.assertFalse(await mgr.upsert_episode({"anime_id": 1, "episode_number": 1}))
        finally:
            config.MONGODB_URI = original_uri


if __name__ == "__main__":
    unittest.main()
