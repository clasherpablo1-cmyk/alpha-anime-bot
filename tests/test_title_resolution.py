import sys
import os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from services.image_search import POPULAR_ANIME_UZ, AnimeImageSearchService
import difflib

def test_title_resolution():
    service = AnimeImageSearchService()
    
    # Test 1: Popular anime exact match
    uz1 = asyncio.run(service.get_uzbek_title("Attack on Titan", "Shingeki no Kyojin"))
    print("Test 1 (Attack on Titan):", uz1)
    assert uz1 == "Titanlar Hujumi"
    
    # Test 2: Solo Leveling
    uz2 = asyncio.run(service.get_uzbek_title("Solo Leveling", "Ore dake Level Up na Ken"))
    print("Test 2 (Solo Leveling):", uz2)
    assert "Solo Leveling" in uz2 or "Yakka" in uz2
    
    # Test 3: Unrelated anime should NOT match Naruto even if it has Drama/Action
    uz3 = asyncio.run(service.get_uzbek_title("Frieren: Beyond Journey's End", "Sousou no Frieren"))
    print("Test 3 (Frieren):", uz3)
    assert "Naruto" not in uz3
    
    # Test 4: Unknown anime should NOT be mangled by Google Translate
    uz4 = asyncio.run(service.get_uzbek_title("Acro Trip", "Acro Trip"))
    print("Test 4 (Acro Trip):", uz4)
    assert uz4 == "Acro Trip"
    
    print("All title resolution tests passed!")

if __name__ == "__main__":
    test_title_resolution()
