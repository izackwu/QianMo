from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re


class BaseParser(object):

    def __init__(self):
        self.standard_url_pattern = re.compile(r"^(https?:)?//[^\s]*$")  # https:// or http:// or //
        self.relative_path_pattern = re.compile(r"^\.{0,2}/?[^\s]*$")  # / or ./ or ../
        self.common_img_formats = ("bmp", "jpg", "jpeg", "png", "gif")

    def parse_url(self, html_content, current_url=None):
        soup = BeautifulSoup(html_content, features="html.parser")  # specify features to avoid potential warnings
        url_set = set()
        for a in soup.findAll("a"):
            maybe_url = a.get("href", "")
            final_url = self.handle_url(maybe_url, current_url)
            if final_url:
                url_set.add(final_url)
        return url_set

    def parse_img(self, html_content, current_url=None):
        soup = BeautifulSoup(html_content, features="html.parser")
        img_set = set()
        for img in soup.findAll("img"):
            maybe_img = img.get("src", "")
            final_img = self.handle_img(maybe_img, current_url)
            if final_img:
                img_set.add(final_img)
        return img_set

    def handle_url(self, maybe_url, current_url=None):
        maybe_url = maybe_url.strip()
        if self.standard_url_pattern.match(maybe_url) or self.relative_path_pattern.match(maybe_url):
            if current_url:
                return urljoin(current_url, maybe_url)
            else:
                return maybe_url  # without the current url, I can't turn a relative path into a standard url
        else:
            return None

    def handle_img(self, maybe_img, current_url=None):
        final_url = self.handle_url(maybe_img, current_url)
        if not final_url:  # make sure that it's a valid url
            return None
        last = final_url.split(".")[-1]
        if last in self.common_img_formats:
            return final_url
        else:
            return None


class QSBKParser(BaseParser):

    def __init__(self):
        super(QSBKParser, self).__init__()

    def parse_page(self, html_content, current_url=None):
        soup = BeautifulSoup(html_content, features="html.parser")
        docs = dict()
        for single_post in soup.findAll("div", {"id": re.compile(r"qiushi_tag_\d+")}):
            qiushi_tag = single_post["id"].split("_")[-1]
            content = single_post.find("div", {"class": "content"}).span.text.strip()
            maybe_img = single_post.find("div", {"class": "thumb"}).a.img["src"]
            img_url = self.handle_img(maybe_img, current_url)
            docs[qiushi_tag] = {
                "content": content,
                "img_url": img_url,
            }
        try:
            maybe_next_page = soup.find("span", {"class": "next"}).parent["href"]
            next_page = self.handle_url(maybe_next_page, current_url)
        except Exception as e:
            print("Failed to get the next page.")
            print(e)
            next_page = None
        return docs, next_page


def unit_test():
    print("Unit Test Begins.")
    with open("example.html", encoding="utf8", mode="r") as file:
        html_data = file.read()
    current_url = "https://keithnull.top"
    print("Try to parse the html content.")
    my_parser = BaseParser()
    url_set = my_parser.parse_url(html_data, current_url)
    img_set = my_parser.parse_img(html_data, current_url)
    print("Urls:")
    for no, url in enumerate(url_set):
        print("#{no}:{url}".format(no=no, url=url))
    print("Imgs:")
    for no, img in enumerate(img_set):
        print("#{no}:{img}".format(no=no, img=img))
    with open("QSBKexample.html", encoding="utf8", mode="r") as file:
        html_data = file.read()
    current_url = "https://www.qiushibaike.com/pic/"
    print("Try to parse Qiushibaike's page.")
    my_parser = QSBKParser()
    docs, next_page = my_parser.parse_page(html_data, current_url)
    for tag, post in docs.items():
        print("#{tag}:{text}\n{img}\n".format(tag=tag, text=post["content"], img=post["img_url"]))
    print("Next Page:", next_page)


if __name__ == '__main__':
    unit_test()
