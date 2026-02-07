#!/usr/bin/env python3
"""
HTTP Context Provider Server for Continue.dev

Serves framework documentation as Continue.dev context items.
Supports multiple frameworks from Skill Seekers output.

Usage:
    python context_server.py
    python context_server.py --host 0.0.0.0 --port 8765
"""

import argparse
from pathlib import Path
from functools import lru_cache
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


app = FastAPI(
    title="Skill Seekers Context Server",
    description="HTTP context provider for Continue.dev",
    version="1.0.0"
)

# Add CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=100)
def load_framework_docs(framework: str) -> str:
    """
    Load framework documentation from Skill Seekers output.

    Args:
        framework: Framework name (vue, react, django, etc.)

    Returns:
        Documentation content as string

    Raises:
        FileNotFoundError: If documentation not found
    """
    # Try multiple possible locations
    possible_paths = [
        Path(f"output/{framework}-markdown/SKILL.md"),
        Path(f"../../output/{framework}-markdown/SKILL.md"),
        Path(f"../../../output/{framework}-markdown/SKILL.md"),
    ]

    for doc_path in possible_paths:
        if doc_path.exists():
            with open(doc_path, 'r', encoding='utf-8') as f:
                return f.read()

    raise FileNotFoundError(
        f"Documentation not found for framework: {framework}\n"
        f"Tried paths: {[str(p) for p in possible_paths]}\n"
        f"Run: skill-seekers scrape --config configs/{framework}.json"
    )


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "Skill Seekers Context Server",
        "description": "HTTP context provider for Continue.dev",
        "version": "1.0.0",
        "endpoints": {
            "/docs/{framework}": "Get framework documentation",
            "/frameworks": "List available frameworks",
            "/health": "Health check"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/frameworks")
async def list_frameworks() -> Dict[str, List[str]]:
    """
    List available frameworks.

    Returns:
        Dictionary with available and missing frameworks
    """
    # Check common framework locations
    output_dir = Path("output")
    if not output_dir.exists():
        output_dir = Path("../../output")
    if not output_dir.exists():
        output_dir = Path("../../../output")

    if not output_dir.exists():
        return {
            "available": [],
            "message": "No output directory found. Run skill-seekers to generate documentation."
        }

    # Find all *-markdown directories
    available = []
    for item in output_dir.glob("*-markdown"):
        framework = item.name.replace("-markdown", "")
        skill_file = item / "SKILL.md"
        if skill_file.exists():
            available.append(framework)

    return {
        "available": available,
        "count": len(available),
        "usage": "GET /docs/{framework} to access documentation"
    }


@app.get("/docs/{framework}")
async def get_framework_docs(framework: str, query: str = None) -> JSONResponse:
    """
    Get framework documentation as Continue.dev context items.

    Args:
        framework: Framework name (vue, react, django, etc.)
        query: Optional search query for filtering (future feature)

    Returns:
        JSON response with contextItems array for Continue.dev
    """
    try:
        # Load documentation (cached)
        docs = load_framework_docs(framework)

        # TODO: Implement query filtering if provided
        if query:
            # Filter docs based on query (simplified)
            # In production, use better search (regex, fuzzy matching, etc.)
            pass

        # Return in Continue.dev format
        return JSONResponse({
            "contextItems": [
                {
                    "name": f"{framework.title()} Documentation",
                    "description": f"Complete {framework} framework expert knowledge",
                    "content": docs
                }
            ]
        })

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading documentation: {str(e)}"
        )


@app.get("/project/conventions")
async def get_project_conventions() -> JSONResponse:
    """
    Get project-specific conventions.

    Returns:
        JSON response with project conventions
    """
    # Load project conventions if they exist
    conventions_path = Path(".project-conventions.md")

    if conventions_path.exists():
        with open(conventions_path, 'r') as f:
            content = f.read()
    else:
        # Default conventions
        content = """
# Project Conventions

## General
- Use TypeScript for all new code
- Follow framework-specific best practices
- Write tests for all features

## Git Workflow
- Feature branch workflow
- Squash commits before merge
- Descriptive commit messages

## Code Style
- Use prettier for formatting
- ESLint for linting
- Follow team conventions
"""

    return JSONResponse({
        "contextItems": [
            {
                "name": "Project Conventions",
                "description": "Team coding standards and conventions",
                "content": content
            }
        ]
    })


def main():
    parser = argparse.ArgumentParser(
        description="HTTP Context Provider Server for Continue.dev"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1, use 0.0.0.0 for all interfaces)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to bind to (default: 8765)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (development)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Skill Seekers Context Server for Continue.dev")
    print("=" * 60)
    print(f"Server: http://{args.host}:{args.port}")
    print(f"Endpoints:")
    print(f"  - GET /                      # Server info")
    print(f"  - GET /health                # Health check")
    print(f"  - GET /frameworks            # List available frameworks")
    print(f"  - GET /docs/{{framework}}     # Get framework docs")
    print(f"  - GET /project/conventions   # Get project conventions")
    print("=" * 60)
    print(f"\nConfigure Continue.dev:")
    print(f"""
{{
  "contextProviders": [
    {{
      "name": "http",
      "params": {{
        "url": "http://{args.host}:{args.port}/docs/vue",
        "title": "vue-docs",
        "displayTitle": "Vue.js Documentation"
      }}
    }}
  ]
}}
""")
    print("=" * 60)
    print("\nPress Ctrl+C to stop\n")

    # Run server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
