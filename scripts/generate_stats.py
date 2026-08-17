import os
import requests
from collections import Counter
from xml.sax.saxutils import escape

USERNAME = "LuizSptech"

TOKEN = os.environ.get("GITHUB_TOKEN")

API = "https://api.github.com"
GRAPHQL_API = "https://api.github.com/graphql"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}


# ============================================================
# GITHUB REST API
# ============================================================

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
            },
            timeout=30
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

        try:

            response = requests.get(
                repo["languages_url"],
                headers=HEADERS,
                timeout=30
            )

            if response.status_code != 200:
                continue

            data = response.json()

            for language, bytes_count in data.items():
                languages[language] += bytes_count

        except requests.RequestException as error:

            print(
                f"Erro ao obter linguagens de "
                f"{repo['name']}: {error}"
            )

    return languages


def get_user():
    response = requests.get(
        f"{API}/users/{USERNAME}",
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# GITHUB GRAPHQL API
# ============================================================

def get_contribution_statistics():

    query = """
    query($username: String!) {

        user(login: $username) {

            contributionsCollection {

                totalCommitContributions

                totalContributions

            }
        }
    }
    """

    payload = {
        "query": query,
        "variables": {
            "username": USERNAME
        }
    }

    response = requests.post(
        GRAPHQL_API,
        headers=HEADERS,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:

        raise RuntimeError(
            f"Erro na API GraphQL: "
            f"{data['errors']}"
        )

    contributions = data["data"]["user"][
        "contributionsCollection"
    ]

    return {
        "commits": contributions[
            "totalCommitContributions"
        ],

        "contributions": contributions[
            "totalContributions"
        ]
    }


# ============================================================
# STATS SVG
# ============================================================

def create_stats_svg(
    repos,
    contribution_stats,
    user
):

    total_repos = len(repos)

    commits = contribution_stats["commits"]

    contributions = contribution_stats[
        "contributions"
    ]

    stars = sum(
        repo["stargazers_count"]
        for repo in repos
    )

    forks = sum(
        repo["forks_count"]
        for repo in repos
    )

    svg = f"""
<svg
    xmlns="http://www.w3.org/2000/svg"
    width="800"
    height="330"
    viewBox="0 0 800 330"
>

<style>

.title {{
    font: 700 24px Arial;
    fill: #ffffff;
}}

.subtitle {{
    font: 400 13px Arial;
    fill: #8b949e;
}}

.label {{
    font: 600 14px Arial;
    fill: #8b949e;
}}

.value {{
    font: 700 25px Arial;
    fill: #ffffff;
}}

.card {{
    fill: #0d1117;
    stroke: #30363d;
    stroke-width: 1;
}}

.divider {{
    stroke: #30363d;
    stroke-width: 1;
}}

</style>


<rect
    width="800"
    height="330"
    rx="15"
    class="card"
/>


<!-- TITLE -->

<text
    x="35"
    y="45"
    class="title"
>
GitHub Activity
</text>


<text
    x="35"
    y="68"
    class="subtitle"
>
LuizSptech
</text>


<!-- FIRST ROW -->

<text
    x="55"
    y="115"
    class="value"
>
{total_repos}
</text>

<text
    x="55"
    y="137"
    class="label"
>
Repositories
</text>


<text
    x="215"
    y="115"
    class="value"
>
{commits}
</text>

<text
    x="215"
    y="137"
    class="label"
>
Commits
</text>


<text
    x="375"
    y="115"
    class="value"
>
{stars}
</text>

<text
    x="375"
    y="137"
    class="label"
>
Stars
</text>


<text
    x="535"
    y="115"
    class="value"
>
{forks}
</text>

<text
    x="535"
    y="137"
    class="label"
>
Forks
</text>


<text
    x="655"
    y="115"
    class="value"
>
{contributions}
</text>

<text
    x="655"
    y="137"
    class="label"
>
Contributions
</text>


<!-- DIVIDER -->

<line
    x1="35"
    y1="180"
    x2="765"
    y2="180"
    class="divider"
/>


<!-- SECOND ROW -->

<text
    x="35"
    y="220"
    class="label"
>
Public Repositories
</text>

<text
    x="35"
    y="250"
    class="value"
>
{user["public_repos"]}
</text>


<text
    x="250"
    y="220"
    class="label"
>
Followers
</text>

<text
    x="250"
    y="250"
    class="value"
>
{user["followers"]}
</text>


<text
    x="465"
    y="220"
    class="label"
>
Following
</text>

<text
    x="465"
    y="250"
    class="value"
>
{user["following"]}
</text>


<text
    x="35"
    y="295"
    class="subtitle"
>
Updated automatically through GitHub Actions
</text>


</svg>
"""

    os.makedirs(
        "assets",
        exist_ok=True
    )

    with open(
        "assets/stats.svg",
        "w",
        encoding="utf-8"
    ) as file:

        file.write(svg)


# ============================================================
# LANGUAGES SVG
# ============================================================

def create_languages_svg(languages):

    total = sum(
        languages.values()
    )

    if total == 0:

        print(
            "Nenhuma linguagem encontrada."
        )

        return

    top_languages = languages.most_common(6)

    rows = []

    y = 85

    for language, amount in top_languages:

        percentage = (
            amount / total * 100
        )

        bar_width = int(
            320 * percentage / 100
        )

        rows.append(
            f"""
<text
    x="30"
    y="{y}"
    class="label"
>
{escape(language)}
</text>

<rect
    x="120"
    y="{y - 13}"
    width="320"
    height="10"
    rx="5"
    fill="#21262d"
/>

<rect
    x="120"
    y="{y - 13}"
    width="{bar_width}"
    height="10"
    rx="5"
    fill="#8b5cf6"
/>

<text
    x="455"
    y="{y}"
    class="percentage"
>
{percentage:.1f}%
</text>
"""
        )

        y += 45

    height = 100 + (
        len(top_languages) * 45
    )

    svg = f"""
<svg
    xmlns="http://www.w3.org/2000/svg"
    width="500"
    height="{height}"
    viewBox="0 0 500 {height}"
>

<style>

.label {{
    font: 600 14px Arial;
    fill: #8b949e;
}}

.percentage {{
    font: 600 13px Arial;
    fill: #8b949e;
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


<rect
    width="500"
    height="{height}"
    rx="15"
    class="card"
/>


<text
    x="30"
    y="40"
    class="title"
>
Most Used Languages
</text>


{''.join(rows)}


</svg>
"""

    with open(
        "assets/languages.svg",
        "w",
        encoding="utf-8"
    ) as file:

        file.write(svg)


# ============================================================
# MAIN
# ============================================================

def main():

    if not TOKEN:

        raise RuntimeError(
            "GITHUB_TOKEN não encontrado."
        )


    print(
        f"Buscando dados do GitHub para "
        f"{USERNAME}..."
    )


    # Repositórios

    repos = get_repositories()

    print(
        f"Repositórios encontrados: "
        f"{len(repos)}"
    )


    # Linguagens

    languages = get_languages(
        repos
    )


    # Usuário

    user = get_user()


    # Commits + contribuições

    contribution_stats = (
        get_contribution_statistics()
    )


    print(
        f"Commits: "
        f"{contribution_stats['commits']}"
    )

    print(
        f"Contribuições: "
        f"{contribution_stats['contributions']}"
    )


    # SVGs

    create_stats_svg(
        repos,
        contribution_stats,
        user
    )

    create_languages_svg(
        languages
    )


    print(
        "SVGs gerados com sucesso."
    )


if __name__ == "__main__":
    main()