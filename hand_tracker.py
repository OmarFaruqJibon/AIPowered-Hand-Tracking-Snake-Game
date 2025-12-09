# hand_tracker.py
import cv2
import mediapipe as mp
import threading
import time

CAM_W, CAM_H = 640, 480

class HandTracker:
    def __init__(self, maxHands=1, detectionCon=0.7, smoothing_alpha=0.4):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=maxHands,
            min_detection_confidence=detectionCon,
            min_tracking_confidence=0.7
        )

        self.frame = None
        self.hands_data = None
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self.update_loop, daemon=True)
        self.thread.start()

        self.smooth_index_pos = None
        self.alpha = smoothing_alpha
        self.last_index_pos = None
        self.prev_index_pos = None

    def update_loop(self):
        while self.running:
            success, frame = self.cap.read()
            if not success:
                continue
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)

            hands_list = []
            if results.multi_hand_landmarks:
                for handLms in results.multi_hand_landmarks:
                    lmList = [(int(lm.x * CAM_W), int(lm.y * CAM_H)) for lm in handLms.landmark]
                    hands_list.append({"lmList": lmList})

            with self.lock:
                self.frame = frame.copy()
                self.hands_data = hands_list

    def read_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None, self.hands_data.copy() if self.hands_data is not None else []

    def get_index_and_fingers(self, hands):
        if not hands:
            return None, None

        hand = hands[0]
        lmList = hand["lmList"]
        ix, iy = lmList[8]  # Index fingertip

        # Improved smoothing with deadzone
        if self.smooth_index_pos is None:
            self.smooth_index_pos = (ix, iy)
        else:
            sx, sy = self.smooth_index_pos
            if abs(ix - sx) > 5 or abs(iy - sy) > 5:
                sx = self.alpha * ix + (1 - self.alpha) * sx
                sy = self.alpha * iy + (1 - self.alpha) * sy
                self.smooth_index_pos = (sx, sy)

        # Finger up detection: tip higher than PIP joint
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        fingers = []
        for tip, pip in zip(tips, pips):
            if lmList[tip][1] < lmList[pip][1] - 5:  # stricter
                fingers.append(1)
            else:
                fingers.append(0)
        fingers_count = sum(fingers)

        return (int(self.smooth_index_pos[0]), int(self.smooth_index_pos[1])), fingers_count

    def release(self):
        self.running = False
        self.thread.join()
        self.cap.release()
        cv2.destroyAllWindows()