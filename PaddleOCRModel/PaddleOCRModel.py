# %%
import sys
import threading
import time
import cv2
import os
import math
import copy
import onnxruntime
import numpy as np
import pyclipper
from shapely.geometry import Polygon
model_shape_w = 48
module_dir = os.path.dirname(os.path.abspath(__file__))
# print("model path",module_dir)
# %%
class NormalizeImage(object):
    """ normalize image such as substract mean, divide std
    """

    def __init__(self, scale=None, mean=None, std=None, order='chw', **kwargs):
        if isinstance(scale, str):
            scale = eval(scale)
        self.scale = np.float32(scale if scale is not None else 1.0 / 255.0)
        mean = mean if mean is not None else [0.485, 0.456, 0.406]
        std = std if std is not None else [0.229, 0.224, 0.225]

        shape = (3, 1, 1) if order == 'chw' else (1, 1, 3)
        self.mean = np.array(mean).reshape(shape).astype('float32')
        self.std = np.array(std).reshape(shape).astype('float32')

    def __call__(self, data):
        img = data['image']
        from PIL import Image
        if isinstance(img, Image.Image):
            img = np.array(img)

        assert isinstance(img,
                          np.ndarray), "invalid input 'img' in NormalizeImage"
        data['image'] = (
            img.astype('float32') * self.scale - self.mean) / self.std
        return data


class ToCHWImage(object):
    """ convert hwc image to chw image
    """

    def __init__(self, **kwargs):
        pass

    def __call__(self, data):
        img = data['image']
        from PIL import Image
        if isinstance(img, Image.Image):
            img = np.array(img)
        data['image'] = img.transpose((2, 0, 1))
        return data


class KeepKeys(object):
    def __init__(self, keep_keys, **kwargs):
        self.keep_keys = keep_keys

    def __call__(self, data):
        data_list = []
        for key in self.keep_keys:
            data_list.append(data[key])
        return data_list

