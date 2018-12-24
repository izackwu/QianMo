'''
This Python script demonstrates the clenned image data (images containing face(s))
'''

import cv2
import os
import random

data_dir = "..\\data"
image_dir = os.path.join(data_dir, "image_data")
new_image_index = os.path.join(data_dir, "new_image_index.txt")

image_list = list()

with open(new_image_index, mode="r", encoding="utf8") as index:
    for line in index:
        _, image_file, _, face_num = line.split()
        image_list.append((image_file, face_num))

image_num = len(image_list)
while True:
    image_file, face_num = image_list[random.randint(0, image_num-1)]
    image = cv2.imread(os.path.join(image_dir, image_file))
    cv2.imshow("face_num:{}".format(face_num), image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
