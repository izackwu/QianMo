import web
import sys
import os
import time
from elasticsearch_dsl.connections import connections

es = connections.create_connection(hosts=["localhost"])


def search_html(query_string, page=1, page_size=10):
    search_from = page_size * (page - 1)
    index = "qianmo"
    doc_type = "doc"
    fields = ["title", "text"]
    tick = time.time()
    response = es.search(
        index=index,
        doc_type=doc_type,
        body={
            "query": {
                "multi_match": {
                    "query": query_string,
                    "fields": fields
                }
            },
            "from": search_from,
            "size": page_size,
            "highlight": {
                "pre_tags": ["<span class = \"highlight\">"],
                "post_tags": ["</span>"],
                "fields": {
                    "title": {
                        "no_match_size": 100    # if there's nothing matched, just return the first 100 chars
                    },
                    "text": {
                        "fragment_size": 25,
                        "number_of_fragments": 4,
                        "no_match_size": 100
                    }
                }
            }
        }
    )
    tock = time.time()
    time_used = tock - tick
    result_num = response["hits"]["total"]
    search_result = list()
    for hit in response["hits"]["hits"]:
        single_result = dict()
        single_result["title"] = hit["highlight"]["title"][0]
        single_result["content"] = "...".join(hit["highlight"]["text"])
        single_result["url"] = hit["_source"]["url"]
        search_result.append(single_result)
    result_data = {
        "time_used": time_used,
        "total_num": result_num,
        "page": page,
        "search_result": search_result,
        "query_string": query_string,
    }
    return result_data


def search_image(query_string, result_num=10):
    # To Do
    pass


class Index:
    def GET(self):
        return render.index()


class IndexImage:
    def GET(self):
        return render.index_image()


class Search:
    def GET(self, search_type="html"):
        search_data = web.input()
        query_string = search_data.get("s", "")
        page = int(search_data.get("page", 1))
        if search_type not in ("html", "image"):
            search_type = "html"
        if not query_string:
            return render.index_image() if search_type == "image" else render.index()
        result_data = search_function[search_type](query_string, page)
        return result_template[search_type](**result_data)


urls = (
    "/", "Index",
    "/image", "IndexImage",
    "/search/(.+)", "Search",

)

render = web.template.render("templates")
search_function = {
    "html": search_html,
    "image": search_image,
}
result_template = {
    "html": render.result,
    "image": render.result_image,
}

if __name__ == '__main__':
    app = web.application(urls, globals(), autoreload=True)
    app.run()
