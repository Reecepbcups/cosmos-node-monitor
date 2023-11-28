# Goal: iterate a list of endpoints, and validate their block heights have increased more since the last run

import json
import os
from typing import List

from httpx import get

from notifications import discord_notification

curr_dir = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(curr_dir, "config.json"), "r") as f:
    config = json.load(f)

webhook = config["discord_webhook"]
endpoints: dict[str, str] = dict(config["chains"])
error_picture = config["error_picture"]


def load_last() -> dict:
    if os.path.exists(f"{curr_dir}/saves.json"):
        with open(f"{curr_dir}/saves.json", "r") as f:
            last_run = json.load(f)
    else:
        print("No saves.json found!")
        last_run = {}

    return last_run


def main():
    # set all endpoints to 0 height
    recentCheck = {e: 0 for e in endpoints.keys()}

    # load most recent run
    last_run = load_last()

    # iterate our endpoints and value the blocks are increasing
    for endpoint in endpoints:
        name = endpoint
        url = endpoints[endpoint]

        try:
            response = get(f"{url}/abci_info", timeout=10)
        except Exception as e:
            print(f"{endpoint} is down for get exception")
            discord_notification(
                url=webhook,
                title=f"Node Down - {name}",
                description=f"Node is down",
                color="ff0000",
                values={
                    "status": [f"{e=}", True],
                },
                imageLink=error_picture,
                footerText="",
            )
            continue

        # non success status code :(
        if response.status_code != 200:
            print(f"{endpoint} is down. {response.status_code=}")
            discord_notification(
                url=webhook,
                title=f"Node Down - {name}",
                description=f"Node is down",
                color="ff0000",
                values={
                    "status": [f"{response.status_code=}", True],
                },
                imageLink=error_picture,
                footerText="",
            )
            continue

        # success, get block height
        j = response.json()
        last_height = (
            dict(j).get("result", {}).get("response", {}).get("last_block_height", 0)
        )
        recentCheck[endpoint] = last_height

        # !: cache may fall behind and the caught up RPC value is used instead. Wonder how this will work
        # if endpoint is in last_run, check if last_height is greater than last_run[endpoint]
        if endpoint in last_run:
            if last_height > last_run[endpoint]:
                print(
                    f"{endpoint} has increased by {int(last_height) - int(last_run[endpoint])} blocks since last run"
                )
            else:
                print(f"{endpoint} has not increased since last run")
                discord_notification(
                    url=webhook,
                    title=f"Node Down - {name}",
                    description=f"Node is down",
                    color="ff0000",
                    values={
                        "last_height": [f"{last_height}", True],
                    },
                    imageLink=error_picture,
                    footerText="",
                )

    # dump recentCheck to curr_dir / saves.json
    with open(f"{curr_dir}/saves.json", "w") as f:
        print(f"Dumping recentCheck to saves.json. {recentCheck=}")
        json.dump(recentCheck, f, indent=4)


if __name__ == "__main__":
    main()
