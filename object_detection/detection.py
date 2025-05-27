import cv2
import numpy as np
import urllib.request

url = 'http://192.168.20.5/cam-hi.jpg'

whT = 320
confThreshold = 0.5
nmsThreshold = 0.3

# Load class names
with open('./object_detection/names', 'r') as f:
    classNames = [line.strip() for line in f.readlines()]

modelConfig = './object_detection/yolov3.cfg'
modelWeights = './object_detection/yolov3.weights'
net = cv2.dnn.readNetFromDarknet(modelConfig, modelWeights)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

def findObject(outputs, im):
    hT, wT, cT = im.shape
    bbox = []
    classIds = []
    confs = []
    for output in outputs:
        for det in output:
            scores = det[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]
            if confidence > confThreshold:
                w, h = int(det[2] * wT), int(det[3] * hT)
                x, y = int((det[0] * wT) - w / 2), int((det[1] * hT) - h / 2)
                bbox.append([x, y, w, h])
                classIds.append(classId)
                confs.append(float(confidence))

    indices = cv2.dnn.NMSBoxes(bbox, confs, confThreshold, nmsThreshold)

    if len(indices) > 0:
        for i in indices.flatten():
            box = bbox[i]
            x, y, w, h = box[0], box[1], box[2], box[3]

            # Ensure bounding box stays within the image boundaries
            x, y, w, h = max(0, x), max(0, y), min(wT - x, w), min(hT - y, h)

            label = f'{classNames[classIds[i]].upper()} {int(confs[i] * 100)}%'
            cv2.rectangle(im, (x, y), (x + w, y + h), (255, 0, 255), 2)
            cv2.putText(im, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

while True:
    try:
        img_resp = urllib.request.urlopen(url)
        imgnp = np.array(bytearray(img_resp.read()), dtype=np.uint8)
        im = cv2.imdecode(imgnp, -1)

        if im is None:
            print("Failed to capture image")
            continue

        blob = cv2.dnn.blobFromImage(im, 1 / 255, (whT, whT), [0, 0, 0], 1, crop=False)
        net.setInput(blob)
        layernames = net.getLayerNames()
        outputNames = [layernames[i - 1] for i in net.getUnconnectedOutLayers()]

        outputs = net.forward(outputNames)

        findObject(outputs, im)

        # Resize image to fit the window
        im_resized = cv2.resize(im, (640, 480))
        cv2.imshow('Image', im_resized)
        if cv2.waitKey(1) == 27:  # Press ESC to exit
            break
    except Exception as e:
        print("Error:", e)
        continue

cv2.destroyAllWindows()
