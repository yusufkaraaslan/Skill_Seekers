#!/usr/bin/env python3
"""
Skill Seekers Config API
FastAPI backend for listing available skill configs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Dict, Any, Optional
import os
from pathlib import Path

from config_analyzer import ConfigAnalyzer

app = FastAPI(
    title="Skill Seekers Config API",
    description="API for discovering and downloading Skill Seekers configuration files",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - allow all origins for public API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize config analyzer
# Try configs_repo first (production), fallback to configs (local development)
CONFIG_DIR = Path(__file__).parent / "configs_repo" / "official"
if not CONFIG_DIR.exists():
    CONFIG_DIR = Path(__file__).parent.parent / "configs"

analyzer = ConfigAnalyzer(CONFIG_DIR)


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Skill Seekers Config API",
        "version": "1.0.0",
        "endpoints": {
            "/api/configs": "List all available configs",
            "/api/configs/{name}": "Get specific config details",
            "/api/categories": "List all categories",
            "/api/download/{name}": "Download config file",
            "/docs": "API documentation",
        },
        "repository": "https://github.com/yusufkaraaslan/Skill_Seekers",
        "configs_repository": "https://github.com/yusufkaraaslan/skill-seekers-configs",
        "website": "https://api.skillseekersweb.com"
    }


@app.get("/api/configs")
async def list_configs(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    type: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all available configs with metadata

    Query Parameters:
    - category: Filter by category (e.g., "web-frameworks")
    - tag: Filter by tag (e.g., "javascript")
    - type: Filter by type ("single-source" or "unified")

    Returns:
    - version: API version
    - total: Total number of configs
    - filters: Applied filters
    - configs: List of config metadata
    """
    try:
        # Get all configs
        all_configs = analyzer.analyze_all_configs()

        # Apply filters
        configs = all_configs
        filters_applied = {}

        if category:
            configs = [c for c in configs if c.get("category") == category]
            filters_applied["category"] = category

        if tag:
            configs = [c for c in configs if tag in c.get("tags", [])]
            filters_applied["tag"] = tag

        if type:
            configs = [c for c in configs if c.get("type") == type]
            filters_applied["type"] = type

        return {
            "version": "1.0.0",
            "total": len(configs),
            "filters": filters_applied if filters_applied else None,
            "configs": configs
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing configs: {str(e)}")


@app.get("/api/configs/{name}")
async def get_config(name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific config

    Path Parameters:
    - name: Config name (e.g., "react", "django")

    Returns:
    - Full config metadata including all fields
    """
    try:
        config = analyzer.get_config_by_name(name)

        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Config '{name}' not found"
            )

        return config

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading config: {str(e)}")


@app.get("/api/categories")
async def list_categories() -> Dict[str, Any]:
    """
    List all available categories with config counts

    Returns:
    - categories: Dict of category names to config counts
    - total_categories: Total number of categories
    """
    try:
        configs = analyzer.analyze_all_configs()

        # Count configs per category
        category_counts = {}
        for config in configs:
            cat = config.get("category", "uncategorized")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "total_categories": len(category_counts),
            "categories": category_counts
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing categories: {str(e)}")


@app.get("/api/download/{config_name}")
async def download_config(config_name: str):
    """
    Download a specific config file

    Path Parameters:
    - config_name: Config filename (e.g., "react.json", "django.json")

    Returns:
    - JSON file for download
    """
    try:
        # Validate filename (prevent directory traversal)
        if ".." in config_name or "/" in config_name or "\\" in config_name:
            raise HTTPException(status_code=400, detail="Invalid config name")

        # Ensure .json extension
        if not config_name.endswith(".json"):
            config_name = f"{config_name}.json"

        # Search recursively in all subdirectories
        config_path = None
        for found_path in CONFIG_DIR.rglob(config_name):
            config_path = found_path
            break

        if not config_path or not config_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Config file '{config_name}' not found"
            )

        return FileResponse(
            path=config_path,
            media_type="application/json",
            filename=config_name
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading config: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "skill-seekers-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
