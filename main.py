# create a confluence page with a html file

import argparse
import os
import re
import requests
import sys
from bs4 import BeautifulSoup
from pathlib import Path, PurePath
from urllib.parse import unquote


# get the confluence url
url = "YOUR_CONFLUENCE_URL"

# authenticate with my public access token
token = os.environ["CONFLUENCE_TOKEN"]
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}


def create_page(parent_id: int, space_key: str, title: str) -> int:
    """Create a new confluence page with the given parent id and return the new page id"""

    # create the json payload
    payload = {
        "type": "page",
        "ancestors": [{"id": parent_id}],
        "title": title,
        "space": {"key": space_key},
        "body": {"storage": {"value": "", "representation": "storage"}},
    }

    # post the page
    r = requests.post(
        f"{url}/rest/api/content",
        json=payload,
        headers=headers,
    )

    if r.status_code != 200:
        if r.status_code == 400:
            # search id of the page with the same title
            r = requests.get(
                f"{url}/rest/api/content",
                headers=headers,
                params={"title": title, "spaceKey": space_key},
            )
            return r.json()["results"][0]["id"]
        else:
            print(r.json())
            sys.exit(-1)

    # return the page id
    return r.json()["id"]


def upload_page(file_path: str, page_id: int):
    print(f"Uploading {file_path} to {page_id}")

    params = {"expand": "version"}
    r = requests.get(
        f"{url}/rest/api/content/{page_id}",
        headers=headers,
        params=params,
    )
    if r.status_code != 200:
        print(file_path, page_id)
        print(r.json())
        return

    # create the json payload
    old_version = r.json()["version"]["number"]
    new_version = old_version + 1

    # get the html file
    html_file = open(file_path, "r")
    html = html_file.read()
    html = re.sub(r"<!DOCTYPE.*?>", "", html)

    # parse the html file
    soup = BeautifulSoup(html, "html.parser")
    if soup.h1:
        soup.h1.decompose()

    # upload attachments
    for a in soup.find_all("a", href=True):
        if a["href"].startswith("blobs"):
            upload_file(a, file_path, page_id)

    body = soup.prettify()
    payload = {
        "version": {"number": new_version},
        "type": "page",
        "title": Path(file_path).stem,
        "body": {"storage": {"value": body, "representation": "storage"}},
    }

    # post the page
    r = requests.put(
        f"{url}/rest/api/content/{page_id}",
        json=payload,
        headers=headers,
    )

    # print the response
    if r.status_code != 200:
        print(r.json())


def upload_file(a: dict, file_path: str, page_id: int):
    href = a["href"]
    href = href.replace("&", "&amp;")
    try:
        with open(os.path.join(os.path.dirname(file_path), href), "rb") as f:
            unquoted = unquote(href[6:])
            unquoted = unquoted.split("&")[0]
            a["href"] = f"{url}/download/attachments/{page_id}/{unquoted}"
            print(f"Uploading {href} as {unquoted}")
            files = {"file": (unquoted, f)}
            attachment_header = {
                "Authorization": f"Bearer {token}",
                "X-Atlassian-Token": "nocheck",
            }
            r = requests.post(
                f"{url}/rest/api/content/{page_id}/child/attachment",
                headers=attachment_header,
                files=files,
            )

            if r.status_code not in [200, 400]:
                try:
                    print(r.json())
                except requests.exceptions.JSONDecodeError:
                    print(r.text)

    except FileNotFoundError:
        print(f"File not found: {href}")


def recursive_upload(input_path: str, space_key: str, parent_id: int):
    """upload all files in the given directory recursively"""
    print(f"Uploading {input_path}...")
    dirname = PurePath(input_path).name
    parent_id = create_page(parent_id, space_key, dirname)

    for d in os.listdir(input_path):
        if os.path.isdir(os.path.join(input_path, d)):
            if d != "blobs":
                recursive_upload(os.path.join(input_path, d), space_key, parent_id)
        else:
            if d.endswith(".html"):
                page_id = create_page(parent_id, space_key, d[:-5])
                path = os.path.join(input_path, d)
                upload_page(path, page_id)


if __name__ == "__main__":
    # get the confluence page id
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--page-id",
        help="confluence page id of the uploading root page",
        type=int,
        required=True,
    )
    parser.add_argument("--input-path", help="path to upload", required=True)
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="if path is a directory, upload all files recursively",
    )
    parser.add_argument("--space-key", help="space key to upload")
    args = parser.parse_args()

    # traverse the directory and upload all files
    if args.recursive:
        assert os.path.isdir(args.input_path), "input_path must be a directory"
        recursive_upload(args.input_path, args.space_key, args.page_id)
    else:
        upload(args.input_path, args.page_id)
