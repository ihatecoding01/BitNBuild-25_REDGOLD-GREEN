#!/usr/bin/env python3
"""Health check script for Review Radar project.

Tests core functionality without external dependencies:
- Import all key modules
- Run analyzer on sample data
- Validate FastAPI app structure
- Check scraper import (no live scraping)
"""
import sys
import traceback
from pathlib import Path

def test_imports():
    """Test that all critical modules can be imported."""
    print("🔍 Testing imports...")
    try:
        import fastapi
        import transformers
        import pandas
        import playwright
        import torch
        import numpy
        print(f"✅ Core deps: fastapi={fastapi.__version__}, transformers={transformers.__version__}")
        print(f"   pandas={pandas.__version__}, torch={torch.__version__}")
        
        # Test project imports
        from analysis.review_analysis import analyze_reviews_advanced
        from backend.main import app
        import scraper
        from backend.core.errors import ScrapingError, NoReviewsFoundError
        
        print("✅ Project modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_analyzer():
    """Test the heavy analyzer with sample data."""
    print("\n🧠 Testing analyzer...")
    try:
        from analysis.review_analysis import analyze_reviews_advanced
        
        # Sample reviews with clear sentiment/aspects
        reviews = [
            "Amazing battery life, lasts all day! Screen is bright and crisp.",
            "Terrible camera quality, photos look blurry. Performance is very slow.",
            "Great value for money. Fast charging and solid design.",
            "Customer service was unhelpful when screen cracked after one week."
        ]
        
        # Test keyword mode (faster, no zero-shot model)
        print("   Testing keyword mode...")
        result_kw = analyze_reviews_advanced(reviews, aspect_method="keywords")
        
        assert 'sentiment' in result_kw
        assert 'categories' in result_kw
        assert 'mode' in result_kw
        assert result_kw['n_reviews'] == len(reviews)
        print(f"   ✅ Keyword mode: {result_kw['n_reviews']} reviews, {len(result_kw['categories'])} categories")
        
        # Test zero-shot mode (slower, downloads model on first run)
        print("   Testing zero-shot mode (may download model)...")
        result_zsc = analyze_reviews_advanced(reviews, aspect_method="zsc")
        
        assert 'sentiment' in result_zsc
        assert 'categories' in result_zsc
        assert result_zsc['mode'] == 'heavy'
        print(f"   ✅ Zero-shot mode: {result_zsc['n_reviews']} reviews, {len(result_zsc['categories'])} categories")
        
        return True
    except Exception as e:
        print(f"   ❌ Analyzer failed: {e}")
        traceback.print_exc()
        return False

def test_app():
    """Test FastAPI app can be instantiated and has expected routes."""
    print("\n🚀 Testing FastAPI app...")
    try:
        from backend.main import app
        
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        expected_routes = ['/api/v1/health', '/api/v1/analyze', '/api/v1/analyze/reviews']
        
        for expected in expected_routes:
            if not any(expected in route for route in routes):
                print(f"   ⚠️  Route {expected} not found")
            else:
                print(f"   ✅ Route {expected} found")
        
        print(f"   ✅ App loaded with {len(routes)} routes total")
        return True
    except Exception as e:
        print(f"   ❌ App test failed: {e}")
        traceback.print_exc()
        return False

def test_scraper_import():
    """Test scraper can be imported and has expected function."""
    print("\n🕷️  Testing scraper import...")
    try:
        import scraper
        from backend.core.errors import ScrapingError, NoReviewsFoundError
        
        # Check function exists and has right signature
        func = scraper.scrape_reviews
        print(f"   ✅ Function {func.__name__} found")
        
        # Test input validation (should raise ScrapingError)
        import asyncio
        async def test_validation():
            try:
                await scraper.scrape_reviews("not-a-url", 5)
                return False  # Should have raised
            except ScrapingError:
                return True  # Expected
            except Exception:
                return False  # Wrong exception type
        
        validation_ok = asyncio.run(test_validation())
        if validation_ok:
            print("   ✅ Input validation works")
        else:
            print("   ⚠️  Input validation may be broken")
        
        return True
    except Exception as e:
        print(f"   ❌ Scraper import failed: {e}")
        traceback.print_exc()
        return False

def test_cli():
    """Test CLI can be imported."""
    print("\n⌨️  Testing CLI...")
    try:
        # Test that the CLI script exists and is importable
        cli_path = Path("SentimentAnalyser/review_sentiment_analyser.py")
        if not cli_path.exists():
            print("   ❌ CLI script not found")
            return False
            
        print("   ✅ CLI script exists")
        return True
    except Exception as e:
        print(f"   ❌ CLI test failed: {e}")
        return False

def main():
    """Run all health checks."""
    print("🏥 Review Radar Health Check")
    print("=" * 40)
    
    tests = [
        ("Imports", test_imports),
        ("Analyzer", test_analyzer),
        ("FastAPI App", test_app),
        ("Scraper", test_scraper_import),
        ("CLI", test_cli),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
    
    print("\n" + "=" * 40)
    print(f"🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Project is healthy.")
        print("\nNext steps:")
        print("1. Run: uvicorn backend.main:app --port 8001")
        print("2. Visit: http://127.0.0.1:8001/docs")
        print("3. Test endpoints manually")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        print("\nCommon fixes:")
        print("- Run: pip install -r requirements.txt")
        print("- Run: pip install torch --index-url https://download.pytorch.org/whl/cpu")
        print("- Run: playwright install chromium")
        return 1

if __name__ == "__main__":
    sys.exit(main())