import web
import sys
import os
import time
import requests
import json
import hashlib
import align.detect_face
import facenet
import numpy as np
import tensorflow as tf
from scipy import misc
import os
from elasticsearch_dsl.connections import connections

data_dir = "../data"
face_feature_file = os.path.join(data_dir, "face_feature.npy")
face_info_file = os.path.join(data_dir, "face_info.txt")

facenet_model = "20180408-102900/"


def extract_feature(image_file, face_size=160, margin=44, gpu_memory_fraction=0.6):
    minsize = 20  # minimum size of face
    threshold = [0.6, 0.7, 0.7]  # three steps's threshold
    factor = 0.709  # scale factor
    image = misc.imread(image_file, mode="RGB")
    image_size = image.shape[0:2]
    bounding_boxes, _ = align.detect_face.detect_face(image, minsize, pnet, rnet, onet, threshold, factor)
    if len(bounding_boxes) < 1:
        print("\ncan't detect face, ignore ", image_file)
        return None
    det = np.squeeze(bounding_boxes[0][0:4])
    bb = np.zeros(4, dtype=np.int32)
    bb[0] = np.maximum(det[0]-margin/2, 0)
    bb[1] = np.maximum(det[1]-margin/2, 0)
    bb[2] = np.minimum(det[2]+margin/2, image_size[1])
    bb[3] = np.minimum(det[3]+margin/2, image_size[0])
    cropped = image[bb[1]:bb[3], bb[0]:bb[2], :]
    aligned = misc.imresize(cropped, (face_size, face_size), interp='bilinear')
    prewhitened = facenet.prewhiten(aligned)
    face_tensor = prewhitened[np.newaxis, :, :, :]
    with graph.as_default():
        with sess.as_default():
            # Get input and output tensors
            images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
            # Run forward pass to calculate embeddings
            feed_dict = {images_placeholder: face_tensor, phase_train_placeholder: False}
            print("Begins to compute embeddings...")
            face_embedding = sess.run(embeddings, feed_dict=feed_dict)
    return face_embedding[0]


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


def search_face(image_hash):
    result_data = dict()
    result_data["target_url"] = "/static/upload/" + image_hash+".jpg"
    result_data["search_result"] = list()
    image_file = os.path.join(upload_dir, image_hash+".jpg")
    target_feature = extract_feature(image_file)
    if not target_feature:
        print("No face detected!")
        return result_data
    all_faces = np.load(face_feature_file)
    similarity = np.dot(all_faces, target_feature.T)
    print(similarity.shape)
    sorted_index = np.argsort(similarity)
    print(sorted_index.shape)
    with open(face_info_file, mode="r", encoding="utf8") as f:
        face_info_list = f.readlines()
    prev_similarity = None
    for i in range(1, 21):
        print(similarity[sorted_index[-i]])
        if similarity[sorted_index[-i]] <= 0.75:
            break
        if prev_similarity == similarity[sorted_index[-i]]:
            continue
        prev_similarity = similarity[sorted_index[-i]]
        face_info = face_info_list[sorted_index[-i]]
        image_url = face_info.split()[0]
        result_data["search_result"].append({
            "url": image_url,
        })
    return result_data


class Index:
    def GET(self):
        return render.index()


class IndexFace:
    def GET(self):
        return render.index_face()


class SearchHtml:
    def GET(self):
        search_data = web.input()
        query_string = search_data.get("s", "")
        page = int(search_data.get("page", 1))
        if not query_string:
            return render.index()
        result_data = search_html(query_string, page)
        return render.result(**result_data)


class SearchFace:
    def POST(self):
        return None

    def GET(self, image_hash):
        result_data = search_face(image_hash)
        return render.result_face(**result_data)


class Upload:

    def POST(self):
        x = web.input()
        if "files[]" not in x:
            print("No file found!")
            return None
        # print(x)
        image_content = x.get("files[]")
        md5 = hashlib.md5()
        md5.update(image_content)
        image_hash = md5.hexdigest()
        image_path = os.path.join(upload_dir, str(image_hash)+".jpg")
        if not os.path.exists(image_path):
            with open(image_path, mode="wb") as f:
                f.write(image_content)
        result_info = {
            "hash": image_hash,
        }
        print(json.dumps(result_info))
        web.header('content-type', 'text/json')
        return json.dumps(result_info)


urls = (
    "/", "Index",
    "/face", "IndexFace",
    "/search/html", "SearchHtml",
    "/search/face/(.+)", "SearchFace",
    "/image-upload", "Upload",
)

render = web.template.render("templates")
es = connections.create_connection(hosts=["localhost"])
upload_dir = "static/upload"
graph = tf.Graph()
with graph.as_default():
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.6)
    sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options, log_device_placement=False))
    with sess.as_default():
        pnet, rnet, onet = align.detect_face.create_mtcnn(sess, None)
    # Load the model
        facenet.load_model(facenet_model)
print("Ready to go")
if __name__ == '__main__':
    app = web.application(urls, globals(), autoreload=False)
    app.run()
