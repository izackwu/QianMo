import requests
import os
from my_utils.parsers import BaseParser
from my_utils.bloom_filter import BloomFilter
from urllib.parse import urlparse
from threading import Thread, Lock
import hashlib

data_dir = "../data"
html_index = os.path.join(data_dir, "new_index.txt")
image_dir = os.path.join(data_dir, "image_data")
image_index = os.path.join(data_dir, "image_index.txt")

target_domains = [
    "www.seiee.sjtu.edu.cn", "www.sjtu.edu.cn", "news.sjtu.edu.cn"]


def get_images(url, html_file, image_parser):
    html_file = os.path.join(data_dir, html_file)
    with open(html_file, mode="r", encoding="utf8") as html:
        content = html.read()
    # print(content)
    return image_parser.parse_img(content, url)


def hash_filename(s):
    md5 = hashlib.md5()
    md5.update(s.encode("utf8"))
    return md5.hexdigest()+".jpg"


def save_image(image_url):
    try:
        # print(image_url)
        content = requests.get(image_url).content
        file_name = hash_filename(image_url)
        with open(os.path.join(image_dir, file_name), mode="wb") as file:
            file.write(content)
    except Exception as e:
        print(e)
        return None
    else:
        return file_name


if __name__ == '__main__':
    if not os.path.exists(image_dir):
        os.mkdir(image_dir)
    image_parser = BaseParser()
    bloom_filter = BloomFilter(100000)
    page_num = 0
    image_num = 0
    with open(html_index, mode="r", encoding="utf8") as h_index:
        with open(image_index, mode="a", encoding="utf8") as i_index:
            for line in h_index:
                print("\rPage Num:{:04}  Image Num:{:05}".format(page_num, image_num), end="")
                page_num += 1
                url, html_file = line.split()
                if urlparse(url).netloc not in target_domains:
                    continue
                all_images = get_images(url, html_file, image_parser)
                # print(all_images)
                for image_url in all_images:
                    if bloom_filter.check(image_url) == True:
                        continue
                    bloom_filter.add(image_url)
                    image_path = save_image(image_url)
                    if image_path:
                        image_num += 1
                        i_index.write("{image_url}\t{image_path}\t{url}\t{html_file}\n".format(
                            image_url=image_url, image_path=image_path, url=url,
                            html_file=html_file))
