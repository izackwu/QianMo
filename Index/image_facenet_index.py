from __future__ import absolute_import  # be compatible with Python 2
from __future__ import division         # as there's no Python 3 on my lab's server
from __future__ import print_function


import align.detect_face
import facenet
import numpy as np
import tensorflow as tf
from scipy import misc
import os


data_dir = "../data"
image_index_file = os.path.join(data_dir, "new_image_index.txt")
image_dir = os.path.join(data_dir, "image_data")
face_feature_file = os.path.join(data_dir, "face_feature.npy")
face_info_file = os.path.join(data_dir, "face_info.txt")

facenet_model = "20180408-102900/"


def load_and_detect_faces(image_index_file, face_size, margin, gpu_memory_fraction=0.6):

    minsize = 20  # minimum size of face
    threshold = [0.6, 0.7, 0.7]  # three steps's threshold
    factor = 0.709  # scale factor
    info_list = []
    face_list = []
    face_num = 0
    image_num = 0
    with tf.Graph().as_default():
        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=gpu_memory_fraction)
        sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options, log_device_placement=False))
        with sess.as_default():
            pnet, rnet, onet = align.detect_face.create_mtcnn(sess, None)
    with open(image_index_file, mode="r") as image_index:
        for line in image_index:
            print("\rFaces Detected:{}/{}".format(face_num, image_num), end="")
            image_num += 1
            image_url, image_file, page_url, cv2_face_num = line.split()
            cv2_face_num = int(cv2_face_num)
            image_file = os.path.join(image_dir, image_file)
            image = misc.imread(image_file, mode="RGB")
            image_size = image.shape[0:2]
            bounding_boxes, _ = align.detect_face.detect_face(image, minsize, pnet, rnet, onet, threshold, factor)
            if len(bounding_boxes) < 1:
                print("\ncan't detect face, ignore ", image_file)
                continue
            for box in bounding_boxes:
                det = np.squeeze(box[0:4])
                bb = np.zeros(4, dtype=np.int32)
                bb[0] = np.maximum(det[0]-margin/2, 0)
                bb[1] = np.maximum(det[1]-margin/2, 0)
                bb[2] = np.minimum(det[2]+margin/2, image_size[1])
                bb[3] = np.minimum(det[3]+margin/2, image_size[0])
                cropped = image[bb[1]:bb[3], bb[0]:bb[2], :]
                aligned = misc.imresize(cropped, (face_size, face_size), interp='bilinear')
                prewhitened = facenet.prewhiten(aligned)
                face_list.append(prewhitened)
                face_num += 1
                info_list.append([image_url, image_file, page_url])
    face_array = np.stack(face_list)
    return face_array, info_list


def main():

    face_array, info_list = load_and_detect_faces(image_index_file, face_size=160, margin=44)
    face_embeddings = None
    face_num = len(face_array)
    assert face_num == len(info_list)
    with open(face_info_file, mode="w") as file:
        for info in info_list:
            file.write("{}\t{}\t{}\n".format(*info))
    face_embeddings = list()
    for i in range(0, face_num, 1000):  # avoid tf's OOM error
        slice_from, slice_to = i, min(i+1000, face_num)
        with tf.Graph().as_default():
            gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.6)
            with tf.Session(config=tf.ConfigProto(gpu_options=gpu_options, log_device_placement=False)) as sess:
                # Load the model
                facenet.load_model(facenet_model)
                # Get input and output tensors
                images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
                embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
                phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
                # Run forward pass to calculate embeddings
                feed_dict = {images_placeholder: face_array[slice_from:slice_to], phase_train_placeholder: False}
                print("Begins to compute embeddings...")
                face_embeddings.append(sess.run(embeddings, feed_dict=feed_dict))
                print(face_embeddings[-1].shape)
    face_embeddings = np.vstack(face_embeddings)
    assert face_num == len(face_embeddings), face_embeddings.shape
    np.save(face_feature_file, face_embeddings)


if __name__ == '__main__':

    main()
