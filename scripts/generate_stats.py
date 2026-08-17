import os
import requests
from collections import Counter
from xml.sax.saxutils import escape

USERNAME = "LuizSptech"
TOKEN = os.environ.get("GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

API = "https://api.github.com"


def get_repositories():
    repos = []
    page = 1

    while True:
        response = requests.get(
            f"{API}/users/{USERNAME}/repos",
            headers=HEADERS,
            params={
                "per_page": 100,
                "page": page,
                "type": "owner"
            }
        )

        response.raise_for_status()
        data = response.json()

        if not data:
            break

        repos.extend(data)
        page += 1

    return repos


def get_languages(repos):
    languages = Counter()

    for repo in repos:
        response = requests.get(
            repo["languages_url"],
            headers=HEADERS
        )

        if response.status_code == 200:
            data = response.json()

            for language, bytes_count in data.items():
                languages[language] += bytes_count

    return languages


def create_stats_svg(repos):
    total_repos = len(repos)

    stars = sum(repo["stargazers_count"] for repo in repos)

    forks = sum(repo["forks_count"] for repo in repos)

    followers_response = requests.get(
        f"{API}/users/{USERNAME}",
        headers=HEADERS
    )

    followers_response.raise_for_status()
    user = followers_response.json()

    followers = user["followers"]

    total_size = sum(repo["size"] for repo in repos)

    public_repos = user["public_repos"]

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="700" height="330" viewBox="0 0 700 330">

<style>
.title {{
    font: 700 24px Arial;
    fill: #ffffff;
}}

.label {{
    font: 600 16px Arial;
    fill: #8b949e;
}}

.value {{
    font: 700 22px Arial;
    fill: #ffffff;
}}

.card {{
    fill: #0d1117;
    stroke: #30363d;
    stroke-width: 1;
}}
</style>

<rect width="700" height="330" rx="15" class="card"/>

<text x="35" y="45" class="title">
GitHub Statistics
</text>

<text x="35" y="95" class="label">
Repositories
</text>

<text x="35" y="125" class="value">
{total_repos}
</text>

<text x="250" y="95" class="label">
Public Repositories
</text>

<text x="250" y="125" class="value">
{public_repos}
</text>

<text x="500" y="95" class="label">
Followers
</text>

<text x="500" y="125" class="value">
{followers}
</text>

<text x="35" y="180" class="label">
Stars
</text>

<text x="35" y="210" class="value">
{stars}
</text>

<text x="250" y="180" class="label">
Forks
</text>

<text x="250" y="210" class="value">
{forks}
</text>

<text x="500" y="180" class="label">
Repository Size
</text>

<text x="500" y="210" class="value">
{total_size} KB
</text>

<text x="35" y="275" class="label">
Updated automatically through GitHub Actions
</text>

</svg>
"""

    os.makedirs("assets", exist_ok=True)

    with open("assets/stats.svg", "w", encoding="utf-8") as file:
        file.write(svg)


def create_languages_svg(languages):
    total = sum(languages.values())

    if total == 0:
        return

    top_languages = languages.most_common(8)

    rows = []

    y = 75

    for language, amount in top_languages:
        percentage = amount / total * 100

        rows.append(
            f"""
            <text x="30" y="{y}" class="label">
                {escape(language)}
            </text>

            <text x="390" y="{y}" class="value">
                {percentage:.1f}%
            </text>
            """
        )

        y += 35

    height = 100 + len(top_languages) * 35

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
width="500"
height="{height}"
viewBox="0 0 500 {height}">

<style>
.label {{
    font: 600 16px Arial;
    fill: #8b949e;
}}

.value {{
    font: 700 16px Arial;
    fill: #ffffff;
}}

.card {{
    fill: #0d1117;
    stroke: #30363d;
    stroke-width: 1;
}}

.title {{
    font: 700 22px Arial;
    fill: #ffffff;
}}
</style>

<rect width="500" height="{height}" rx="15" class="card"/>

<text x="30" y="38" class="title">
Most Used Languages
</text>

{''.join(rows)}

</svg>
"""

    with open("assets/languages.svg", "w", encoding="utf-8") as file:
        file.write(svg)


def main():
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN não encontrado.")

    repos = get_repositories()

    languages = get_languages(repos)

    create_stats_svg(repos)

    create_languages_svg(languages)

    print("SVGs gerados com sucesso.")


if __name__ == "__main__":
    main()