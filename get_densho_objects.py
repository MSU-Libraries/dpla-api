import requests
import os
import csv


def get_topics_to_collect():
    """Read spreadsheet to get selected topics."""
    topics = []
    with open("data/densho_topics.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["COLLECTED?"] == "x":
                topics.append(row["TOPIC"].strip())

    return topics


base_url = "https://ddr.densho.org/api/0.2/"


r = requests.get(topics_url)

topics_to_collect = get_topics_to_collect()
print(topics_to_collect)


densho_topics = []

if r.ok:
    data = r.json()

