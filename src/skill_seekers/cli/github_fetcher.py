"""
GitHub Three-Stream Fetcher

Fetches from GitHub and splits into 3 streams:
- Stream 1: Code (for C3.x analysis)
- Stream 2: Documentation (README, CONTRIBUTING, docs/*.md)
- Stream 3: Insights (issues, metadata)

This is the foundation of the unified codebase analyzer architecture.
"""

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import Counter
import requests


@dataclass
class CodeStream:
    """Code files for C3.x analysis."""
    directory: Path
    files: List[Path]


@dataclass
class DocsStream:
    """Documentation files from repository."""
    readme: Optional[str]
    contributing: Optional[str]
    docs_files: List[Dict]  # [{"path": "docs/oauth.md", "content": "..."}]


@dataclass
class InsightsStream:
    """GitHub metadata and issues."""
    metadata: Dict  # stars, forks, language, etc.
    common_problems: List[Dict]
    known_solutions: List[Dict]
    top_labels: List[Dict]


@dataclass
class ThreeStreamData:
    """Complete output from GitHub fetcher."""
    code_stream: CodeStream
    docs_stream: DocsStream
    insights_stream: InsightsStream


class GitHubThreeStreamFetcher:
    """
    Fetch from GitHub and split into 3 streams.

    Usage:
        fetcher = GitHubThreeStreamFetcher(
            repo_url="https://github.com/facebook/react",
            github_token=os.getenv('GITHUB_TOKEN')
        )

        three_streams = fetcher.fetch()

        # Now you have:
        # - three_streams.code_stream (for C3.x)
        # - three_streams.docs_stream (for doc parser)
        # - three_streams.insights_stream (for issue analyzer)
    """

    def __init__(self, repo_url: str, github_token: Optional[str] = None):
        """
        Initialize fetcher.

        Args:
            repo_url: GitHub repository URL (e.g., https://github.com/owner/repo)
            github_token: Optional GitHub API token for higher rate limits
        """
        self.repo_url = repo_url
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.owner, self.repo = self.parse_repo_url(repo_url)

    def parse_repo_url(self, url: str) -> Tuple[str, str]:
        """
        Parse GitHub URL to extract owner and repo.

        Args:
            url: GitHub URL (https://github.com/owner/repo or git@github.com:owner/repo.git)

        Returns:
            Tuple of (owner, repo)
        """
        # Remove .git suffix if present
        if url.endswith('.git'):
            url = url[:-4]  # Remove last 4 characters (.git)

        # Handle git@ URLs (SSH format)
        if url.startswith('git@github.com:'):
            parts = url.replace('git@github.com:', '').split('/')
            if len(parts) >= 2:
                return parts[0], parts[1]

        # Handle HTTPS URLs
        if 'github.com/' in url:
            parts = url.split('github.com/')[-1].split('/')
            if len(parts) >= 2:
                return parts[0], parts[1]

        raise ValueError(f"Invalid GitHub URL: {url}")

    def fetch(self, output_dir: Path = None) -> ThreeStreamData:
        """
        Fetch everything and split into 3 streams.

        Args:
            output_dir: Directory to clone repository to (default: /tmp)

        Returns:
            ThreeStreamData with all 3 streams
        """
        if output_dir is None:
            output_dir = Path(tempfile.mkdtemp(prefix='github_fetch_'))

        print(f"📦 Cloning {self.repo_url}...")
        local_path = self.clone_repo(output_dir)

        print(f"🔍 Fetching GitHub metadata...")
        metadata = self.fetch_github_metadata()

        print(f"🐛 Fetching issues...")
        issues = self.fetch_issues(max_issues=100)

        print(f"📂 Classifying files...")
        code_files, doc_files = self.classify_files(local_path)
        print(f"  - Code: {len(code_files)} files")
        print(f"  - Docs: {len(doc_files)} files")

        print(f"📊 Analyzing {len(issues)} issues...")
        issue_insights = self.analyze_issues(issues)

        # Build three streams
        return ThreeStreamData(
            code_stream=CodeStream(
                directory=local_path,
                files=code_files
            ),
            docs_stream=DocsStream(
                readme=self.read_file(local_path / 'README.md'),
                contributing=self.read_file(local_path / 'CONTRIBUTING.md'),
                docs_files=[
                    {'path': str(f.relative_to(local_path)), 'content': self.read_file(f)}
                    for f in doc_files
                    if f.name not in ['README.md', 'CONTRIBUTING.md']
                ]
            ),
            insights_stream=InsightsStream(
                metadata=metadata,
                common_problems=issue_insights['common_problems'],
                known_solutions=issue_insights['known_solutions'],
                top_labels=issue_insights['top_labels']
            )
        )

    def clone_repo(self, output_dir: Path) -> Path:
        """
        Clone repository to local directory.

        Args:
            output_dir: Parent directory for clone

        Returns:
            Path to cloned repository
        """
        repo_dir = output_dir / self.repo
        repo_dir.mkdir(parents=True, exist_ok=True)

        # Clone with depth 1 for speed
        cmd = ['git', 'clone', '--depth', '1', self.repo_url, str(repo_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Failed to clone repository: {result.stderr}")

        return repo_dir

    def fetch_github_metadata(self) -> Dict:
        """
        Fetch repo metadata via GitHub API.

        Returns:
            Dict with stars, forks, language, open_issues, etc.
        """
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}"
        headers = {}
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            return {
                'stars': data.get('stargazers_count', 0),
                'forks': data.get('forks_count', 0),
                'open_issues': data.get('open_issues_count', 0),
                'language': data.get('language', 'Unknown'),
                'description': data.get('description', ''),
                'homepage': data.get('homepage', ''),
                'created_at': data.get('created_at', ''),
                'updated_at': data.get('updated_at', ''),
                'html_url': data.get('html_url', ''),  # NEW: Repository URL
                'license': data.get('license', {})  # NEW: License info
            }
        except Exception as e:
            print(f"⚠️  Failed to fetch metadata: {e}")
            return {
                'stars': 0,
                'forks': 0,
                'open_issues': 0,
                'language': 'Unknown',
                'description': '',
                'homepage': '',
                'created_at': '',
                'updated_at': '',
                'html_url': '',  # NEW: Repository URL
                'license': {}  # NEW: License info
            }

    def fetch_issues(self, max_issues: int = 100) -> List[Dict]:
        """
        Fetch GitHub issues (open + closed).

        Args:
            max_issues: Maximum number of issues to fetch

        Returns:
            List of issue dicts
        """
        all_issues = []

        # Fetch open issues
        all_issues.extend(self._fetch_issues_page(state='open', max_count=max_issues // 2))

        # Fetch closed issues
        all_issues.extend(self._fetch_issues_page(state='closed', max_count=max_issues // 2))

        return all_issues

    def _fetch_issues_page(self, state: str, max_count: int) -> List[Dict]:
        """
        Fetch one page of issues.

        Args:
            state: 'open' or 'closed'
            max_count: Maximum issues to fetch

        Returns:
            List of issues
        """
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues"
        headers = {}
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'

        params = {
            'state': state,
            'per_page': min(max_count, 100),  # GitHub API limit
            'sort': 'comments',
            'direction': 'desc'
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            issues = response.json()

            # Filter out pull requests (they appear in issues endpoint)
            issues = [issue for issue in issues if 'pull_request' not in issue]

            return issues
        except Exception as e:
            print(f"⚠️  Failed to fetch {state} issues: {e}")
            return []

    def classify_files(self, repo_path: Path) -> Tuple[List[Path], List[Path]]:
        """
        Split files into code vs documentation.

        Code patterns:
        - *.py, *.js, *.ts, *.go, *.rs, *.java, etc.
        - In src/, lib/, pkg/, etc.

        Doc patterns:
        - README.md, CONTRIBUTING.md, CHANGELOG.md
        - docs/**/*.md, doc/**/*.md
        - *.rst (reStructuredText)

        Args:
            repo_path: Path to repository

        Returns:
            Tuple of (code_files, doc_files)
        """
        code_files = []
        doc_files = []

        # Documentation patterns
        doc_patterns = [
            '**/README.md',
            '**/CONTRIBUTING.md',
            '**/CHANGELOG.md',
            '**/LICENSE.md',
            'docs/*.md',            # Files directly in docs/
            'docs/**/*.md',          # Files in subdirectories of docs/
            'doc/*.md',              # Files directly in doc/
            'doc/**/*.md',            # Files in subdirectories of doc/
            'documentation/*.md',     # Files directly in documentation/
            'documentation/**/*.md',  # Files in subdirectories of documentation/
            '**/*.rst',
        ]

        # Code extensions
        code_extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx',
            '.go', '.rs', '.java', '.kt',
            '.c', '.cpp', '.h', '.hpp',
            '.rb', '.php', '.swift', '.cs',
            '.scala', '.clj', '.cljs'
        ]

        # Directories to exclude
        exclude_dirs = [
            'node_modules', '__pycache__', 'venv', '.venv',
            '.git', 'build', 'dist', '.tox', '.pytest_cache',
            'htmlcov', '.mypy_cache', '.eggs', '*.egg-info'
        ]

        for file_path in repo_path.rglob('*'):
            if not file_path.is_file():
                continue

            # Check excluded directories first
            if any(exclude in str(file_path) for exclude in exclude_dirs):
                continue

            # Skip hidden files (but allow docs in docs/ directories)
            is_in_docs_dir = any(pattern in str(file_path) for pattern in ['docs/', 'doc/', 'documentation/'])
            if any(part.startswith('.') for part in file_path.parts):
                if not is_in_docs_dir:
                    continue

            # Check if documentation
            is_doc = any(file_path.match(pattern) for pattern in doc_patterns)

            if is_doc:
                doc_files.append(file_path)
            elif file_path.suffix in code_extensions:
                code_files.append(file_path)

        return code_files, doc_files

    def analyze_issues(self, issues: List[Dict]) -> Dict:
        """
        Analyze GitHub issues to extract insights.

        Returns:
        {
            "common_problems": [
                {
                    "title": "OAuth setup fails",
                    "number": 42,
                    "labels": ["question", "oauth"],
                    "comments": 15,
                    "state": "open"
                },
                ...
            ],
            "known_solutions": [
                {
                    "title": "Fixed OAuth redirect",
                    "number": 35,
                    "labels": ["bug", "oauth"],
                    "comments": 8,
                    "state": "closed"
                },
                ...
            ],
            "top_labels": [
                {"label": "question", "count": 23},
                {"label": "bug", "count": 15},
                ...
            ]
        }
        """
        common_problems = []
        known_solutions = []
        all_labels = []

        for issue in issues:
            # Handle both string labels and dict labels (GitHub API format)
            raw_labels = issue.get('labels', [])
            labels = []
            for label in raw_labels:
                if isinstance(label, dict):
                    labels.append(label.get('name', ''))
                else:
                    labels.append(str(label))
            all_labels.extend(labels)

            issue_data = {
                'title': issue.get('title', ''),
                'number': issue.get('number', 0),
                'labels': labels,
                'comments': issue.get('comments', 0),
                'state': issue.get('state', 'unknown')
            }

            # Open issues with many comments = common problems
            if issue['state'] == 'open' and issue.get('comments', 0) >= 5:
                common_problems.append(issue_data)

            # Closed issues with comments = known solutions
            elif issue['state'] == 'closed' and issue.get('comments', 0) > 0:
                known_solutions.append(issue_data)

        # Count label frequency
        label_counts = Counter(all_labels)

        return {
            'common_problems': sorted(common_problems, key=lambda x: x['comments'], reverse=True)[:10],
            'known_solutions': sorted(known_solutions, key=lambda x: x['comments'], reverse=True)[:10],
            'top_labels': [
                {'label': label, 'count': count}
                for label, count in label_counts.most_common(10)
            ]
        }

    def read_file(self, file_path: Path) -> Optional[str]:
        """
        Read file content safely.

        Args:
            file_path: Path to file

        Returns:
            File content or None if file doesn't exist or can't be read
        """
        if not file_path.exists():
            return None

        try:
            return file_path.read_text(encoding='utf-8')
        except Exception:
            # Try with different encoding
            try:
                return file_path.read_text(encoding='latin-1')
            except Exception:
                return None
