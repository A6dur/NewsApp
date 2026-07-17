import requests
import webbrowser

API_KEY = "7fb741c01f0b47c5b4fab3fca1456545"
BASE_URL = "https://newsapi.org/v2/everything"


def get_news(query):
    params = {
        "q": query,
        "sortBy": "popularity",
        "language": "en",
        "apiKey": API_KEY
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data["status"] != "ok":
            print(f"\n❌ Error: {data.get('message', 'Unknown Error')}")
            return []

        return data["articles"]

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Network Error: {e}")
        return []


def display_articles(articles, limit):
    print(f"\nFound {len(articles)} articles.\n")

    limit = min(limit, len(articles))

    for i in range(limit):

        article = articles[i]

        title = article.get("title") or "No Title"
        author = article.get("author") or "Unknown"
        description = article.get("description") or "No description available."
        source = article.get("source", {}).get("name", "Unknown")
        published = article.get("publishedAt") or "Unknown"
        url = article.get("url") or "No URL"

        print("=" * 90)
        print(f"Article {i + 1}")
        print("=" * 90)
        print(f"📰 Title       : {title}")
        print(f"✍ Author      : {author}")
        print(f"🏢 Source      : {source}")
        print(f"📅 Published   : {published}")
        print(f"\n📝 Description :")
        print(description)
        print(f"\n🔗 Read More   : {url}")
        print()


def open_article(articles, limit):
    while True:

        choice = input(
            f"\nEnter article number to open (1-{limit}) or 0 to Exit: "
        )

        if not choice.isdigit():
            print("Please enter a valid number.")
            continue

        choice = int(choice)

        if choice == 0:
            print("\nGoodbye!")
            break

        if 1 <= choice <= limit:
            print("\nOpening article in your browser...")
            webbrowser.open(articles[choice - 1]["url"])
            break

        print("Invalid article number.")


def main():

    print("=" * 90)
    print("📰 NEWS READER")
    print("=" * 90)

    query = input("\nEnter your topic of interest: ").strip()

    if not query:
        print("Search topic cannot be empty.")
        return

    while True:
        try:
            number = int(input("How many articles do you want to read? "))

            if number > 0:
                break

            print("Please enter a positive number.")

        except ValueError:
            print("Please enter a valid integer.")

    articles = get_news(query)

    if not articles:
        print("\nNo articles found.")
        return

    display_articles(articles, number)

    open_article(articles, min(number, len(articles)))


if __name__ == "__main__":
    main()