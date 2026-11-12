# -*- coding: utf-8 -*-
import sys
import os
import pytest
from unittest.mock import AsyncMock, patch
sys.path.insert(0, os.path.abspath("."))

from services.image_search import AnimeImageSearchService, AnimeSearchResult

@pytest.mark.asyncio
async def test_search_by_image_gemini_vision_fallback():
    service = AnimeImageSearchService()
    
    mock_gemini_response = {
        "found": True,
        "title_english": "Solo Leveling",
        "title_romaji": "Ore dake Level Up na Ken",
        "title_japanese": "俺だけレベルアップな件",
        "title_uzbek": "Solo Leveling (Yakka Darajalash)",
        "character_name": "Sung Jin-woo",
        "confidence": 98,
        "genres": "Jangari, Fantaziya",
        "is_adult": False
    }
    
    with patch.object(service, "_query_trace_moe", new_callable=AsyncMock) as mock_trace, \
         patch.object(service, "_query_gemini_vision", new_callable=AsyncMock) as mock_gemini, \
         patch.object(service, "_match_local_db", new_callable=AsyncMock) as mock_db:
         
        mock_trace.return_value = None
        mock_gemini.return_value = mock_gemini_response
        mock_db.return_value = None
        
        result = await service.search_by_image(b"fake_image_bytes")
        
        assert result.status == "high_confidence"
        assert result.title_english == "Solo Leveling"
        assert result.title_romaji == "Ore dake Level Up na Ken"
        assert result.title_japanese == "俺だけレベルアップな件"
        assert "Solo Leveling" in result.title_uzbek
        assert result.character_name == "Sung Jin-woo"
        assert result.similarity_percent == 98

@pytest.mark.asyncio
async def test_search_by_image_18_plus_filtered():
    service = AnimeImageSearchService()
    
    mock_gemini_adult = {
        "found": True,
        "title_english": "Explicit Anime",
        "title_romaji": "Explicit Anime",
        "title_japanese": "...",
        "title_uzbek": "...",
        "is_adult": True
    }
    
    with patch.object(service, "_query_trace_moe", new_callable=AsyncMock) as mock_trace, \
         patch.object(service, "_query_gemini_vision", new_callable=AsyncMock) as mock_gemini:
         
        mock_trace.return_value = None
        mock_gemini.return_value = mock_gemini_adult
        
        result = await service.search_by_image(b"fake_image_bytes")
        assert result.status == "error"
        assert result.raw_error == "18_plus_filtered"
