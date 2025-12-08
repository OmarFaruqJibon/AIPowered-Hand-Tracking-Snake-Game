# hand_tracker.py
import cv2
from cvzone.HandTrackingModule import HandDetector
import time

CAM_W, CAM_H = 640, 480

class HandTracker:
    def __init__(self, maxHands=1, detectionCon=0.6):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
        self.detector = HandDetector(maxHands=maxHands, detectionCon=detectionCon)
        self.last_index_pos = None

        # gesture debounce
        self._last_gesture_time = 0
        self._gesture_cooldown = 0.6  # seconds

    def read_frame(self):
        success, frame = self.cap.read()
        if not success:
            return None, None
        frame = cv2.flip(frame, 1)
        hands, img = self.detector.findHands(frame, flipType=False, draw=False)
        return frame, hands

    def get_index_and_fingers(self, hands):

        if not hands:
            return None, None
        hand = hands[0]
        lmList = hand["lmList"]  # 21 points
        ix, iy = int(lmList[8][0]), int(lmList[8][1])  # index fingertip
        self.last_index_pos = (ix, iy)

        # cvzone HandDetector has fingersUp() method
        try:
            fingers = self.detector.fingersUp(hand)
            fingers_count = sum(fingers)
        except Exception:
            # fallback: unknown -> None
            fingers_count = None

        return (ix, iy), fingers_count

    def detect_pause_toggle_gesture(self, hands):
        frame, hands_local = None, hands
        _, fingers = self.get_index_and_fingers(hands_local)
        now = time.time()
        if fingers is None:
            return None

        if now - self._last_gesture_time < self._gesture_cooldown:
            return None

        if fingers == 0:
            self._last_gesture_time = now
            return "toggle"
        if fingers >= 2:
            self._last_gesture_time = now
            return "resume"
        return None

    def release(self):
        self.cap.release()
