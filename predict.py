# -*- coding: utf-8 -*-

import torch
from torchvision import transforms
import os
import cv2
import time
import numpy as np

from models import get_model
import pyclipper
import glob

class Pytorch_model:
    def __init__(self, model_path, gpu_id=None):
        '''
        初始化pytorch模型
        :param model_path: 模型地址(可以是模型的参数或者参数和计算图一起保存的文件)
        :param gpu_id: 在哪一块gpu上运行
        '''
        self.gpu_id = gpu_id
        
        if self.gpu_id is not None and isinstance(self.gpu_id, int) and torch.cuda.is_available():
            self.device = torch.device("cuda:%s" % self.gpu_id)
            checkpoint = torch.load(model_path)
        else:
            self.device = torch.device("cpu")
            checkpoint = torch.load(model_path, map_location='cpu')
        print('device:', self.device)

        config = checkpoint['config']
        config['arch']['args']['pretrained'] = False
        self.net = get_model(config)

        self.img_channel = config['data_loader']['args']['dataset']['img_channel']
        self.net.load_state_dict(checkpoint['state_dict']) ## load weights
        self.net.to(self.device)
        self.net.eval()

    def predict(self, img: str, short_size: int = 736, min_area: int = 100):
        '''
        对传入的图像进行预测，支持图像地址, opencv读取图片，偏慢
        :param img: 图像地址
        :param short_size: 
        :param min_area: 小于该尺度的bbox忽略
        :return:
        '''
        # print(img)
        assert os.path.exists(img), 'file is not exists'
        img = cv2.imread(img)
        if self.img_channel == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        scale = short_size / min(h, w)
        img = cv2.resize(img, None, fx=scale, fy=scale)

        tensor = transforms.ToTensor()(img)
        tensor = tensor.unsqueeze_(0)

        tensor = tensor.to(self.device)
        with torch.no_grad():
            # todo by saiful
            # torch.cuda.synchronize(self.device) # if you use GPU please uncommet this line
            start = time.time()
            preds = self.net(tensor)[0]
            # torch.cuda.synchronize(self.device) # if you use GPU please uncommet this line
            scale = (preds.shape[2] / w, preds.shape[1] / h)
            t = time.time() - start
            
        '''inference'''
        start = time.time()
        prob_map, thres_map = preds[0], preds[1]
        
        ## Step 1: Use threshold to get the binary map 
        thr = 0.2
        out = (prob_map > thr).float() * 255
        out = out.data.cpu().numpy().astype(np.uint8)
        # cv2.imwrite('c_bin_map.png', out)   
        
        ## Step 2: Connected components findContours
        contours, hierarchy = cv2.findContours(out, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = [(i / scale).astype(np.int) for i in contours if len(i)>=4] 
                
        # Step 3: Dilate the shrunk region (not necessary)    
        ratio_prime = 1.5
        dilated_polys = []
        for poly in contours:
            poly = poly[:,0,:]
            D_prime = cv2.contourArea(poly) * ratio_prime / cv2.arcLength(poly, True) # formula(10) in the thesis
            pco = pyclipper.PyclipperOffset()
            pco.AddPath(poly, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
            dilated_poly = np.array(pco.Execute(D_prime))
            if dilated_poly.size == 0 or dilated_poly.dtype != np.int or len(dilated_poly) != 1:
                continue
            dilated_polys.append(dilated_poly)
            
        boxes_list = []
        for cnt in dilated_polys:
            # print('=============')
            # print(cnt)
            # print(len(cnt))
            if cv2.contourArea(cnt) < min_area:
                continue
            rect = cv2.minAreaRect(cnt)
            box = (cv2.boxPoints(rect)).astype(np.int)
            boxes_list.append(box)
        
        t = time.time() - start + t
            
        boxes_list = np.array(boxes_list)
        return dilated_polys, boxes_list, t


if __name__ == '__main__':
    from utils.util import show_img, draw_bbox
    # todo by saiful
    os.environ["CUDA_VISIBLE_DEVICES"] = "0" # if use GPU please uncomment this line
    model_path = './output/DB_shufflenetv2_FPN/DBNet_best_loss.pth'    
    
    ## icdar 2013 / 2015
    img_id = 130
    img_dir = glob.glob("demo/*.jpg")
    # img_path = 'demo/2.jpg'
    
    # todo by saiful
    model = Pytorch_model(model_path, gpu_id = None)  ## set GPU id or None if you only have cpu
    cnt = 0
    for i in img_dir:
        contours, boxes_list, t = model.predict(i)
        print('Time: %.4f' %t)
    
        img = cv2.imread(i)[:, :, ::-1]
        imgc = img.copy()
        cv2.drawContours(imgc, contours, -1, (22,222,22), 1, cv2.LINE_AA)
        cv2.imwrite('logs/contour_'+str(cnt)+".jpg", imgc)
        img = draw_bbox(img, boxes_list)
        cv2.imwrite('logs/image_'+str(cnt)+".jpg", img)
        cnt+=1

