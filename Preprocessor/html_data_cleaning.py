import os

total = 0
valid = 0
file_to_remove = []
with open("..\\data\\index.txt", encoding="utf8", mode="r") as original_index:
    with open("..\\data\\new_index.txt", encoding="utf8", mode="w") as new_index:
        for line in original_index:
            total += 1
            try:
                url, file = line.split()
            except:
                continue
            if not os.path.exists(file):
                continue
            if url.find("fileUpload.action") != -1 or url.find("download.action") != -1 or os.path.getsize(file) <= 2048:
                file_to_remove.append(file)
                continue
            new_index.write("{}\t{}\n".format(url, file))
            valid += 1
print("{}/{}".format(valid, total))
confirm = input("There are {} invalid files, remove all?".format(len(file_to_remove)))
if confirm and confirm[0].lower() == 'y':
    for file in file_to_remove:
        os.remove(file)
    print("All removed.")
