import cv2
import sys
import os

faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

total, face_exist = 0, 0
images_with_faces = list()

data_dir = "..\\data"
image_dir = os.path.join(data_dir, "image_data")
image_index = os.path.join(data_dir, "image_index.txt")
new_image_index = os.path.join(data_dir, "new_image_index.txt")

with open(image_index, mode="r", encoding="utf8") as i_index:
    with open(new_image_index, mode="w", encoding="utf8") as new_i_index:
        for line in i_index:
            # print(line.split())
            try:
                image_url, image_file, page_url, html_file = line.split()
            except:
                continue
            total += 1
            gray_img = cv2.imread(os.path.join(image_dir, image_file), cv2.IMREAD_GRAYSCALE)
            gray_img = cv2.equalizeHist(gray_img)
            faces = faceCascade.detectMultiScale(
                gray_img,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(10, 10)
            )
            if len(faces) > 0:
                print("\n{img}".format(img=image_file))
                face_exist += 1
                new_i_index.write("{image_url}\t{image_file}\t{page_url}\t{face_num}\n".format(
                    image_url=image_url, image_file=image_file, page_url=page_url, face_num=len(faces)))
            print("\r{}/{}".format(face_exist, total), end="")
