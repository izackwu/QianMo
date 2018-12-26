import align.detect_face
import facenet
import numpy as np
import tensorflow as tf
from scipy import misc
import os
import cv2


data_dir = "../data"
image_dir = os.path.join(data_dir, "image_data")
face_feature_file = os.path.join(data_dir, "face_feature.npy")
face_info_file = os.path.join(data_dir, "face_info.txt")

target_image_file = os.path.join(image_dir, "2cfea024ce730e291cfcc8ad48759f13.jpg")

facenet_model = "20180408-102900/"


def extract_feature(image_file, face_size=160, margin=44, gpu_memory_fraction=0.6):
    minsize = 20  # minimum size of face
    threshold = [0.6, 0.7, 0.7]  # three steps's threshold
    factor = 0.709  # scale factor
    with tf.Graph().as_default():
        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=gpu_memory_fraction)
        sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options, log_device_placement=False))
        with sess.as_default():
            pnet, rnet, onet = align.detect_face.create_mtcnn(sess, None)
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
            feed_dict = {images_placeholder: face_tensor, phase_train_placeholder: False}
            print("Begins to compute embeddings...")
            face_embedding = sess.run(embeddings, feed_dict=feed_dict)
    return face_embedding[0]


if __name__ == '__main__':
    target_feature = extract_feature(target_image_file)
    all_faces = np.load(face_feature_file)
    similarity = np.dot(all_faces, target_feature.T)
    print(similarity.shape)
    sorted_index = np.argsort(similarity)
    print(sorted_index.shape)
    with open(face_info_file, mode="r", encoding="utf8") as f:
        face_info_list = f.readlines()
    for i in range(1, 11):
        face_info = face_info_list[sorted_index[-i]]
        image_path = face_info.split()[1]
        print(i, similarity[sorted_index[-i]], image_path)
        # image = cv2.imread(image_path)    # uncomment these if you have cv2 available
        # cv2.imshow(str(i+1), image)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
