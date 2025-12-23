"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_articles():
    """Sample article data for tests."""
    return [
        {
            "news_id": "001",
            "title": "AI 기술 혁신이 산업 전반을 변화시키다",
            "publisher": "경향신문",
            "date": "2025-01-01",
            "summary": "인공지능 기술이 다양한 산업 분야에서 혁신을 이끌고 있습니다.",
        },
        {
            "news_id": "002",
            "title": "글로벌 경제 전망과 한국의 대응",
            "publisher": "조선일보",
            "date": "2025-01-02",
            "summary": "세계 경제 전문가들이 2025년 경제 전망을 발표했습니다.",
        },
    ]


@pytest.fixture
def sample_issues():
    """Sample trending issues for tests."""
    return [
        {"rank": 1, "title": "AI 혁명", "keywords": ["인공지능", "기술", "혁신"]},
        {"rank": 2, "title": "기후 변화", "keywords": ["환경", "탄소중립", "에너지"]},
        {"rank": 3, "title": "경제 전망", "keywords": ["금리", "인플레이션", "성장"]},
    ]
