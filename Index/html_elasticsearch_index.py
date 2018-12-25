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

    title = Text(analyzer="ik_max_word")
    url = Text()
    host = Text()
    text = Text(analyzer="ik_max_word")

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
            soup = BeautifulSoup(html_content, "html.parser")
            title = soup.title.text if soup.title else "无标题"
            host = urlparse(url).netloc
            doc = HtmlDoc(title=title, text=text, url=url, host=host)
            doc.save()
            indexed_num += 1
            print("\r{}".format(indexed_num), end="")
