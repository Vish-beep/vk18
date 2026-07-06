import json
import requests
from bs4 import BeautifulSoup


def load_config():
    with open("config.json", "r") as file:
        return json.load(file)


def scrape(url):

    response = requests.get(url)

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    products = []

    items = soup.find_all(
        "div",
        class_="thumbnail"
    )

    for item in items:

        name = item.find(
            "a",
            class_="title"
        ).get("title")

        price = item.find(
            "h4",
            class_="price"
        ).text

        products.append(
            {
                "name": name,
                "price": price
            }
        )

    return products


def main():

    config = load_config()

    url = config["products"][0]["url"]

    data = scrape(url)


    with open(
        "cleaned/products.json",
        "w"
    ) as file:

        json.dump(
            data,
            file,
            indent=4
        )


    print("Scraping completed")
    print(data)


if __name__ == "__main__":
    main()