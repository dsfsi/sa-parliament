#!/usr/bin/env python3

import argparse
import random
import re
import requests
import time

import numpy as np
import pandas as pd

from pathlib import Path

from bs4 import BeautifulSoup
from tqdm import tqdm

from pandas_utility import PandasUtilities as utils

# An index of the members, with a thumbnail linking to their individual profile pages.
# NOTE: This is a public link which contains details of our esteemed members of parliament
# from the website of the Parliamentary Monitoring Group.
URL = "https://pmg.org.za/members/"


class ParliamentMembers:
    def __init__(self, url, min_time_range: int = 10, max_time_range: int = 20):
        self.url = url
        self._columns = ["Name", "Political Party", "Phone", "Email", "Twitter Handle"]
        self._min_range = min_time_range
        self._max_range = max_time_range

    @staticmethod
    def read_html(url: str) -> BeautifulSoup:
        """
        Retrieve URL via GET request.
        Check that request was successful and that the result is an HTML document.
        """
        try:
            response = requests.get(url, stream=True)
            status_code = response.status_code
            content_type = response.headers["Content-Type"].lower()
        except requests.RequestException as e:
            raise RuntimeError(f"Error during requests to {url} : {str(e)}")
        else:
            if (
                status_code == 200
                and content_type is not None
                and content_type.find("html") > -1
            ):
                return BeautifulSoup(response.content, "html.parser")

    def get_person(self, url: str) -> dict:
        """
        Retrieve a persons information from the provident Parliament direct URL link.
        """
        person = self.read_html(url)

        return {
            # TODO: There's a better way of doing this.
            self._columns[0]: person.select_one("h1").text.strip(),
            self._columns[1]: person.select_one(".party-membership--party").text,
            self._columns[2]: "; ".join(
                [a.text for a in person.select('[href^="tel:"]')]
            ),
            self._columns[3]: "; ".join(
                [a.text for a in person.select(".email-address a")]
            ),
            self._columns[4]: "; ".join(
                [a.text.strip() for a in person.select(".contact-actions__twitter")]
            ),
        }

    def get_parliament_members_urls(self) -> list:
        """
        Retrieve a list of members direct URL which link to their Parliament's profile.
        """
        directory = self.read_html(self.url)
        return [
            a.attrs["href"]
            for a in directory.select(".single-mp a")
            if a.attrs["href"].startswith("https")
        ]

    def get_person_delayed(self, url: str,) -> dict:
        """
        Pretend to be real Human by delaying the retrieval of a persons information.
        """
        time.sleep(random.randint(self._min_range, self._max_range))
        return self.get_person(url)

    def get_all_members_info(self) -> None:
        """
        Retrieve all members direct URL's and create a Pandas DataFrame containing the
        persons of interests information.
        """
        members_url = self.get_parliament_members_urls()
        print(f"Found {len(members_url)} number of Parliamentary members.")
        members_data = []

        for member_url in tqdm(members_url):
            try:
                members_data.append(self.get_person_delayed(member_url))
            except Exception:
                print(f"Failed to get members information: {member_url}")

        self.dataframe = pd.DataFrame(members_data, columns=self._columns)
        self.dataframe.replace("", np.nan, inplace=True, regex=True)


def parse_args():
    # TODO: Add arguments.
    parser = argparse.ArgumentParser()


def main():
    args = parse_args()

    parliament_data = ParliamentMembers(URL)
    parliament_data.get_all_members_info()
    csv_path = f"member_data_{time.strftime('%Y_%m_%d')}.csv"
    print(f"Writing data to csv file: {csv_path.as_posix()!r}")
    parliament_data.dataframe.to_csv(csv_path)


if __name__ == "__main__":
    main()
