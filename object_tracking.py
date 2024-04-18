import torch 
import cv2
import numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort
from models.common import DetectMultiBackend, AutoShape

# Config
video_path = "data_ext/people.mp4"
conf_threshold = 0.5
tracking_class = 0

# Initialize DeepSort
tracker = DeepSort(max_age=5)

# Initialize YOLO
device_str = "cuda"
device = torch.device(device_str)
model = DetectMultiBackend(weights="weights/yolov9-c-converted.pt", device=device, fuse=True)

model = AutoShape(model)

#Load classname 
with open("data_ext/classes.names") as f:
    class_names = f.read().strip().split("\n")
    
colors = np.random.randint(0, 255, size=(len(class_names), 3))

tracks = []

# Initialize Videocapture form video
cap = cv2.VideoCapture(video_path)

# Read everyframe from video
while True:
    ret, frame = cap.read()
    
    if not ret:
        continue
    
    # Model detect
    results = model(frame)
    
    detect = []
    
    for detect_object in results.pred[0]:
        label, confidence, bbox = detect_object[5], detect_object[4], detect_object[:4]
        x1, y1, x2, y2 = map(int, bbox)
        class_id = int(label)
        
        if tracking_class is None:
            if confidence < conf_threshold:
                continue
            else:
                if class_id != tracking_class or confidence < conf_threshold:
                    continue
        
        detect.append([ [x1, y1, x2-x1, y2 - y1], confidence, class_id])  
        
    # Update, assign Id
    tracks = tracker.update_tracks(detect, frame=frame)
    # Draw 
    for track in tracks:
        if track.is_confirmed():
            track_id = track.track_id
            
            # Take position
            ltrb = track.to_ltrb()
            class_id = track.get_det_class()
            x1, y1, x2, y2 = map(int, ltrb)
            color = colors[class_id]
            B, G, R = map(int, color)
            
            label = "{}-{}".format(class_names[class_id], track_id)
            
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), (B, G, R), 2)
            cv2.rectangle(frame, (x1 - 1, y1 - 20), (x1 + len(label) * 12, y1) ,(B, G, R), -1)
            cv2.putText(frame, label, (x1 + 5, y1 -8 ), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 0.5, (255, 255, 255), 2)
    # Show
    cv2.imshow("OT", frame)    
    if cv2.waitKey(1) == ord("q"):
        break
    
cap.release()
cv2.destroyAllWindows()
       