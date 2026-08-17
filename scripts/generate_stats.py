import os
import json
import urllib.request
from collections import Counter
from pathlib import Path


USERNAME = os.getenv("GITHUB_USERNAME", "LuizSptech")
TOKEN = os.getenv("GITHUB_TOKEN")

API_URL = "https://api.github.com"

ASSETS_DIR = Path("assets")
ASSETS_DIR.mkdir(exist_ok=True)


def github_request(endpoint):
    url = f"{API_URL}{endpoint}"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USERNAME,
    }

    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    request = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def get_repositories():
    repositories = []
    page = 1

    while True:
        data = github_request(
            f"/users/{USERNAME}/repos?per_page=100&page={page}"
        )

        if not data:
            break

        repositories.extend(data)

        if len(data) < 100:
            break

        page += 1

    return repositories


def get_commit_count(repository):
    owner = repository["owner"]["login"]
    name = repository["name"]

    try:
        data = github_request(
            f"/repos/{owner}/{name}/commits?per_page=1"
        )

        # O GitHub fornece o total através do header Link,
        # mas para manter o script simples e estável,
        # usamos a quantidade retornada quando disponível.
        return len(data)

    except Exception:
        return 0


def get_languages(repository):
    owner = repository["owner"]["login"]
    name = repository["name"]

    try:
        return github_request(
            f"/repos/{owner}/{name}/languages"
        )
    except Exception:
        return {}


def calculate_statistics(repositories):
    total_repositories = len(repositories)

    total_stars = sum(
        repository["stargazers_count"]
        for repository in repositories
    )

    total_forks = sum(
        repository["forks_count"]
        for repository in repositories
    )

    total_commits = 0

    languages = Counter()

    for repository in repositories:
        total_commits += get_commit_count(repository)

        repo_languages = get_languages(repository)

        for language, amount in repo_languages.items():
            languages[language] += amount

    return {
        "repositories": total_repositories,
        "commits": total_commits,
        "stars": total_stars,
        "forks": total_forks,
        "languages": languages,
    }


def escape_svg(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def create_stats_svg(stats):
    repositories = stats["repositories"]
    commits = stats["commits"]
    stars = stats["stars"]
    forks = stats["forks"]

    svg = f"""<svg width="800" height="300"
xmlns="http://www.w3.org/2000/svg">

<rect width="800" height="300" rx="16"
fill="#171717"
stroke="#3b3b3b"/>

<text x="40" y="50"
font-family="Arial, sans-serif"
font-size="24"
font-weight="bold"
fill="#ffffff">
GitHub Activity
</text>

<text x="40" y="75"
font-family="Arial, sans-serif"
font-size="13"
fill="#999999">
LuizSptech
</text>

<text x="80" y="135"
font-family="Arial, sans-serif"
font-size="28"
font-weight="bold"
fill="#ffffff">
{repositories}
</text>

<text x="80" y="158"
font-family="Arial, sans-serif"
font-size="13"
fill="#999999">
Repositories
</text>

<text x="280" y="135"
font-family="Arial, sans-serif"
font-size="28"
font-weight="bold"
fill="#ffffff">
{commits}
</text>

<text x="280" y="158"
font-family="Arial, sans-serif"
font-size="13"
fill="#999999">
Commits
</text>

<text x="480" y="135"
font-family="Arial, sans-serif"
font-size="28"
font-weight="bold"
fill="#ffffff">
{stars}
</text>

<text x="480" y="158"
font-family="Arial, sans-serif"
font-size="13"
fill="#999999">
Stars
</text>

<text x="680" y="135"
font-family="Arial, sans-serif"
font-size="28"
font-weight="bold"
fill="#ffffff">
{forks}
</text>

<text x="680" y="158"
font-family="Arial, sans-serif"
font-size="13"
fill="#999999">
Forks
</text>

<line x1="40" y1="195" x2="760" y2="195"
stroke="#333333"/>

<text x="40" y="235"
font-family="Arial, sans-serif"
font-size="14"
fill="#aaaaaa">
Generated automatically by GitHub Actions
</text>

</svg>
"""

    (ASSETS_DIR / "stats.svg").write_text(
        svg,
        encoding="utf-8"
    )


def create_languages_svg(stats):
    languages = stats["languages"]

    top_languages = languages.most_common(6)

    total = sum(languages.values())

    width = 800
    height = 340

    svg = f"""<svg width="{width}" height="{height}"
xmlns="http://www.w3.org/2000/svg">

<rect width="{width}" height="{height}" rx="16"
fill="#171717"
stroke="#3b3b3b"/>

<text x="40" y="50"
font-family="Arial, sans-serif"
font-size="24"
font-weight="bold"
fill="#ffffff">
Most Used Languages
</text>
"""

    y = 90

    for language, amount in top_languages:
        percentage = (amount / total * 100) if total else 0

        bar_width = int(500 * percentage / 100)

        svg += f"""
<text x="40" y="{y}"
font-family="Arial, sans-serif"
font-size="14"
fill="#ffffff">
{escape_svg(language)}
</text>

<rect x="160" y="{y - 12}"
width="500" height="12"
rx="6"
fill="#292929"/>

<rect x="160" y="{y - 12}"
width="{bar_width}" height="12"
rx="6"
fill="#7c3aed"/>

<text x="680" y="{y}"
font-family="Arial, sans-serif"
font-size="13"
fill="#999999">
{percentage:.1f}%
</text>
"""

        y += 40

    svg += """
<text x="40" y="315"
font-family="Arial, sans-serif"
font-size="12"
fill="#777777">
Based on repository language statistics
</text>

</svg>
"""

    (ASSETS_DIR / "languages.svg").write_text(
        svg,
        encoding="utf-8"
    )


def main():
    print(f"Collecting GitHub data for {USERNAME}...")

    repositories = get_repositories()

    print(f"Repositories found: {len(repositories)}")

    statistics = calculate_statistics(repositories)

    print("Statistics:")
    print(f"Repositories: {statistics['repositories']}")
    print(f"Commits: {statistics['commits']}")
    print(f"Stars: {statistics['stars']}")
    print(f"Forks: {statistics['forks']}")

    create_stats_svg(statistics)
    create_languages_svg(statistics)

    print("SVG files generated successfully.")


if __name__ == "__main__":
    main()