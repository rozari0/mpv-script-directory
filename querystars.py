#!/usr/bin/env python3
import json
import re
from pprint import pprint

import requests
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth

import credentials

auth = HTTPBasicAuth(credentials.user, credentials.token)
re_gitlab = re.compile(
    r"^https://gitlab\.com/([^/]+)/([^/]+)(?:/[^#&]*?)*?([^/#&]+)?/?(?:#.*|&.*)*$"
)
re_github = re.compile(
    r"^https://github\.com/([^/]+)/([^/]+)(?:/[^#&]*?)*?([^/#&]+)?/?(?:#.*|&.*)*$"
)
re_gist = re.compile(r"^https://gist.github\.com/([^/]+)/(\w+)/?(?:#.*|&.*)*$")


def getGithubStars(owner, repo, _):
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    r = requests.get(api_url, auth=auth)
    if r.status_code != 200:
        return None
    data = r.json()
    if "stargazers_count" not in data:
        print("Something went wrong: ", data)
        return None
    return data["stargazers_count"]


def updatestars(allscripts):
    for script in allscripts.values():
        stars = None
        match = re_github.fullmatch(script["url"])
        if match:
            stars = getGithubStars(*match.groups())
            if stars is None:
                print("dead url", script["url"])
                script["url"] = None
                continue
            own = match.groups()[2] is None
        elif re_gist.match(script["url"]):
            # Github API is missing a possibility to query for stars of a gist
            page = requests.get(script["url"])
            if page.status_code == 404:
                print("dead url", script["url"])
                script["url"] = None
                continue
            soup = BeautifulSoup(page.content, "html.parser")
            stars = soup.select_one(".social-count").text.strip()
            own = True
        elif match := re_gitlab.match(script["url"]):
            # TODO use gitlab api instead – if possible
            page = requests.get(script["url"])
            if page.status_code == 404:
                print("dead url", script["url"])
                script["url"] = None
                continue
            soup = BeautifulSoup(page.content, "html.parser")
            stars = soup.select_one(".star-count").text.strip()
            own = match.groups()[2] is None
        if stars:
            print("got stars:", stars, own)
            script["stars"] = stars
            script["own"] = own
    return allscripts


if __name__ == "__main__":
    with open("mpvscripts.json") as f:
        allscripts = json.load(f)

    allscripts = updatestars(allscripts)
    pprint(allscripts)

    with open("mpvscripts.json", "w") as f:
        json.dump(allscripts, f, indent=4)
