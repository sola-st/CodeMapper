from os.path import join
import requests
from bs4 import BeautifulSoup


def get_linked_posts(question_id):
    linked_posts = []
    try:
        prefix = "https://stackoverflow.com"
        url = f"{prefix}/q/{question_id}?lq=1"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        lined_posts_div = soup.find('div', class_='linked')

        if lined_posts_div:
            a_tags = lined_posts_div.find_all('a')

            for a_tag in a_tags:
                href = a_tag.get('href')
                if href.startswith("/questions/"):
                    linked_posts.append(f"{prefix}{href}")
        else:
            print("No linked posts.")
        
    except requests.exceptions.RequestException as e:
        print("Error fetching data:", e)

    return linked_posts


if __name__ == "__main__":
    question_id = 4468361
    output = join("data", "results", "motivations", f"{question_id}_linked_posts.txt")

    linked_posts = get_linked_posts(question_id)
    to_write = "\n".join(linked_posts)
    print("Linked Posts Extraction Done.")

    with open(output, "w") as f:
        f.writelines(to_write)
