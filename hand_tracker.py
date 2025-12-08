import cv2
from cvzone.HandTrackingModule import HandDetector

CAM_W, CAM_H = 640, 480
INPUT_COOLDOWN_FRAMES = 5

class HandTracker:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)

        self.detector = HandDetector(maxHands=1, detectionCon=0.6)
        self.cooldown = 0
        self.last_index_pos = None

    def read_frame(self):
        success, frame = self.cap.read()
        if not success:
            return None, None, None

        frame = cv2.flip(frame, 1)
        hands, img = self.detector.findHands(frame, flipType=False, draw=False)

        return frame, hands, img

    def get_direction(self, hands):
        """Return direction (-1,0),(1,0),(0,-1),(0,1) or None."""
        if not hands:
            return None, None

        hand = hands[0]
        lmList = hand["lmList"]
        ix, iy = int(lmList[8][0]), int(lmList[8][1])

        self.last_index_pos = (ix, iy)

        left_th = CAM_W * 0.35
        right_th = CAM_W * 0.65
        top_th = CAM_H * 0.35
        bottom_th = CAM_H * 0.65

        if ix < left_th:
            return (-1, 0), (ix, iy)
        if ix > right_th:
            return (1, 0), (ix, iy)
        if iy < top_th:
            return (0, -1), (ix, iy)
        if iy > bottom_th:
            return (0, 1), (ix, iy)

        return None, (ix, iy)

    def release(self):
        self.cap.release()
