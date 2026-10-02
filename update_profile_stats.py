#!/usr/bin/env python3
"""
GitHub Profile Stats Tracker & Auto-Updater
------------------------------------------
Tracks real-time repository updates, star counts, and stats from GitHub,
and updates the profile-card.svg only upon explicit user permission.
"""

import sys
import os
import json
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

# Import generator functions and defaults from generate_card.py
try:
    from generate_card import DEFAULT_CONFIG, generate_svg, convert_image_to_ascii
except ImportError:
    # Fallback if run independently
    DEFAULT_CONFIG = {
        "user": "muhammed-shifan",
        "host": "Bit-wisely",
        "os": "Parrot OS / Arch Linux / Windows",
        "uptime": "20 years, 9 months",
        "status": "Student",
        "shell": "Curiosity + C",
        "ide": "VSCode, STM32CubeIDE",
        "lang_prog": "C, HTML, CSS, JavaScript, Python",
        "lang_learning": "Web Dev, OS / Kernel Dev, Cybersecurity",
        "lang_real": "English",
        "hobby_crypto": "Classical Ciphers, RSA, Key Exchange",
        "hobby_systems": "Low-Level C, Memory Management",
        "hobby_web": "Building things from scratch",
        "email": "muhammedshifanvm12@gmail.com",
        "linkedin": "muhammedshifanvm",
        "github": "Bit-wisely",
        "repos": "10",
        "member_since": "Dec 2024",
        "bio": "Learning curiously.",
    }


def fetch_json(url: str, token: Optional[str] = None) -> Any:
    """Fetches JSON data from GitHub API."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "GitHub-Profile-Card-Updater/1.0",
            "Accept": "application/vnd.github.v3+json",
            **({"Authorization": f"token {token}"} if token else {})
        }
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def get_live_github_stats(username: str, token: Optional[str] = None) -> Dict[str, Any]:
    """Fetches public user stats and repository activity from GitHub."""
    print(f"[*] Querying GitHub API for user: @{username}...")
    
    user_url = f"https://api.github.com/users/{username}"
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
    
    try:
        user_data = fetch_json(user_url, token)
        repos_data = fetch_json(repos_url, token)
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print("[!] Error: GitHub API rate limit exceeded. Pass a GITHUB_TOKEN environment variable.")
        elif e.code == 404:
            print(f"[!] Error: User '{username}' not found on GitHub.")
        else:
            print(f"[!] HTTP Error: {e.code} - {e.reason}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[!] Network Error: {e.reason}")
        sys.exit(1)

    # Calculate Member Since string
    created_at_str = user_data.get("created_at", "")
    member_since = "Dec 2024"
    if created_at_str:
        try:
            dt = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
            member_since = dt.strftime("%b %Y")
        except ValueError:
            pass

    # Tally stats across repos
    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos_data)
    total_forks = sum(repo.get("forks_count", 0) for repo in repos_data)
    public_repos_count = str(user_data.get("public_repos", len(repos_data)))
    bio = user_data.get("bio") or "Learning curiously."

    # Top recently updated repos
    recent_repos = []
    for r in repos_data[:5]:
        updated_at = r.get("updated_at", "")
        if updated_at:
            try:
                dt = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
                updated_fmt = dt.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                updated_fmt = updated_at
        else:
            updated_fmt = "N/A"
            
        recent_repos.append({
            "name": r.get("name"),
            "stars": r.get("stargazers_count", 0),
            "language": r.get("language") or "C/Other",
            "updated": updated_fmt,
            "description": r.get("description") or "No description"
        })

    return {
        "username": username,
        "public_repos": public_repos_count,
        "total_stars": total_stars,
        "total_forks": total_forks,
        "followers": user_data.get("followers", 0),
        "member_since": member_since,
        "bio": bio,
        "recent_repos": recent_repos,
    }


def ask_permission(prompt: str) -> bool:
    """Explicitly asks the user for confirmation."""
    while True:
        try:
            response = input(f"\n{prompt} [y/N]: ").strip().lower()
            if response in ("y", "yes"):
                return True
            if response in ("n", "no", ""):
                return False
            print("Please enter 'y' for yes or 'n' for no.")
        except (KeyboardInterrupt, EOFError):
            return False


def main():
    username = os.environ.get("GITHUB_USER", "Bit-wisely")
    token = os.environ.get("GITHUB_TOKEN", None)
    output_card = "profile-card.svg"

    print("=" * 65)
    print(f" GitHub Profile Stats Tracker & Updater")
    print(f" Target GitHub Account: @{username}")
    print("=" * 65)

    stats = get_live_github_stats(username, token=token)

    print("\n--- Live GitHub Account Summary ---")
    print(f" . Repos Count  : {stats['public_repos']}")
    print(f" . Total Stars  : {stats['total_stars']}")
    print(f" . Followers    : {stats['followers']}")
    print(f" . Member Since : {stats['member_since']}")
    print(f" . Bio          : {stats['bio']}")

    print("\n--- Recently Active / Updated Repositories ---")
    for i, r in enumerate(stats["recent_repos"], 1):
        print(f"  {i}. {r['name']:<20} | Lang: {r['language']:<12} | Updated: {r['updated']}")

    # Build updated config
    updated_config = DEFAULT_CONFIG.copy()
    updated_config["github"] = username
    updated_config["repos"] = stats["public_repos"]
    updated_config["member_since"] = stats["member_since"]
    updated_config["bio"] = stats["bio"]

    # Check for differences against default / current config
    changes = []
    if str(DEFAULT_CONFIG.get("repos")) != str(stats["public_repos"]):
        changes.append(f"Repositories: {DEFAULT_CONFIG.get('repos')} -> {stats['public_repos']}")
    if DEFAULT_CONFIG.get("member_since") != stats["member_since"]:
        changes.append(f"Member Since: {DEFAULT_CONFIG.get('member_since')} -> {stats['member_since']}")
    if DEFAULT_CONFIG.get("bio") != stats["bio"]:
        changes.append(f"Bio: {DEFAULT_CONFIG.get('bio')} -> {stats['bio']}")

    if changes:
        print("\n[!] Detected differences between local preset and live GitHub stats:")
        for c in changes:
            print(f"    - {c}")
    else:
        print("\n[*] Local preset values are already in sync with live GitHub stats.")

    # Explicit user permission request
    proceed = ask_permission(f"[?] Do you give permission to update '{output_card}' with these live stats?")
    
    if not proceed:
        print("\n[-] Operation cancelled by user. No files were modified.")
        sys.exit(0)

    # Generate updated SVG
    print(f"\n[*] Generating updated '{output_card}'...")
    svg_content = generate_svg(updated_config)
    
    with open(output_card, "w", encoding="utf-8") as f:
        f.write(svg_content)
        
    print(f"[+] Successfully updated {os.path.abspath(output_card)}")

    # Ask if user also wants to Git commit and push
    push_confirm = ask_permission("[?] Do you also want to Git commit and push the updated profile card to GitHub?")
    if push_confirm:
        try:
            print("\n[*] Running git add, commit, and push...")
            subprocess.run(["git", "add", output_card], check=True)
            commit_msg = f"Auto-update profile card stats ({datetime.now().strftime('%Y-%m-%d')})"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("[+] Successfully committed and pushed updates to origin/main!")
        except subprocess.CalledProcessError as e:
            print(f"[!] Git operation failed: {e}")
    else:
        print("[*] Skipped git push. Changes saved locally in your repository.")


if __name__ == "__main__":
    main()
