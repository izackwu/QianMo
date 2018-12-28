import os
import re
from elasticsearch_dsl import Document, Date, Integer, Keyword, Text
from elasticsearch_dsl.connections import connections
from urllib.parse import urlparse
from html2text import HTML2Text
from bs4 import BeautifulSoup

data_dir = "..\\data"
index_file = os.path.join(data_dir, "new_index.txt")


class HtmlDoc(Document):

    title = Text(analyzer="ik_max_word", search_analyzer="ik_smart")
    url = Keyword()
    host = Keyword()
    text = Text(analyzer="ik_max_word", search_analyzer="ik_smart")

    class Index:
        name = "qianmo"
        settings = {
            "number_of_shards": 2,
        }

    def save(self, ** kwargs):
        return super(HtmlDoc, self).save(** kwargs)


def html_to_text(html_content):
    converter = HTML2Text()
    converter.ignore_links = True
    converter.ignore_images = True
    markdown_text = converter.handle(html_content)
    pattern = "[\\\`\*\_\[\]\#\+\-\!\>|·]"
    return re.sub(pattern, ' ', markdown_text)


def get_title(html_content, url=None):
    special_cases = ["https://www.sjtu.edu.cn/", "http://www.sjtu.edu.cn/",
                     "https://www.sjtu.edu.cn", "http://www.sjtu.edu.cn"]
    soup = BeautifulSoup(html_content, "html.parser")
    title = ""
    if url and url in special_cases:
        return soup.title.text.strip()
    for tag in ["h1", "h2", "title"]:
        all_tags = soup.find_all(tag)
        if all_tags:
            for x in all_tags:
                if len(x.text.strip()) > len(title):
                    title = x.text.strip()
            break
    if not title:
        return "无标题文档"
    if len(title) <= 20 and soup.title.text.find(title) == -1:
        title = title + " " + soup.title.text.strip()
    elif soup.title.text.find(title) != -1:
        title = soup.title.text.strip()
    return title


if __name__ == '__main__':
    connections.create_connection(hosts=['localhost'])
    HtmlDoc.init()
    indexed_num = 0
    with open(index_file, mode="r", encoding="utf8") as f:
        for line in f:
            url, file_path = line.split()
            file_path = os.path.join(data_dir, file_path)
            with open(file_path, mode="r", encoding="utf8") as html_file:
                html_content = html_file.read()
            text = html_to_text(html_content)
            title = get_title(html_content, url)
            host = urlparse(url).netloc
            # print("#", url, "#", sep="")
            # input()
            # print(title)
            # print(text)
            # input()
            doc = HtmlDoc(title=title, text=text, url=url, host=host)
            doc.save()
            indexed_num += 1
            print("\r{}".format(indexed_num), end="")