class DetResizeForTest(object):
    def __init__(self, **kwargs):
        super(DetResizeForTest, self).__init__()
        self.resize_type = 0
        self.keep_ratio = False
        if 'image_shape' in kwargs:
            self.image_shape = kwargs['image_shape']
            self.resize_type = 1
            if 'keep_ratio' in kwargs:
                self.keep_ratio = kwargs['keep_ratio']
        elif 'limit_side_len' in kwargs:
            self.limit_side_len = kwargs['limit_side_len']
            self.limit_type = kwargs.get('limit_type', 'min')
        elif 'resize_long' in kwargs:
            self.resize_type = 2
            self.resize_long = kwargs.get('resize_long', 640)
        else:
            self.limit_side_len = 736
            self.limit_type = 'min'

    def __call__(self, data):
        img = data['image']
        src_h, src_w, _ = img.shape
        #print(self.resize_type)
        if sum([src_h, src_w]) < 64:
            img = self.image_padding(img)
        if self.resize_type == 0:
            # img, shape = self.resize_image_type0(img)
            img, [ratio_h, ratio_w] = self.resize_image_type0(img)
        elif self.resize_type == 2:
            img, [ratio_h, ratio_w] = self.resize_image_type2(img)
        else:
            # img, shape = self.resize_image_type1(img)
            img, [ratio_h, ratio_w] = self.resize_image_type1(img)
        data['image'] = img
        data['shape'] = np.array([src_h, src_w, ratio_h, ratio_w])
        return data

    def image_padding(self, im, value=0):
        h, w, c = im.shape
        im_pad = np.zeros((max(model_shape_w, h), max(model_shape_w, w), c), np.uint8) + value
        im_pad[:h, :w, :] = im
        return im_pad

    def image_padding_640(self, im, value=0):
        h, w, c = im.shape
        im_pad = np.zeros((max(640, h), max(640, w), c), np.uint8) + value
        im_pad[:h, :w, :] = im
        return im_pad

    def resize_image_type1(self, img):
        resize_h, resize_w = self.image_shape
        ori_h, ori_w = img.shape[:2]  # (h, w, c)
        if self.keep_ratio is True:
            resize_w = ori_w * resize_h / ori_h
            N = math.ceil(resize_w / model_shape_w)
            resize_w = N * model_shape_w
        ratio_h = float(resize_h) / ori_h
        ratio_w = float(resize_w) / ori_w
      
        img = cv2.resize(img, (int(resize_w), int(resize_h)))
        # return img, np.array([ori_h, ori_w])
        return img, [ratio_h, ratio_w]

    def resize_image_type0(self, img):
        """
        resize image to a size multiple of 48 which is required by the network
        args:
            img(array): array with shape [h, w, c]
        return(tuple):
            img, (ratio_h, ratio_w)
        """
        limit_side_len = self.limit_side_len
        h, w, c = img.shape

        # limit the max side
        if self.limit_type == 'max':
            if max(h, w) > limit_side_len:
                if h > w:
                    ratio = float(limit_side_len) / h
                else:
                    ratio = float(limit_side_len) / w
            else:
                ratio = 1.
        elif self.limit_type == 'min':
            if min(h, w) < limit_side_len:
                if h < w:
                    ratio = float(limit_side_len) / h
                else:
                    ratio = float(limit_side_len) / w
            else:
                ratio = 1.
        elif self.limit_type == 'resize_long':
            ratio = float(limit_side_len) / max(h, w)
        else:
            raise Exception('not support limit type, image ')
        resize_h = int(h * ratio)
        resize_w = int(w * ratio)

        resize_h = max(int(round(resize_h / model_shape_w) * model_shape_w), model_shape_w)
        resize_w = max(int(round(resize_w / model_shape_w) * model_shape_w), model_shape_w)

        try:
            if int(resize_w) <= 0 or int(resize_h) <= 0:
                return None, (None, None)
            img = cv2.resize(img, (int(resize_w), int(resize_h)))
        except:
            print(img.shape, resize_w, resize_h)
            sys.exit(0)
        ratio_h = resize_h / float(h)
        ratio_w = resize_w / float(w)
        return img, [ratio_h, ratio_w]

    def resize_image_type2(self, img):
        h, w, _ = img.shape

        resize_w = w
        resize_h = h

        if resize_h > resize_w:
            ratio = float(self.resize_long) / resize_h
        else:
            ratio = float(self.resize_long) / resize_w

        resize_h = int(resize_h * ratio)
        resize_w = int(resize_w * ratio)
        img = cv2.resize(img, (resize_w, resize_h))
        #这里加个0填充，适配固定shape模型
        img = self.image_padding_640(img)
        return img, [ratio, ratio]

