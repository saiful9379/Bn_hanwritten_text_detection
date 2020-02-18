import glob
import os

image_path = "train/img"
ann_txt_name = "train"
txt_path = image_path.split("/")[0]+"/gt"
file_ = glob.glob(image_path+"/*")
annotation = open(ann_txt_name+".txt","w")
for i in file_:
    txt_file = i.split("/")[-1][:-4]+".txt"
    txt_file = os.path.join(txt_path,txt_file)
    if os.path.exists(txt_file):
        image_dir_="./datasets/" + i
        txt_file_dir = "./datasets/" + txt_file
        annotation.write(image_dir_ + "\t" + txt_file_dir+ "\n")
        print(image_dir_,txt_file_dir)
annotation.close()