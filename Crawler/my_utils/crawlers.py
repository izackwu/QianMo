import requests
import random
import chardet
import os
import hashlib
from time import sleep
from queue import Queue, PriorityQueue
from threading import Thread, Lock
from urllib.parse import urlparse
from .bloom_filter import BloomFilter
from .parsers import BaseParser


class customized_str(object):

    def __init__(self, s, priority):
        self.raw_str = s
        self.priority = priority

    def __lt__(self, value):
        return self.priority > value.priority


class BaseCrawler(object):

    def __init__(self, headers=None):
        self.new_session()
        self.headers = headers

    def get_html(self, url, headers=None):
        assert self.session != None
        headers = headers or self.headers  # if headers are not specified for this single request, use the global headers
        content = self.session.get(url, headers=headers).content
        decoded_content = content.decode("utf8")  # maybe not utf-8 for some sites?
        return decoded_content

    def new_session(self):
        self.session = requests.Session()


class MultiThreadingCrawler(BaseCrawler):

    def __init__(self, thread_num=4, headers=None, session_num=10,
                 index_file=None, data_folder=None, debug=False, verbose=True, domains=None):
        super(MultiThreadingCrawler, self).__init__(headers)
        self.thread_num = thread_num
        self.index_file = index_file or "index.txt"
        self.data_folder = data_folder or "html_data"
        self.my_parser = BaseParser()
        self.sessions = list()
        for i in range(session_num):
            self.sessions.append(requests.Session())
        self.debug = debug
        self.verbose = verbose
        self.domains = domains

    def get_html(self, url, headers=None):
        assert len(self.sessions) != 0, "There's no Session available!"
        headers = headers or self.headers
        current_session = random.choice(self.sessions)
        raw_html = current_session.get(url, headers=headers).content
        decoded_html = self.__decode_html(raw_html)
        return decoded_html

    def __decode_html(self, raw_html):
        encoding_info = chardet.detect(raw_html)
        try:
            return raw_html.decode(encoding_info["encoding"] or "utf8", errors="replace")
        except Exception as e:
            if self.debug:
                print("Failed to decode:\n", e)
            try:
                return raw_html.decode("utf8", errors="replace")
            except Exception as e:
                if self.debug:
                    print(e)
                return raw_html.decode(encoding_info["encoding"] or "utf8",
                                       errors="ignore")

    def __get_links(self, html_content, current_url):
        return self.my_parser.parse_url(html_content, current_url)

    def __wirte_data(self, url, content):
        # filename = os.path.join(self.data_folder, self.__valid_filename(url))
        # to prevent extremely long filenames, just hash the url
        filename = os.path.join(self.data_folder, self.__hash_filename(url))
        with open(self.index_file, mode="a", encoding="utf8") as index:
            index.write("{url}\t{filename}\n".format(url=url, filename=filename))
        if not os.path.exists(self.data_folder):
            os.mkdir(self.data_folder)
        with open(filename, mode="w", encoding="utf8") as file:
            file.write(content)

    def __valid_filename(self, s):
        import string
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        s = ''.join(c for c in s if c in valid_chars)
        s += ".html"
        return s

    def __hash_filename(self, s):
        md5 = hashlib.md5()
        md5.update(s.encode("utf8"))
        return md5.hexdigest()+".html"

    def __check_domain(self, url):
        if not self.domains:
            return True
        current_domain = urlparse(url).netloc
        return any(current_domain.find(x) != -1 for x in self.domains)

    def crawl_from(self, seeds, max_page, thread_num=None, sleeping=None):

        def crawl_single_page(thread_id=0):
            print("Thread {0} begins to work.".format(thread_id))
            while count[0] < max_page:
                url = url_queue.get(timeout=10)
                priority = url.priority
                url = url.raw_str
                if not crawled.check(url) and self.__check_domain(url):
                    if self.verbose:
                        print("#{0:<4} {1} {2}".format(count[0]+1, priority, url))
                    else:
                        print("\rCrawling: {0}/{1}".format(count[0], max_page), end="")
                    try:
                        content = self.get_html(url)
                        outlinks = self.__get_links(content, url)
                        self.__wirte_data(url, content)
                    except Exception as e:
                        if self.debug:
                            print(e)
                            print(url)
                        continue
                    with lock:
                        domain_to_priority[urlparse(url).netloc] -= 10
                        for k in domain_to_priority.keys():
                            domain_to_priority[k] = min(100, domain_to_priority[k] + 1)
                        if count[0] >= max_page:
                            if self.verbose:
                                print("Drop!")
                            break
                        graph[url] = outlinks
                        for l in outlinks:
                            url_queue.put(customized_str(l, domain_to_priority.setdefault(urlparse(l).netloc, 100)))
                        crawled.add(url)
                        count[0] += 1
                    sleep(sleeping)
                url_queue.task_done()
            print("Thread {0} has finished.".format(thread_id))
        url_queue = PriorityQueue()
        domain_to_priority = dict()
        lock = Lock()
        crawled = BloomFilter(max_page)
        graph = {}
        count = [0, ]
        for seed in seeds:
            domain_to_priority[urlparse(seed).netloc] = 1
            url_queue.put(customized_str(seed, 100))
        threads = []
        sleeping = sleeping or 5
        print("Thread(s):", thread_num or self.thread_num)
        print("Max Pages:", max_page)
        print("Interval:", sleeping)
        for i in range(thread_num or self.thread_num):
            t = Thread(target=crawl_single_page, kwargs={"thread_id": i})
            threads.append(t)
            t.setDaemon(True)
            t.start()
        for t in threads:
            t.join()
        return graph, crawled


def unit_test():
    print("Unit Test Begins.")
    test_crawler = BaseCrawler()
    print("Try to get the content of https://keithnull.top/")
    html = test_crawler.get_html("https://keithnull.top/")
    assert html.find("Keith") != -1
    print("Success")


def debugging():
    crawler = MultiThreadingCrawler()
    seed = "https://www.baidu.com"
    max_page = 10
    thread_num = 4
    crawler.crawl_from(seed, max_page, thread_num)


if __name__ == '__main__':
    # unit_test()
    debugging()
