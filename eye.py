import cv2
import mediapipe as mp
import time
import math
from collections import deque
from datetime import datetime
import csv

# Optional TTS
try:
    import pyttsx3
    tts_engine = pyttsx3.init()
    tts_available = True
except Exception:
    tts_engine = None
    tts_available = False

# -------------------------
# MediaPipe / OpenCV Setup
# -------------------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Finger landmark indices
finger_tips = [8, 12, 16, 20]
thumb_tip = 4

# -------------------------
# Recognition mapping
# -------------------------
def recognize_letter(fingers):
    mapping = {
        (0,0,0,0,0): "A", (1,1,1,1,1): "B", (1,0,0,0,0): "C", (1,1,0,0,0): "D",
        (1,1,1,0,0): "E", (1,1,1,1,0): "F", (0,0,0,0,1): "G", (0,0,0,1,1): "H",
        (0,0,1,1,1): "I", (0,1,1,1,1): "J", (1,0,0,0,1): "K", (1,0,0,1,1): "L",
        (1,0,1,1,1): "M", (0,0,1,0,1): "N", (1,1,0,0,1): "O", (1,1,0,1,1): "P",
        (1,1,1,0,1): "Q", (0,1,0,0,0): "R", (0,1,0,1,1): "S", (0,0,0,1,0): "T",
        (0,1,0,1,0): "U", (1,0,1,0,0): "V", (1,0,1,0,1): "W", (1,0,0,1,0): "X",
        (0,1,0,0,1): "Y", (0,1,1,0,1): "Z"
    }
    return mapping.get(tuple(fingers), "?")

def rainbow_color(t, speed=0.6):
    r = int((math.sin(speed * t + 0) + 1) * 127.5)
    g = int((math.sin(speed * t + 2) + 1) * 127.5)
    b = int((math.sin(speed * t + 4) + 1) * 127.5)
    return (b, g, r)

# -------------------------
# State Variables
# -------------------------
sentence = ""
last_added_time = 0.0
letter_delay = 3.0
current_letter = ""
history = deque()
recent_detections = deque(maxlen=8)
consensus_threshold = 3
smoothing_window = recent_detections.maxlen
tts_enabled = False and tts_available
auto_clear_seconds = 40
last_activity_time = time.time()
log_rows = []
prev_frame_time = 0
fps = 0.0

# -------------------------
# Helper Functions
# -------------------------
def try_speak(text):
    if not tts_available or not tts_enabled:
        return
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception:
        pass

def save_sentence_file(sentence_text):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sentence_{ts}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(sentence_text)
    print(f"Saved sentence to {filename}")

def save_csv_log():
    if not log_rows:
        print("No log data to save.")
        return
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"asl_log_{ts}.csv"
    try:
        with open(filename, "w", newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["timestamp_iso", "letter"])
            writer.writerows(log_rows)
        print(f"Saved CSV log to {filename}")
    except Exception as e:
        print("Error saving CSV:", e)

# -------------------------
# Main Loop
# -------------------------
while True:
    success, frame = cap.read()
    if not success:
        print("Unable to read from webcam.")
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    cur_time = time.time()
    if prev_frame_time:
        fps = 1.0 / (cur_time - prev_frame_time) if (cur_time - prev_frame_time) > 0 else 0.0
    prev_frame_time = cur_time

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    detected_letter = ""
    if result.multi_hand_landmarks:
        for handLms in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)
            lm_list = [(id, int(lm.x * w), int(lm.y * h)) for id, lm in enumerate(handLms.landmark)]

            if lm_list:
                fingers = []
                fingers.append(1 if lm_list[thumb_tip][1] > lm_list[thumb_tip - 1][1] else 0)
                for tip in finger_tips:
                    fingers.append(1 if lm_list[tip][2] < lm_list[tip - 2][2] else 0)

                detected_letter = recognize_letter(fingers)
                recent_detections.appendleft(detected_letter)
    else:
        recent_detections.appendleft("?")

    def consensus_from_buffer(buf, threshold):
        counts = {}
        for ch in buf:
            if ch in ("?", ""):
                continue
            counts[ch] = counts.get(ch, 0) + 1
        if not counts:
            return None, 0
        return max(counts.items(), key=lambda x: x[1])

    consensus_letter, consensus_count = consensus_from_buffer(list(recent_detections), consensus_threshold)

    time_since_added = time.time() - last_added_time if last_added_time else float('inf')
    readiness = min(1.0, time_since_added / letter_delay) if letter_delay > 0 else 1.0

    if consensus_letter and consensus_count >= consensus_threshold:
        if (time.time() - last_added_time) > letter_delay and consensus_letter != current_letter:
            sentence += consensus_letter
            history.appendleft(consensus_letter)
            current_letter = consensus_letter
            last_added_time = time.time()
            last_activity_time = time.time()
            log_rows.append((datetime.now().isoformat(), consensus_letter))
            if tts_enabled:
                try_speak(consensus_letter)

    if sentence and (time.time() - last_activity_time) > auto_clear_seconds:
        sentence = ""
        current_letter = ""
        history.clear()
        recent_detections.clear()
        last_added_time = 0
        print("Auto-cleared sentence due to inactivity.")

    # UI Drawing
    t = time.time()
    col = rainbow_color(t)
    display_letter = consensus_letter if consensus_letter else (detected_letter if detected_letter else "?")
    cv2.putText(frame, f"Sign: {display_letter}", (30, 70), cv2.FONT_HERSHEY_DUPLEX, 2.0, col, 3)

    # Readiness Bar
    cv2.rectangle(frame, (28, 108), (332, 132), (50, 50, 50), -1)
    fill_w = int(300 * readiness)
    cv2.rectangle(frame, (30, 110), (30 + fill_w, 128), (0, 180, 255), -1)

    # Sentence
    base_x, base_y = 30, 160
    for i, ch in enumerate(sentence):
        cv2.putText(frame, ch, (base_x + i * 28, base_y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, rainbow_color(t + i * 0.3), 2)

    cv2.imshow("ASL to Sentence", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord(' '):
        if not sentence.endswith(" "):  # avoid duplicate spaces
            sentence += " "
        last_activity_time = time.time()
    elif key == ord('c') or key == 8:
        if sentence:
            sentence = sentence[:-1]
        current_letter = ""
        last_added_time = 0
        last_activity_time = time.time()
    elif key == ord('r'):
        sentence = ""
        current_letter = ""
        history.clear()
        recent_detections.clear()
        last_added_time = 0
        last_activity_time = time.time()
    elif key == ord('s'):
        save_sentence_file(sentence)
    elif key == ord('S'):
        save_csv_log()
    elif key == ord('+') or key == ord('='):
        letter_delay = max(0.5, letter_delay - 0.5)
        print(f"Letter delay set to {letter_delay:.1f}s")
    elif key == ord('-') or key == ord('_'):
        letter_delay += 0.5
        print(f"Letter delay set to {letter_delay:.1f}s")
    elif key == ord('v'):
        if not tts_available:
            print("TTS unavailable.")
        else:
            tts_enabled = not tts_enabled
            print("TTS", "enabled" if tts_enabled else "disabled")
    elif key == 27:
        break

# Cleanup
if log_rows:
    save_csv_log()
cap.release()
cv2.destroyAllWindows()
hands.close()
if tts_engine:
    tts_engine.stop()
print("Exited cleanly.")