# %%
### 检测结果后处理过程（得到检测框）
class DBPostProcess(object):
    """
    The post process for Differentiable Binarization (DB).
    """

    def __init__(self,
                 thresh=0.3,
                 box_thresh=0.7,
                 max_candidates=1000,
                 unclip_ratio=2.0,
                 use_dilation=False,
                 **kwargs):
        self.thresh = thresh
        self.box_thresh = box_thresh
        self.max_candidates = max_candidates
        self.unclip_ratio = unclip_ratio
        self.min_size = 3
        self.dilation_kernel = np.array([[1, 1], [1, 1]]) if use_dilation else None

    def boxes_from_bitmap(self, pred, _bitmap, dest_width, dest_height,ratio):
        '''
        _bitmap: single map with shape (1, H, W),
                whose values are binarized as {0, 1}
        '''
        bitmap = _bitmap
        #height, width = bitmap.shape  
        height, width = dest_height*ratio, dest_width*ratio,
    
        outs = cv2.findContours((bitmap * 255).astype(np.uint8), cv2.RETR_LIST,
                                cv2.CHAIN_APPROX_SIMPLE)
        if len(outs) == 3:
            img, contours, _ = outs[0], outs[1], outs[2]
        elif len(outs) == 2:
            contours, _ = outs[0], outs[1]

        num_contours = min(len(contours), self.max_candidates)

        boxes = []
        scores = []
        for index in range(num_contours):
            contour = contours[index]
            points, sside = self.get_mini_boxes(contour)
            if sside < self.min_size:
                continue
            points = np.array(points)
            score = self.box_score_fast(pred, points.reshape(-1, 2))
            if self.box_thresh > score:
                continue

            box = self.unclip(points).reshape(-1, 1, 2)
            box, sside = self.get_mini_boxes(box)
            if sside < self.min_size + 2:
                continue
            box = np.array(box)

            box[:, 0] = np.clip(   # 640 * 661
                np.round(box[:, 0] / width * dest_width), 0, dest_width)
            box[:, 1] = np.clip(
                np.round(box[:, 1] / height * dest_height), 0, dest_height)
            boxes.append(box.astype(np.int16))
            scores.append(score)
        return np.array(boxes, dtype=np.int16), scores

    def unclip(self, box):
        unclip_ratio = self.unclip_ratio
        poly = Polygon(box)
        distance = poly.area * unclip_ratio / poly.length
        offset = pyclipper.PyclipperOffset()
        offset.AddPath(box, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
        return np.array(offset.Execute(distance))

    def get_mini_boxes(self, contour):
        bounding_box = cv2.minAreaRect(contour)
        points = sorted(list(cv2.boxPoints(bounding_box)), key=lambda x: x[0])

        index_1, index_2, index_3, index_4 = 0, 1, 2, 3
        if points[1][1] > points[0][1]:
            index_1 = 0
            index_4 = 1
        else:
            index_1 = 1
            index_4 = 0
        if points[3][1] > points[2][1]:
            index_2 = 2
            index_3 = 3
        else:
            index_2 = 3
            index_3 = 2

        box = [
            points[index_1], points[index_2], points[index_3], points[index_4]
        ]
        return box, min(bounding_box[1])

    def box_score_fast(self, bitmap, _box):
        h, w = bitmap.shape[:2]
        box = _box.copy()
        xmin = np.clip(np.floor(box[:, 0].min()).astype(np.int32), 0, w - 1)
        xmax = np.clip(np.ceil(box[:, 0].max()).astype(np.int32), 0, w - 1)
        ymin = np.clip(np.floor(box[:, 1].min()).astype(np.int32), 0, h - 1)
        ymax = np.clip(np.ceil(box[:, 1].max()).astype(np.int32), 0, h - 1)

        mask = np.zeros((ymax - ymin + 1, xmax - xmin + 1), dtype=np.uint8)
        box[:, 0] = box[:, 0] - xmin
        box[:, 1] = box[:, 1] - ymin
        cv2.fillPoly(mask, box.reshape(1, -1, 2).astype(np.int32), 1)
        return cv2.mean(bitmap[ymin:ymax + 1, xmin:xmax + 1], mask)[0]

    def __call__(self, outs_dict, shape_list):
        pred = outs_dict
        pred = pred[:, 0, :, :]
        segmentation = pred > self.thresh
        boxes_batch = []
        for batch_index in range(pred.shape[0]):
            src_h, src_w, ratio_h, ratio_w = shape_list[batch_index]
            if self.dilation_kernel is not None:
                mask = cv2.dilate(
                    np.array(segmentation[batch_index]).astype(np.uint8),
                    self.dilation_kernel)
            else:
                mask = segmentation[batch_index]
            boxes, scores = self.boxes_from_bitmap(pred[batch_index], mask,
                                                   src_w, src_h,ratio_w)
            boxes_batch.append({'points': boxes})
        return boxes_batch


# %%
## 根据推理结果解码识别结果
class process_pred(object):
    def __init__(self, character_dict_path=None, character_type='ch', use_space_char=False):
        self.character_str = ''
        with open(character_dict_path, 'rb') as fin:
            lines = fin.readlines()
            for line in lines:
                line = line.decode('utf-8').strip('\n').strip('\r\n')
                self.character_str += line
        if use_space_char:
            self.character_str += ' '
        dict_character = list(self.character_str)

        dict_character = self.add_special_char(dict_character)
        self.dict = {char: i for i, char in enumerate(dict_character)}
        self.character = dict_character

    def add_special_char(self, dict_character):
        dict_character = ['blank'] + dict_character
        return dict_character

    def decode(self, text_index, text_prob=None, is_remove_duplicate=False):
        result_list = []
        ignored_tokens = [0]
        batch_size = len(text_index)
        for batch_idx in range(batch_size):
            char_list = []
            conf_list = []
            for idx in range(len(text_index[batch_idx])):
                if text_index[batch_idx][idx] in ignored_tokens:
                    continue
                if is_remove_duplicate and idx > 0 and text_index[batch_idx][idx - 1] == text_index[batch_idx][idx]:
                    continue
                char_list.append(self.character[int(text_index[batch_idx][idx])])
                if text_prob is not None:
                    conf_list.append(text_prob[batch_idx][idx])
                else:
                    conf_list.append(1)
            text = ''.join(char_list)
            result_list.append((text, np.mean(conf_list)))
        return result_list

    def __call__(self, preds, label=None):
        if not isinstance(preds, np.ndarray):
            preds = np.array(preds)
        preds_idx = preds.argmax(axis=2)
        preds_prob = preds.max(axis=2)
        text = self.decode(preds_idx, preds_prob, is_remove_duplicate=True)
        if label is None:
            return text
        label = self.decode(label)
        return text, label


# %%
class det_rec_functions(object):
    def __init__(self, image,use_dnn = False,version=3):
        global model_shape_w
        self.img = image.copy()
        self.det_file = os.path.join(module_dir,'modelv{}/det_model.onnx'.format(version))
        self.small_rec_file = os.path.join(module_dir,'modelv{}/rec_model.onnx'.format(version))
        model_shape_w = 48 if version == 3 else 32 # 适配v2和v3
        self.model_shape = [3,model_shape_w,1000]
        self.use_dnn = use_dnn
        if self.use_dnn == False:
            self.onet_det_session = onnxruntime.InferenceSession(self.det_file)
            self.onet_rec_session = onnxruntime.InferenceSession(self.small_rec_file)
        else:
            self.onet_det_session = cv2.dnn.readNetFromONNX(self.det_file)
            self.onet_rec_session = cv2.dnn.readNetFromONNX(self.small_rec_file)
        self.infer_before_process_op, self.det_re_process_op = self.get_process()
        self.postprocess_op = process_pred(os.path.join(module_dir,'ppocr_keys_v1.txt'), 'ch', True)

    ## 图片预处理过程
    def transform(self, data, ops=None):
        """ transform """
        if ops is None:
            ops = []
        for op in ops:
            data = op(data)
            if data is None:
                return None
        return data

    def create_operators(self, op_param_list, global_config=None):
        """
        create operators based on the config

        Args:
            params(list): a dict list, used to create some operators
        """
        assert isinstance(op_param_list, list), ('operator config should be a list')
        ops = []
        for operator in op_param_list:
            assert isinstance(operator,
                              dict) and len(operator) == 1, "yaml format error"
            op_name = list(operator)[0]
            param = {} if operator[op_name] is None else operator[op_name]
            if global_config is not None:
                param.update(global_config)
            op = eval(op_name)(**param)
            ops.append(op)
        return ops

    ### 检测框的后处理
    def order_points_clockwise(self, pts):
        """
        reference from: https://github.com/jrosebr1/imutils/blob/master/imutils/perspective.py
        # sort the points based on their x-coordinates
        """
        xSorted = pts[np.argsort(pts[:, 0]), :]

        # grab the left-most and right-most points from the sorted
        # x-roodinate points
        leftMost = xSorted[:2, :]
        rightMost = xSorted[2:, :]

        # now, sort the left-most coordinates according to their
        # y-coordinates so we can grab the top-left and bottom-left
        # points, respectively
        leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
        (tl, bl) = leftMost

        rightMost = rightMost[np.argsort(rightMost[:, 1]), :]
        (tr, br) = rightMost

        rect = np.array([tl, tr, br, bl], dtype="float32")
        return rect

    def clip_det_res(self, points, img_height, img_width):
        for pno in range(points.shape[0]):
            points[pno, 0] = int(min(max(points[pno, 0], 0), img_width - 1))
            points[pno, 1] = int(min(max(points[pno, 1], 0), img_height - 1))
        return points
    
    #shape_part_list = [661 969 7.74583964e-01 6.60474716e-01]
    def filter_tag_det_res(self, dt_boxes, shape_part_list):
        img_height, img_width = shape_part_list[0],shape_part_list[1]
        dt_boxes_new = []
        for box in dt_boxes:
            box = self.order_points_clockwise(box)
            box = self.clip_det_res(box, img_height, img_width) 
            rect_width = int(np.linalg.norm(box[0] - box[1]))
            rect_height = int(np.linalg.norm(box[0] - box[3]))
            if rect_width <= 3 or rect_height <= 3:
                continue
            dt_boxes_new.append(box)
        dt_boxes = np.array(dt_boxes_new)
        return dt_boxes

    ### 定义图片前处理过程，和检测结果后处理过程
    def get_process(self):
        det_db_thresh = 0.3
        det_db_box_thresh = 0.3
        max_candidates = 2000
        unclip_ratio = 1.6
        use_dilation = True
        # DetResizeForTest 定义检测模型前处理规则
        pre_process_list = [{
            'DetResizeForTest': {
                # 'limit_side_len': 2500,
                # 'limit_type': 'max',
                'resize_long': 640
                # 'image_shape':[640,640],
                # 'keep_ratio':True,
            }
        }, {
            'NormalizeImage': {
                'std': [0.229, 0.224, 0.225],
                'mean': [0.485, 0.456, 0.406],
                'scale': '1./255.',
                'order': 'hwc'
            }
        }, {
            'ToCHWImage': None
        }, {
            'KeepKeys': {
                'keep_keys': ['image', 'shape']
            }
        }]

        infer_before_process_op = self.create_operators(pre_process_list)
        det_re_process_op = DBPostProcess(det_db_thresh, det_db_box_thresh, max_candidates, unclip_ratio, use_dilation)
        return infer_before_process_op, det_re_process_op

    def sorted_boxes(self, dt_boxes):
        """
        Sort text boxes in order from top to bottom, left to right
        args:
            dt_boxes(array):detected text boxes with shape [4, 2]
        return:
            sorted boxes(array) with shape [4, 2]
        """
        num_boxes = dt_boxes.shape[0]
        sorted_boxes = sorted(dt_boxes, key=lambda x: (x[0][1], x[0][0]))
        _boxes = list(sorted_boxes)

        for i in range(num_boxes - 1):
            if abs(_boxes[i + 1][0][1] - _boxes[i][0][1]) < 10 and \
                    (_boxes[i + 1][0][0] < _boxes[i][0][0]):
                tmp = _boxes[i]
                _boxes[i] = _boxes[i + 1]
                _boxes[i + 1] = tmp
        return _boxes

    ### 图像输入预处理
    def resize_norm_img(self, img):
        imgC, imgH, imgW = [int(v) for v in self.model_shape]
        assert imgC == img.shape[2]
        h, w = img.shape[:2]
        ratio = w / float(h)
        if math.ceil(imgH * ratio) > imgW:
            resized_w = imgW
        else:
            resized_w = int(math.ceil(imgH * ratio))
        resized_image = cv2.resize(img, (resized_w, imgH))
        resized_image = resized_image.astype('float32')
        resized_image = resized_image.transpose((2, 0, 1)) / 255
        resized_image -= 0.5
        resized_image /= 0.5
        padding_im = np.zeros((imgC, imgH, imgW), dtype=np.float32)
        padding_im[:, :, 0:resized_w] = resized_image
        return padding_im
    def draw_boxes(self,boxes,image,display = False):
        for points in boxes:
            # 将四个点转换成轮廓格式
            contours = [points.astype(int)]
            # 绘制边框
            cv2.drawContours(image, contours, -1, (0, 255, 0), 1)
            # cv2.putText(image,str(contours),(points[0],points[1]))
        # cv2.imwrite("testocr.png",image)
        # 显示图像
        if display:
            # cv2.namedWindow("Bounding Boxes", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Bounding Boxes", 1280, 720)
            cv2.imshow("Bounding Boxes", image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        return image
    ## 推理检测图片中的部分
    def get_boxes(self):
        img_ori = self.img
        img_part = img_ori.copy()
        data_part = {'image': img_part}
        data_part = self.transform(data_part, self.infer_before_process_op)
        img_part, shape_part_list = data_part
        img_part = np.expand_dims(img_part, axis=0)
        shape_part_list = np.expand_dims(shape_part_list, axis=0)
        if self.use_dnn == True:
            self.onet_det_session.setInput(img_part)  
            outs_part = self.onet_det_session.forward()
        else:
            inputs_part = {self.onet_det_session.get_inputs()[0].name: img_part}
            outs_part = self.onet_det_session.run(None, inputs_part)
            outs_part = outs_part[0]
        print(outs_part.shape)
        post_res_part = self.det_re_process_op(outs_part, shape_part_list)
        dt_boxes_part = post_res_part[0]['points']
        dt_boxes_part = self.filter_tag_det_res(dt_boxes_part,shape_part_list[0])
        dt_boxes_part = self.sorted_boxes(dt_boxes_part)
        
        return dt_boxes_part,img_part

    ### 根据bounding box得到单元格图片
    def get_rotate_crop_image(self, img, points):
        img_crop_width = int(
            max(
                np.linalg.norm(points[0] - points[1]),
                np.linalg.norm(points[2] - points[3])))
        img_crop_height = int(
            max(
                np.linalg.norm(points[0] - points[3]),
                np.linalg.norm(points[1] - points[2])))
        pts_std = np.float32([[0, 0], [img_crop_width, 0],
                              [img_crop_width, img_crop_height],
                              [0, img_crop_height]])
        M = cv2.getPerspectiveTransform(points, pts_std)
        dst_img = cv2.warpPerspective(
            img,
            M, (img_crop_width, img_crop_height),
            borderMode=cv2.BORDER_REPLICATE,
            flags=cv2.INTER_CUBIC)
        dst_img_height, dst_img_width = dst_img.shape[0:2]
        if dst_img_height * 1.0 / dst_img_width >= 1.5:
            dst_img = np.rot90(dst_img)
        return dst_img

    ### 单张图片推理
    def get_img_res(self, onnx_model, img, process_op):
        img = self.resize_norm_img(img)
        img = img[np.newaxis, :]
        if self.use_dnn:
            onnx_model.setInput(img)  # 设置模型输入
            outs = onnx_model.forward()  # 推理出结果
        else:
            inputs = {onnx_model.get_inputs()[0].name: img}
            outs = onnx_model.run(None, inputs)
            outs = outs[0]
        return process_op(outs)
    
    def process_n_pic(self,piclist):
        results = []
        results_info = []
        for pic in piclist:
            res = self.get_img_res(self.onet_rec_session, pic, self.postprocess_op)
            results.append(res[0])
            results_info.append(res)
    def get_match_text_boxes(self,dt_boxes,results,threshold = 0.5):
        match_text_boxes = []
        for pos, textres in zip(dt_boxes,results):
            if textres[1]>threshold:
                text = textres[0]
                match_text_boxes.append({'text': text, 'box': pos})
        return match_text_boxes
    
    def get_format_text(self,match_text_boxes):
        if len(match_text_boxes) == 0:
            return "no result"
        text_blocks = []
        total_h = 0
        for text_box in match_text_boxes:
            pos = text_box["box"]
            text = text_box["text"]
            # 提取最小的x和y
            min_x = np.min(pos[:, 0])
            min_y = np.min(pos[:, 1])

            # 提取近似的宽度和高度
            width = np.max(pos[:, 0]) - min_x
            height = np.max(pos[:, 1]) - min_y
            total_h += height
            print((min_x, min_y, width, height))
            text_blocks.append({'text': text, 'box': (min_x, min_y, width, height)})
        
        av_h = int(total_h/len(text_blocks))       
        def sort_blocks(blocks):
            # 定义一个排序函数
            def sort_func(block):
                # 获取box中的x和y
                x, y, w, h = block['box']
                # 返回一个元组，第一个元素是x，第二个元素是y，如果两个块的x相差小于h//2，则比较y
                return ( y//av_h,x)
            
            # 使用sorted函数进行排序，key参数传入排序函数
            return sorted(blocks, key=sort_func)
        # 按照文字块的顶部位置从上到下排序
        text_blocks = sort_blocks(text_blocks)

        # 拼接所有文字块的识别结果
        result = ''
        last_bottom = 0
        last_right = 0
        first_line_x = 0
        adding_line_first_W = False
        for i,block in enumerate(text_blocks):
            text = block['text']
            box = block['box']
            x, y, w, h = box
            top = y
            bottom = y + h
            if i == 0 :
                result += text
                last_bottom = bottom
                last_right = x + w
                first_line_x = x
                continue
            print(block,top , bottom,last_bottom - h // 2)
            # 如果当前文字块的顶部位置比上一个文字块的底部位置高，则需要换行
            new_line = False
            if top > last_bottom - h // 2:
                result += '\n'
                last_right = 0
                new_line=True
                print("add new line")
            if new_line:
                if x - first_line_x > h // 2:
                    result += ' ' * (int(x-last_right)//av_h)
            # 如果当前文字块的左侧位置比上一个文字块的右侧位置大，则需要增加空格
            elif x > last_right:
                result += ' ' * (int(x - last_right)//av_h)
                print("add space")
                
            # 添加当前文字块的识别结果
            result += text
            
            # 更新上一个文字块的底部位置和右侧位置
            last_bottom = bottom
            last_right = x + w

        return result
    def recognition_img(self, dt_boxes):
        stime = time.time()
        img_ori = self.img  #原图大小
        img = img_ori.copy()
        img_list = []
        for box in dt_boxes[0]:
            tmp_box = copy.deepcopy(box)
            img_crop = self.get_rotate_crop_image(img, tmp_box)
            img_list.append(img_crop)
        ptime = time.time()
        print("rec preprocess time",ptime-stime)
        ## 识别小图片
        results = []
        results_info = []
        for pic in img_list:
            res = self.get_img_res(self.onet_rec_session, pic, self.postprocess_op)
            results.append(res[0])
            results_info.append(res)
        # threads = []
        # tmp_img = []
        # for i, pic in enumerate(img_list):
        #     tmp_img.append(pic)
        #     if len(tmp_img)==116 or i == len(img_list)-1:
        #         print("process len",len(tmp_img))
        #         thread = threading.Thread(target=self.process_n_pic,args=(copy.deepcopy(tmp_img),))
        #         thread.start()
        #         threads.append(thread)
        #         tmp_img = []
        # print("waiting..")
        # # 等待所有线程执行完毕
        # for thread in threads:
        #     thread.join()
            
        print("rec end time",time.time()-ptime)
        return results, results_info


# %%
if __name__=='__main__':
    # 读取图片
    image = cv2.imread('./00.png')
    # 文本检测
    # 模型固化为640*640 需要修改对应前处理，box的后处理。
    # ocr_sys = det_rec_functions(image,use_dnn = True)
    # # 得到检测框
    # dt_boxes = ocr_sys.get_boxes()
    # # 识别 results: 单纯的识别结果，results_info: 识别结果+置信度    原图
    # # 识别模型固定尺寸只能100长度，需要处理可以根据自己场景导出模型 1000
    # # onnx可以支持动态，不受限
    # results, results_info = ocr_sys.recognition_img(dt_boxes)
    # print(f'opencv dnn :{str(results)}')
    # print('------------------------------')
    
    ocr_sys = det_rec_functions(image,use_dnn = False,version=3)# 支持v2和v3版本的
    stime = time.time()
    # 得到检测框
    dt_boxes = ocr_sys.get_boxes()
    ocr_sys.draw_boxes(dt_boxes[0],image,display=True)
    dettime = time.time()
    print(len(dt_boxes[0]),dt_boxes[0][:3])
    # 识别 results: 单纯的识别结果，results_info: 识别结果+置信度    原图
    # 识别模型固定尺寸只能100长度，需要处理可以根据自己场景导出模型 1000
    # onnx可以支持动态，不受限
    results, results_info = ocr_sys.recognition_img(dt_boxes)
    print(f'results :{str(results)}',len(results))
    print(f'results_info :{str(results_info)}')
    print(ocr_sys.get_format_text(ocr_sys.get_match_text_boxes(dt_boxes[0],results)))
    print(time.time()-dettime,dettime - stime)



