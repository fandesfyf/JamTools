# PaddleOCR-OpenCV-DNN
尝试 opencv dnn 推理 paddleocr ；大部分代码来自PaddleOCR项目，修改前后处理适配DNN推理。


## 环境：

 - onnx 	 1.11.0
 - onnxruntime 	 1.10.0
 - opencv  4.5.5.62
 - paddle2onnx 	1.0.1
 - paddlpaddle   2.3.2

## 转换模型
 - 使用paddle2onnx 转换模型：
  见aistudio项目地址: https://aistudio.baidu.com/aistudio/projectdetail/5672175?contributionType=1

- onnx模型simplifier：https://convertmodel.com/

- 推理

## 不足：
	
 - 由于固化模型shape，使得部分特殊场景下效果不良，如长条形图片，降低了通用性；可根据自己对应的场景去固化模型尺寸（通用场景下建议导出dynamic shape模型，使用onnxruntime推理）。

 - 相同图片下（前后处理一致），速度方面DNN比onnxruntime慢（大约2~3倍）。
 - 精度未与原始paddle模型对比；简单测试效果尚可。
 - 测试PaddleOCR v3版本，det模型dnn支持，rec模型dnn推理。

## 引用：
 - https://github.com/PaddlePaddle/PaddleOCR
 - https://github.com/PaddlePaddle/Paddle2ONNX
 - https://github.com/daquexian/onnx-simplifier
 - https://blog.csdn.net/favorxin/article/details/115270800
