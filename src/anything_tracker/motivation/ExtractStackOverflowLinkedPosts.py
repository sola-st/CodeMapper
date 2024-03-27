from os.path import join
import requests
from bs4 import BeautifulSoup


def get_question_text(question_link):
    question_text_tmp = question_link.split("/")[-1].split("?")[0]
    question_text = question_text_tmp.replace("-", " ")
    if question_text.isdigit():
        question_text = ""
    return question_text


class ExtractStackOverflowLinkedPosts():
    def __init__(self, question_url, output_dir):
        self.question_url = question_url
        self.question_id = question_url.split("/")[4]
        self.linked_posts = []
        self.output = join(output_dir, f"{self.question_id}_linked_posts.csv")
        
    def write_to_file(self):
        to_write = "\n".join(self.linked_posts)
        with open(self.output, "w") as f:
            f.writelines(to_write + "\n")

    def get_linked_posts(self):
        try:
            response = requests.get(self.question_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            linked_posts_div = soup.find('div', class_='linked')

            if linked_posts_div:
                # append the base question first
                base_question_text = get_question_text(self.question_url)
                self.linked_posts.append(f'"Base question", {base_question_text}, {self.question_url}')

                prefix = "https://stackoverflow.com"
                a_tags = linked_posts_div.find_all('a')
                # iterate to append the linked questions
                for a_tag in a_tags:
                    href = a_tag.get('href')
                    if href.startswith("/questions/"):
                        question_text = get_question_text(href)
                        self.linked_posts.append(f", {question_text}, {prefix}{href}")

        except requests.exceptions.RequestException as e:
            print("Error fetching data:", e)

    def run(self):
        self.get_linked_posts()
        if self.linked_posts != []:
            self.write_to_file()
        else:
            print("No linked posts.")


if __name__ == "__main__":
    question_url = "replace with the link you are interested in"
    output_dir = join("data", "results", "motivations")
    ExtractStackOverflowLinkedPosts(question_url, output_dir).run()
    print("Linked Posts Extraction Done.")