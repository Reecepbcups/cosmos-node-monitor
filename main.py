# Goal: iterate a list of endpoints, and validate their block heights have increased more since the last run

import json
import multiprocessing
import os
from typing import List, Tuple

from helpers import Endpoint
from httpx import get
from notifications import discord_notification

curr_dir = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(curr_dir, "config.json"), "r") as f:
    config = json.load(f)


# Load configuration
webhook = config["discord_webhook"]
error_picture = config["error_picture"]

endpoints: dict[str, Endpoint] = {}

cfg_chains: dict = config["chains"]
for endpoint in cfg_chains:
    o: dict = cfg_chains[endpoint]
    e = Endpoint(
        name=endpoint,
        nodes=o["nodes"],
        references=o["references"],
        allowed_block_drift=o.get("allowed_block_drift", 5),
    )
    endpoints[e.name] = e


def main():
    task = []
    for name, obj in endpoints.items():
        our_urls = obj.nodes
        references = obj.references
        drift = obj.allowed_block_drift
        task.append((our_urls, references, name, drift))

    with multiprocessing.Pool() as p:
        p.starmap(check_nodes, task)


def notify(
    url: str,
    values: dict[str, Tuple[str, bool]],
    title: str = f" ",
    desc: str = f"",
):
    if len(title) == 0:
        title = f"Node is down: {url}"

    if len(desc) == 0:
        desc = f"Node is down"

    discord_notification(
        url=webhook,
        title=title,
        description=desc,
        color="ff0000",
        values=values,
        imageLink=error_picture,
        footerText="",
    )


def get_height(name: str, url: str) -> int | None:
    try:
        response = get(f"{url}/abci_info", timeout=15)
    except Exception as e:
        print(f"{endpoint} is down for get exception")
        notify(
            url=url,
            values={
                "status": [f"{e=}", True],
                "name": [f"{name}", True],
                "url": [f"{url}", True],
            },
        )
        return None

    # non success status code :(
    if response.status_code != 200:
        print(f"{endpoint} is down. {response.status_code=}")
        notify(
            url=url,
            title=f"Bad Status Code for {name}",
            values={
                "status": [f"{response.status_code=}", True],
                "url": [f"{url}", True],
            },
        )
        return None

    j = response.json()
    last_height = (
        dict(j).get("result", {}).get("response", {}).get("last_block_height", 0)
    )

    # convert last_height to int
    try:
        last_height = int(last_height)
    except Exception as e:
        print(f"{endpoint} is down for int exception")
        notify(
            url=url,
            title=f"Bad JSON Resp parsing for {name}",
            desc="ERROR!!!",
            values={
                "url": [f"{url}", True],
                "status": [f"{e}", True],
                "json": [f"{j}", True],
            },
        )
        return None

    return last_height


def get_reference_height(name: str, reference_urls: List[str]) -> int:
    reference_height = 0

    for url in reference_urls:
        height = get_height(name, url)

        if height is None:
            print(f"reference: {url} is down, next")
            continue

        if height > reference_height:
            reference_height = height

    return reference_height


def get_our_heights(name: str, nodes: List[str]) -> dict[str, int]:
    heights: dict[str, int] = {}

    for url in nodes:
        height = get_height(name, url)

        if height is None:
            print(f"{url} is down, next")
            continue

        heights[url] = height

    return heights


def check_nodes(
    our_urls: List[str], references: List[str], name: str, block_drift: int
):
    # url -> height
    reference_height = get_reference_height(name, references)
    heights = get_our_heights(name, our_urls)

    print(f"{name} {heights=}, {reference_height=}")

    # if reference_height is 0, we compare within our own nodes for highest height
    if reference_height == 0:
        reference_height = max(heights.values())
        if reference_height == 0:
            print(f"{name} reference_height is 0, something is wrong")
            notify(
                url=name,
                title=f"{name} reference_height is 0",
                desc=f"ERROR!!!",
                values={
                    "ref: ": [f"no reference >0...", True],
                },
            )
            exit(1)

    # iterate our heights and compare to reference
    for url, height in heights.items():
        if reference_height - height >= block_drift:
            notify(
                url=url,
                title=f"{name} node is out of sync: {url}",
                desc=f"Blocks: {reference_height-height:,}",
                values={
                    "last_height": [f"{height:,}", True],
                    "reference_height": [f"{reference_height:,}", True],
                },
            )


if __name__ == "__main__":
    main()
