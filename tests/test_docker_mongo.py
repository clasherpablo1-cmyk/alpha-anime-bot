# -*- coding: utf-8 -*-
import pytest
from unittest.mock import AsyncMock, patch
from database.mongo_manager import MongoManager
from config import config

@pytest.mark.asyncio
async def test_mongo_manager_local_docker_uri():
    """Verify that MongoManager properly configures client for local non-SSL Docker MongoDB."""
    manager = MongoManager()
    
    with patch("config.config.MONGODB_URI", "mongodb://alpha_admin:alpha_anime_2026_pass@localhost:27027/AlphaAnimeBotDB?authSource=admin"):
        assert manager.is_configured is True
        
        # Test connecting with mock to verify tlsCAFile is NOT set for non-TLS Docker connection
        with patch("database.mongo_manager.AsyncIOMotorClient") as mock_motor:
            mock_client = AsyncMock()
            mock_motor.return_value = mock_client
            mock_db = AsyncMock()
            mock_client.__getitem__.return_value = mock_db
            mock_db.command = AsyncMock(return_value={"ok": 1})
            
            with patch.object(manager, "_setup_indexes", new_callable=AsyncMock):
                success = await manager.connect()
                assert success is True
                assert manager._is_connected is True
                
                # Check call kwargs: tlsCAFile should NOT be passed for localhost non-SSL
                _, kwargs = mock_motor.call_args
                assert "tlsCAFile" not in kwargs

@pytest.mark.asyncio
async def test_mongo_manager_atlas_uri():
    """Verify that MongoManager properly configures client with tlsCAFile for Atlas SRV URI."""
    manager = MongoManager()
    
    with patch("config.config.MONGODB_URI", "mongodb+srv://user:pass@cluster.mongodb.net/?appName=Bot"):
        assert manager.is_configured is True
        
        with patch("database.mongo_manager.AsyncIOMotorClient") as mock_motor:
            mock_client = AsyncMock()
            mock_motor.return_value = mock_client
            mock_db = AsyncMock()
            mock_client.__getitem__.return_value = mock_db
            mock_db.command = AsyncMock(return_value={"ok": 1})
            
            with patch.object(manager, "_setup_indexes", new_callable=AsyncMock):
                success = await manager.connect()
                assert success is True
                
                # tlsCAFile MUST be present for mongodb+srv://
                _, kwargs = mock_motor.call_args
                assert "tlsCAFile" in kwargs
