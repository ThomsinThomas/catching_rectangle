import sys
import random
import math
import os
import time
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QStackedWidget,
    QFrame,
)
from PyQt6.QtCore import (
    Qt,
    QTimer,
    pyqtSignal,
    QRect,
    QPoint,
    QByteArray,
    QIODevice,
    QBuffer,
)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QFont, QPen
from PyQt6.QtMultimedia import QAudioFormat, QAudioSink


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# --- UI CONSTANTS ---
PURPLE = QColor(108, 92, 231)
THEME_BLUE = "#00a8ff"
DARK_RED = "#e84118"
BRIGHT_RED = "#ff4d4d"
LIGHT_OVERLAY = "rgba(255, 255, 255, 190)"
DARK_OVERLAY = "rgba(45, 52, 54, 220)"
HEADING_YELLOW = "#fabe42"
BEIGE_BG = "#f5f5dc"
GREEN_DOT = QColor(50, 205, 50)  # Lime green for both hands

GRADIENT_PROGRESS_STYLE = f"""
    QProgressBar {{
        border: 2px solid rgba(255, 255, 255, 50);
        background-color: rgba(0, 0, 0, 100);
        border-radius: 4px;
    }}
    QProgressBar::chunk {{
        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, 
            stop:0 {DARK_RED}, stop:1 {THEME_BLUE});
    }}
"""


# --- AUDIO GENERATOR ---
class SoundGenerator:
    def __init__(self):
        self.format = QAudioFormat()
        self.format.setSampleRate(44100)
        self.format.setChannelCount(1)
        self.format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        self.audio_sink = QAudioSink(self.format)
        self.buffer = QBuffer()

    def play_tone(self, frequency, duration_ms, volume=0.3):
        self.audio_sink.stop()
        sample_rate = 44100
        num_samples = int(sample_rate * (duration_ms / 1000))
        data = QByteArray()
        for i in range(num_samples):
            t = i / sample_rate
            value = int(32767 * volume * math.sin(2 * math.pi * frequency * t))
            data.append(value.to_bytes(2, byteorder="little", signed=True))
        if self.buffer.isOpen():
            self.buffer.close()
        self.buffer.setData(data)
        self.buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        self.audio_sink.start(self.buffer)


class GameRectangle:
    def __init__(self, screen_w, screen_h, speed, size, head_y, hip_y, spawn_from_left=True):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.size = size
        self.spawn_from_left = spawn_from_left
        
        # Set initial x position based on spawn side
        if spawn_from_left:
            self.x = -self.size  # Start from left
        else:
            self.x = screen_w  # Start from right
        
        # Use calibrated head and hip positions for vertical spawn range
        margin = 110
        # Convert normalized coordinates to screen pixels
        head_pixel = int(head_y * screen_h)
        hip_pixel = int(hip_y * screen_h)
        
        # Ensure min_y is the higher (smaller value) and max_y is the lower (larger value)
        min_y = min(head_pixel, hip_pixel)
        max_y = max(head_pixel, hip_pixel)
        
        # Add some vertical variance (20% of the range)
        range_height = max_y - min_y
        variance = int(range_height * 0.2)
        
        # Apply margins to keep rectangles fully on screen
        safe_min = margin
        safe_max = screen_h - margin - self.size
        
        # Calculate final y position within expanded region
        self.y = random.randint(
            max(safe_min, min_y - variance),
            min(safe_max, max_y + variance)
        )
        
        # Speed is positive for left-to-right, negative for right-to-left
        self.speed = speed if spawn_from_left else -speed
        self.color = QColor(232, 65, 24)  # Red initially
        self.is_blue = False

    def move(self):
        self.x += self.speed
        
        # Change color based on crossing the center (when the trailing edge crosses the center)
        if self.spawn_from_left and self.x > self.screen_w // 2:
            self.color = QColor(0, 120, 255)
            self.is_blue = True
        elif not self.spawn_from_left and (self.x + self.size) < self.screen_w // 2:
            self.color = QColor(0, 120, 255)
            self.is_blue = True


class SplashPage(QWidget):
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.splash_bg = QLabel(self)
        self.splash_bg.setPixmap(QPixmap(resource_path("splash_bg.jpg")))
        self.splash_bg.setScaledContents(True)
        self.progress = QProgressBar(self)
        self.progress.setFixedSize(600, 30)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(GRADIENT_PROGRESS_STYLE)
        layout.addStretch()
        layout.addWidget(self.progress, 0, Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 150)
        self.val = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(20)

    def tick(self):
        self.val += 1
        self.progress.setValue(self.val)
        if self.val >= 100:
            self.timer.stop()
            self.finished.emit()

    def resizeEvent(self, event):
        self.splash_bg.resize(self.size())


class SetupPage(QWidget):
    start_setup = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration = 2
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        top = QHBoxLayout()
        top.addStretch()
        quit_btn = QPushButton(" QUIT")
        quit_btn.setFixedSize(140, 60)
        quit_btn.setStyleSheet(
            f"QPushButton {{ background-color: {DARK_RED}; color: white; border-radius: 12px; font-weight: bold; font-size: 18px; border: 2px solid white; }}"
        )
        quit_btn.clicked.connect(QApplication.instance().quit)
        top.addWidget(quit_btn)
        layout.addLayout(top)
        main_box = QFrame()
        main_box.setStyleSheet(
            f"background-color: {LIGHT_OVERLAY}; border-radius: 30px; border: 3px solid white;"
        )
        main_lay = QVBoxLayout(main_box)
        main_lay.setContentsMargins(50, 50, 50, 50)
        title = QLabel(" DURATION ")
        title.setStyleSheet(
            f"font-size: 32px; font-weight: 1000; color: #2d3436; background-color: {HEADING_YELLOW}; border-radius: 10px; padding: 5px 20px;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ctrl = QHBoxLayout()
        m_btn = self.create_nav_btn("-")
        p_btn = self.create_nav_btn("+")
        self.lbl_time = QLabel("02:00")
        self.lbl_time.setStyleSheet(
            f"font-size: 80px; font-weight: 1000; color: #2d3436; background-color: {BEIGE_BG}; padding: 15px 50px; border-radius: 15px; border: 2px solid #dcdde1;"
        )
        ctrl.addStretch()
        ctrl.addWidget(m_btn)
        ctrl.addWidget(self.lbl_time)
        ctrl.addWidget(p_btn)
        ctrl.addStretch()
        main_lay.addWidget(title, 0, Qt.AlignmentFlag.AlignCenter)
        main_lay.addLayout(ctrl)
        diff_t = QLabel(" SELECT DIFFICULTY ")
        diff_t.setStyleSheet(
            f"font-size: 28px; font-weight: 1000; color: #2d3436; background-color: {HEADING_YELLOW}; border-radius: 10px; padding: 5px 20px; margin-top: 30px;"
        )
        diff_t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_lay.addWidget(diff_t, 0, Qt.AlignmentFlag.AlignCenter)
        d_lay = QHBoxLayout()
        self.btn_e = self.create_diff("EASY", THEME_BLUE)
        self.btn_m = self.create_diff("MEDIUM", "#f1c40f")
        self.btn_h = self.create_diff("HARD", DARK_RED)
        d_lay.addWidget(self.btn_e)
        d_lay.addWidget(self.btn_m)
        d_lay.addWidget(self.btn_h)
        main_lay.addLayout(d_lay)
        layout.addStretch()
        layout.addWidget(main_box, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        m_btn.clicked.connect(lambda: [self.window().play_click(), self.upd_dur(-1)])
        p_btn.clicked.connect(lambda: [self.window().play_click(), self.upd_dur(1)])
        self.btn_e.clicked.connect(
            lambda: [
                self.window().play_click(),
                self.start_setup.emit(self.duration, "EASY"),
            ]
        )
        self.btn_m.clicked.connect(
            lambda: [
                self.window().play_click(),
                self.start_setup.emit(self.duration, "MEDIUM"),
            ]
        )
        self.btn_h.clicked.connect(
            lambda: [
                self.window().play_click(),
                self.start_setup.emit(self.duration, "HARD"),
            ]
        )

    def create_nav_btn(self, t):
        b = QPushButton(t)
        b.setFixedSize(80, 80)
        b.setStyleSheet(
            f"QPushButton {{ border: 4px solid {HEADING_YELLOW}; background: white; font-size: 40px; color: {HEADING_YELLOW}; font-weight: bold; border-radius: 15px; }} QPushButton:hover {{ background: {HEADING_YELLOW}; color: white; }}"
        )
        return b

    def create_diff(self, t, c):
        b = QPushButton(t)
        b.setFixedSize(200, 80)
        b.setStyleSheet(
            f"QPushButton {{ background-color: white; color: {HEADING_YELLOW}; border-radius: 20px; font-weight: 1000; font-size: 20px; border: 4px solid {HEADING_YELLOW}; }} QPushButton:hover {{ background-color: {c}; color: white; border: 4px solid white; }}"
        )
        return b

    def upd_dur(self, v):
        self.duration = max(2, min(20, self.duration + v))  # Reduced max to 20 minutes
        self.lbl_time.setText(f"{self.duration:02d}:00")


class InstructionPage(QWidget):
    start_triggered = pyqtSignal()
    back_triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.count = 30
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        nav = QHBoxLayout()
        b_btn = QPushButton(" BACK")
        b_btn.setFixedSize(140, 60)
        b_btn.setStyleSheet(
            f"QPushButton {{ background-color: {THEME_BLUE}; color: white; border-radius: 12px; font-weight: bold; font-size: 18px; border: 2px solid white; }}"
        )
        b_btn.clicked.connect(
            lambda: [self.window().play_click(), self.back_triggered.emit()]
        )
        q_btn = QPushButton(" QUIT")
        q_btn.setFixedSize(140, 60)
        q_btn.setStyleSheet(
            f"QPushButton {{ background-color: {DARK_RED}; color: white; border-radius: 12px; font-weight: bold; font-size: 18px; border: 2px solid white; }}"
        )
        q_btn.clicked.connect(QApplication.instance().quit)
        nav.addWidget(b_btn)
        nav.addStretch()
        nav.addWidget(q_btn)
        layout.addLayout(nav)
        
        # Create a container frame that will scale with the window
        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {DARK_OVERLAY}; border-radius: 40px; border: 3px solid {THEME_BLUE};"
        )
        f_lay = QVBoxLayout(frame)
        
        # Use percentage-based margins for scaling
        margins = int(min(self.width(), self.height()) * 0.30)
        f_lay.setContentsMargins(margins, margins, margins, margins)
        
        title = QLabel("HOW TO PLAY")
        title.setStyleSheet(
            f"font-size: 48px; color: {THEME_BLUE}; font-weight: 1000; margin-bottom: 25px; background: transparent; border: none;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f_lay.addWidget(title)
        
        instr_text = (
            "• Red rectangles cannot be captured.\n\n"
            "• Wait for rectangles to turn BLUE pass the center.\n\n"
            "• Rectangles spawn from BOTH sides alternately!\n\n"
            "• BOTH hands are active, use either hand to catch!\n"
        )
        lbl = QLabel(instr_text)
        lbl.setStyleSheet(
            "font-size: 26px; color: #f5f6fa; font-family: 'Segoe UI'; background: transparent; border: none;"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lbl.setWordWrap(True)  # Enable word wrap for better scaling
        f_lay.addWidget(lbl)
        
        self.lbl_t = QLabel(f"Starting in {self.count}s...")
        self.lbl_t.setStyleSheet(
            "color: #b2bec3; font-size: 20px; margin-top: 30px; background: transparent; border: none;"
        )
        self.lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        s_btn = QPushButton("START CALIBRATION")
        # Use percentage-based sizing for button
        btn_width = int(min(self.width(), self.height()) * 0.3)
        btn_height = int(btn_width * 0.2)
        s_btn.setFixedSize(max(300, btn_width), max(60, btn_height))
        s_btn.setStyleSheet(
            f"QPushButton {{ background-color: {THEME_BLUE}; color: white; border-radius: 25px; font-weight: bold; font-size: 26px; border: 3px solid white; }} QPushButton:hover {{ background-color: white; color: {THEME_BLUE}; }}"
        )
        s_btn.clicked.connect(lambda: [self.window().play_click(), self.go()])
        
        f_lay.addWidget(self.lbl_t)
        f_lay.addWidget(s_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Add stretch to center the frame vertically
        layout.addStretch()
        layout.addWidget(frame, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)

    def resizeEvent(self, event):
        # Update frame margins and button size when window is resized
        if hasattr(self, 'layout') and self.layout().count() > 1:
            frame = self.layout().itemAt(1).widget()
            if frame:
                margins = int(min(self.width(), self.height()) * 0.05)
                frame.layout().setContentsMargins(margins, margins, margins, margins)
                
                # Update button size
                s_btn = frame.layout().itemAt(3).widget()
                btn_width = int(min(self.width(), self.height()) * 0.3)
                btn_height = int(btn_width * 0.2)
                s_btn.setFixedSize(max(300, btn_width), max(60, btn_height))
        
        super().resizeEvent(event)

    def start_t(self):
        self.count = 30
        self.timer.start(1000)

    def tick(self):
        self.count -= 1
        self.lbl_t.setText(f"Starting in {self.count}s...")
        if self.count <= 0:
            self.go()

    def go(self):
        self.timer.stop()
        self.start_triggered.emit()


_WORKING_CAM_INDEX = None
def get_working_camera_index():
    import cv2
    global _WORKING_CAM_INDEX
    if _WORKING_CAM_INDEX is not None:
        return _WORKING_CAM_INDEX
    for index in range(5):
        cap = cv2.VideoCapture(index)
        if cap is not None and cap.isOpened():
            ret, frame = cap.read()
            if ret:
                cap.release()
                _WORKING_CAM_INDEX = index
                return index
            cap.release()
    _WORKING_CAM_INDEX = 0
    return 0


class CalibrationPage(QWidget):
    complete = pyqtSignal(float, float, float)  # Emits head_y, hip_y, and swap_dist
    back = pyqtSignal()  # Signal for going back

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: black;")  # Black background as fallback
        
        # Main layout without any containers - will paint video directly
        self.video_label = QLabel(self)
        self.video_label.setGeometry(self.rect())
        self.video_label.setScaledContents(True)
        
        # Create overlay widgets with scalable sizes
        self.b_btn = QPushButton(" BACK", self)
        self.b_btn.setFixedSize(140, 60)  # Fixed minimum size
        self.b_btn.setStyleSheet(
            f"QPushButton {{ background-color: {THEME_BLUE}; color: white; border-radius: 12px; font-weight: bold; font-size: 18px; border: 2px solid white; }}"
        )
        self.b_btn.clicked.connect(
            lambda: [self.window().play_click(), self.close_cam_back()]
        )
        
        self.q_btn = QPushButton(" QUIT", self)
        self.q_btn.setFixedSize(140, 60)  # Fixed minimum size
        self.q_btn.setStyleSheet(
            f"QPushButton {{ background-color: {DARK_RED}; color: white; border-radius: 12px; font-weight: bold; font-size: 18px; border: 2px solid white; }}"
        )
        self.q_btn.clicked.connect(QApplication.instance().quit)
        
        # Countdown label - scalable
        self.countdown_label = QLabel("3", self)
        self.countdown_label.setStyleSheet("font-size: 72px; color: white; font-weight: 1000; background-color: rgba(0,0,0,100); border-radius: 20px; padding: 20px;")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.hide()
        
        # Progress bar - scalable width
        self.bar = QProgressBar(self)
        self.bar.setFixedHeight(30)
        self.bar.setTextVisible(False)
        self.bar.setStyleSheet(GRADIENT_PROGRESS_STYLE)
        
        # Instruction label - scalable
        self.instruction_label = QLabel("Raise and show both hands to the camera.", self)
        self.instruction_label.setStyleSheet("color: white; font-size: 18px; background-color: rgba(0,0,0,100); padding: 10px; border-radius: 10px;")
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_label.setWordWrap(True)
        
        # Position status label
        self.position_status = QLabel("Please stand inside the rectangle", self)
        self.position_status.setStyleSheet("color: yellow; font-size: 20px; background-color: rgba(0,0,0,100); padding: 10px; border-radius: 10px; font-weight: bold;")
        self.position_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position_status.hide()
        
        self.mp_holistic = None
        self.holistic = None
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.upd)
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.countdown_tick)
        self.countdown_value = 3
        self.counter = 0
        self.head_y_sum = 0
        self.hip_y_sum = 0
        self.dist_sum = 0
        self.position_ok = False  # Flag to track if player is properly positioned

    def resizeEvent(self, event):
        self.video_label.setGeometry(self.rect())
        
        # Position UI elements absolutely with scaling
        # Buttons at top left and right (fixed positions)
        self.b_btn.move(40, 40)
        self.q_btn.move(self.width() - 180, 40)
        
        # Position status label at top center
        status_width = min(400, int(self.width() * 0.3))
        status_height = 50
        self.position_status.setGeometry(
            self.width() // 2 - status_width // 2, 
            120, 
            status_width, 
            status_height
        )
        
        # Countdown in center (scaled size)
        countdown_size = min(150, int(min(self.width(), self.height()) * 0.15))
        self.countdown_label.setGeometry(
            self.width() // 2 - countdown_size // 2, 
            self.height() // 2 - countdown_size // 2, 
            countdown_size, 
            countdown_size
        )
        
        # Progress bar at bottom (scaled width)
        bar_width = min(600, int(self.width() * 0.5))
        self.bar.setFixedWidth(bar_width)
        self.bar.move(self.width() // 2 - bar_width // 2, self.height() - 150)
        
        # Instruction label at bottom (scaled width)
        label_width = min(800, int(self.width() * 0.7))
        label_height = 50
        self.instruction_label.setGeometry(
            self.width() // 2 - label_width // 2, 
            self.height() - 220, 
            label_width, 
            label_height
        )
        
        super().resizeEvent(event)

    def start_c(self):
        import cv2
        import mediapipe as mp
        if self.mp_holistic is None:
            self.mp_holistic = mp.solutions.holistic
            self.holistic = self.mp_holistic.Holistic(
                min_detection_confidence=0.7, min_tracking_confidence=0.7
            )
            
        self.cap = cv2.VideoCapture(get_working_camera_index())
        self.counter = 0
        self.head_y_sum = 0
        self.hip_y_sum = 0
        self.dist_sum = 0
        self.position_ok = False
        self.bar.setValue(0)
        
        # Show position status
        self.position_status.show()
        self.position_status.setText("Please stand inside the rectangle")
        self.position_status.setStyleSheet("color: yellow; font-size: 20px; background-color: rgba(0,0,0,100); padding: 10px; border-radius: 10px; font-weight: bold;")
        
        # Hide instruction during initial positioning
        self.instruction_label.hide()
        self.timer.start(30)

    def countdown_tick(self):
        self.countdown_value -= 1
        if self.countdown_value > 0:
            self.countdown_label.setText(str(self.countdown_value))
            self.window().play_click()  # Play click sound for each count
        else:
            self.countdown_label.hide()
            self.countdown_timer.stop()
            self.instruction_label.show()

    def close_cam_back(self):
        self.timer.stop()
        self.countdown_timer.stop()
        if self.cap:
            self.cap.release()
        self.back.emit()  # Emit the back signal

    def upd(self):
        import cv2
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.holistic.process(rgb)
        
        # Define the target rectangle in the middle of the screen
        rect_width = int(w * 0.4)  # 40% of screen width
        rect_height = int(h * 0.8)  # 80% of screen height
        rect_x = w // 2 - rect_width // 2
        rect_y = h // 2 - rect_height // 2
        
        # Draw the target rectangle on frame
        cv2.rectangle(frame, (rect_x, rect_y), (rect_x + rect_width, rect_y + rect_height), 
                     (255, 255, 255), 3)  # White rectangle
        
        # Add "STAND HERE" text above rectangle
        cv2.putText(frame, "STAND HERE", (rect_x + 20, rect_y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Check if player is properly positioned (only if pose landmarks are detected)
        if res.pose_landmarks:
            lm = res.pose_landmarks.landmark
            
            # Get head position (nose)
            nose = lm[self.mp_holistic.PoseLandmark.NOSE]
            nose_x, nose_y = int(nose.x * w), int(nose.y * h)
            
            # Get hip position (average of left and right hip)
            left_hip = lm[self.mp_holistic.PoseLandmark.LEFT_HIP]
            right_hip = lm[self.mp_holistic.PoseLandmark.RIGHT_HIP]
            hip_x = int(((left_hip.x + right_hip.x) / 2) * w)
            hip_y = int(((left_hip.y + right_hip.y) / 2) * h)
            
            # Draw head point and hip line
            cv2.circle(frame, (nose_x, nose_y), 10, (128, 0, 128), -1)  # Purple for head
            cv2.line(frame, (rect_x, hip_y), (rect_x + rect_width, hip_y), (0, 255, 0), 4)  # Green line for hip
            
            # Check if both head and hip are inside the rectangle
            head_inside = (rect_x <= nose_x <= rect_x + rect_width and 
                          rect_y <= nose_y <= rect_y + rect_height)
            hip_inside = (rect_x <= hip_x <= rect_x + rect_width and 
                         rect_y <= hip_y <= rect_y + rect_height)
            
            # Update position status
            if head_inside and hip_inside:
                if not self.position_ok:
                    self.position_ok = True
                    self.position_status.setText("Position OK! Starting countdown...")
                    self.position_status.setStyleSheet("color: lightgreen; font-size: 20px; background-color: rgba(0,0,0,100); padding: 10px; border-radius: 10px; font-weight: bold;")
                    
                    # Start countdown
                    self.countdown_value = 3
                    self.countdown_label.setText("3")
                    self.countdown_label.show()
                    self.countdown_timer.start(1000)
                    
                    # Hide position status after countdown starts
                    self.position_status.hide()
            else:
                self.position_ok = False
                self.position_status.setText("Please stand inside the rectangle")
                self.position_status.setStyleSheet("color: yellow; font-size: 20px; background-color: rgba(0,0,0,100); padding: 10px; border-radius: 10px; font-weight: bold;")
            
            # Only collect calibration data if position is OK and countdown is complete
            if self.position_ok and self.countdown_value <= 0:
                # Get head position (nose)
                self.head_y_sum += nose.y
                
                # Get hip position
                hip_y = (left_hip.y + right_hip.y) / 2
                self.hip_y_sum += hip_y
                
                # Removed the rectangle connecting head and hip
                
                if res.left_hand_landmarks and res.right_hand_landmarks:
                    l_wrist = res.left_hand_landmarks.landmark[0]
                    r_wrist = res.right_hand_landmarks.landmark[0]
                    dist = math.sqrt(
                        (l_wrist.x - r_wrist.x) ** 2 + (l_wrist.y - r_wrist.y) ** 2
                    )
                    self.dist_sum += dist
                    
                    # Draw hand points only (no text labels)
                    cv2.circle(frame, (int(l_wrist.x * w), int(l_wrist.y * h)), 8, (0, 255, 0), -1)
                    cv2.circle(frame, (int(r_wrist.x * w), int(r_wrist.y * h)), 8, (0, 255, 0), -1)
                
                self.counter += 1
                self.bar.setValue(self.counter)
        
        # Convert frame to QImage and display in video_label
        qimg = QImage(frame.data, w, h, w * 3, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(qimg)
        self.video_label.setPixmap(pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))
        
        if self.counter >= 100:
            self.timer.stop()
            if self.cap:
                self.cap.release()
            avg_dist = (self.dist_sum / self.counter) if self.counter > 0 else 0.15
            avg_head = self.head_y_sum / self.counter
            avg_hip = self.hip_y_sum / self.counter
            self.complete.emit(avg_head, avg_hip, avg_dist)


class GamePage(QWidget):
    finished = pyqtSignal(int, int)  # Emits left_score, right_score (no lives)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rects = []
        self.l_score = 0
        self.r_score = 0
        # No lives - game ends on timer only
        self.flash_timer = 0
        self.is_paused = False
        self.mp_holistic = None
        self.holistic = None
        self.cap = None
        self.current_frame = None
        self.left_cursor_pos = QPoint(0, 0)
        self.right_cursor_pos = QPoint(0, 0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.loop)
        self.spawn_t = QTimer()
        self.spawn_t.timeout.connect(self.spawn)
        self.session_t = QTimer()
        self.session_t.timeout.connect(self.tick_session)
        self.head_y = 0.3  # Default values
        self.hip_y = 0.7   # Default values
        self.speed = 5
        self.size = 60
        self.time_elapsed = 0
        self.duration_seconds = 0
        self.diff = ""
        self.border_pixmap = QPixmap(resource_path("game_bg.png"))
        self.btn_pause = QPushButton("PAUSE", self)
        self.btn_exit = QPushButton("EXIT", self)
        self.btn_pause.setStyleSheet(
            f"QPushButton {{ background-color: {THEME_BLUE}; color: white; border-radius: 12px; font-weight: bold; font-size: 18px; border: 2px solid white; }}"
        )
        self.btn_exit.setStyleSheet(
            f"QPushButton {{ background-color: {DARK_RED}; color: white; border-radius: 12px; font-weight: bold; font-size: 18px; border: 2px solid white; }}"
        )
        for b in [self.btn_pause, self.btn_exit]:
            b.setFixedSize(140, 60)
        self.btn_pause.clicked.connect(
            lambda: [self.window().play_click(), self.toggle_pause()]
        )
        self.btn_exit.clicked.connect(
            lambda: [self.window().play_click(), self.stop_and_finish()]
        )
        
        # Spawn side tracking - True for left, False for right
        self.next_spawn_from_left = True

    def resizeEvent(self, event):
        self.btn_exit.move(self.width() - 160, 20)
        self.btn_pause.move(self.width() - 320, 20)
        
        # Update rectangle positions if needed based on new screen size
        # This ensures rectangles spawn correctly after resize
        for rect in self.rects:
            rect.screen_w = self.width()
            rect.screen_h = self.height()
        
        super().resizeEvent(event)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.btn_pause.setText("RESUME" if self.is_paused else "PAUSE")

    def start(self, head_y, hip_y, d_swap, d_min, diff):
        self.head_y = head_y
        self.hip_y = hip_y
        self.l_score = 0
        self.r_score = 0
        self.rects = []
        self.time_elapsed = 0
        self.duration_seconds = d_min * 60
        self.flash_timer = 0
        self.is_paused = False
        self.btn_pause.setText("PAUSE")
        self.next_spawn_from_left = True  # Start with left spawn
        
        self.diff = diff
        if diff == "EASY":
            self.speed, self.size = 6, 110
            spawn_interval = 2000  # 2 seconds
        elif diff == "MEDIUM":
            self.speed, self.size = 10, 90
            spawn_interval = 1200  # 1.2 seconds
        else:  # HARD
            self.speed, self.size = 15, 75
            spawn_interval = 700   # 0.7 seconds
            
        import cv2
        import mediapipe as mp
        if self.mp_holistic is None:
            self.mp_holistic = mp.solutions.holistic
            self.holistic = self.mp_holistic.Holistic(
                min_detection_confidence=0.7, min_tracking_confidence=0.8
            )
            
        self.cap = cv2.VideoCapture(get_working_camera_index())
        self.timer.start(30)
        self.spawn_t.start(spawn_interval)
        self.session_t.start(1000)

    def spawn(self):
        if not self.is_paused:
            # Spawn from alternating sides using calibrated head and hip positions
            self.rects.append(
                GameRectangle(
                    self.width(), self.height(), self.speed, self.size, 
                    self.head_y, self.hip_y, self.next_spawn_from_left
                )
            )
            # Toggle for next spawn
            self.next_spawn_from_left = not self.next_spawn_from_left

    def tick_session(self):
        if not self.is_paused:
            self.time_elapsed += 1
            if self.time_elapsed >= self.duration_seconds:
                self.stop_and_finish()

    def stop_and_finish(self):
        self.timer.stop()
        self.spawn_t.stop()
        self.session_t.stop()
        if self.cap:
            self.cap.release()
        self.finished.emit(self.l_score, self.r_score)  # Emit only scores

    def loop(self):
        import cv2
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.holistic.process(rgb)
        self.current_frame = QImage(
            frame.data, w, h, w * 3, QImage.Format.Format_BGR888
        )
        
        # Track both hands independently
        hand_l = res.left_hand_landmarks
        hand_r = res.right_hand_landmarks
        
        top_offset = int(self.height() * 0.12)
        
        # Update left hand cursor (MediaPipe's left is user's right)
        if hand_l:
            tip_l = hand_l.landmark[8]  # Index finger tip
            target_x_l = int(tip_l.x * self.width())
            target_y_l = int(top_offset + (tip_l.y * (self.height() - top_offset)))
            self.right_cursor_pos = QPoint(  # MediaPipe left hand = user's right hand
                int(self.right_cursor_pos.x() * 0.3 + target_x_l * 0.7),
                int(self.right_cursor_pos.y() * 0.3 + target_y_l * 0.7),
            )
        
        # Update right hand cursor (MediaPipe's right is user's left)
        if hand_r:
            tip_r = hand_r.landmark[8]  # Index finger tip
            target_x_r = int(tip_r.x * self.width())
            target_y_r = int(top_offset + (tip_r.y * (self.height() - top_offset)))
            self.left_cursor_pos = QPoint(  # MediaPipe right hand = user's left hand
                int(self.left_cursor_pos.x() * 0.3 + target_x_r * 0.7),
                int(self.left_cursor_pos.y() * 0.3 + target_y_r * 0.7),
            )
        
        if not self.is_paused:
            if self.flash_timer > 0:
                self.flash_timer -= 1
            
            for r in self.rects[:]:
                r.move()
                
                # Check if caught by either hand
                caught = False
                
                # Check left hand (user's left)
                if hand_r and r.is_blue and QRect(r.x, r.y, r.size, r.size).contains(  # Using hand_r for left cursor
                    self.left_cursor_pos
                ):
                    self.l_score += 1
                    caught = True
                
                # Check right hand (user's right)
                if hand_l and r.is_blue and QRect(r.x, r.y, r.size, r.size).contains(  # Using hand_l for right cursor
                    self.right_cursor_pos
                ):
                    self.r_score += 1
                    caught = True
                
                if caught:
                    self.window().play_success()
                    self.rects.remove(r)
                
                # Remove rectangles that passed screen (no life penalty)
                elif (r.spawn_from_left and r.x > self.width()) or (not r.spawn_from_left and r.x + r.size < 0):
                    self.rects.remove(r)
        
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.current_frame:
            top_offset = int(self.height() * 0.12)
            p.drawImage(
                QRect(0, top_offset, self.width(), self.height() - top_offset),
                self.current_frame,
            )
            
            # Removed the dotted rectangle that was showing the spawn zone
            
        # Draw rectangles
        for r in self.rects:
            p.setBrush(r.color)
            p.setPen(QPen(Qt.GlobalColor.white, 2))
            p.drawRoundedRect(r.x, r.y, r.size, r.size, 15, 15)
        
        # Draw left hand cursor (user's left - GREEN DOT)
        if self.left_cursor_pos.x() > 0 or self.left_cursor_pos.y() > 0:
            p.setBrush(GREEN_DOT)
            p.setPen(QPen(Qt.GlobalColor.white, 3))
            p.drawEllipse(self.left_cursor_pos, 35, 35)
            p.setFont(QFont("Verdana", 12))
            p.setPen(Qt.GlobalColor.white)
            p.drawText(self.left_cursor_pos + QPoint(-20, -40), "LEFT")
        
        # Draw right hand cursor (user's right - GREEN DOT)
        if self.right_cursor_pos.x() > 0 or self.right_cursor_pos.y() > 0:
            p.setBrush(GREEN_DOT)  # Same green dot for both hands
            p.setPen(QPen(Qt.GlobalColor.white, 3))
            p.drawEllipse(self.right_cursor_pos, 35, 35)
            p.setFont(QFont("Verdana", 12))
            p.setPen(Qt.GlobalColor.white)
            p.drawText(self.right_cursor_pos + QPoint(-25, -40), "RIGHT")
        
        if not self.border_pixmap.isNull():
            p.drawPixmap(
                self.rect(),
                self.border_pixmap.scaled(
                    self.rect().size(),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ),
            )
        
        if self.flash_timer > 0:
            p.setBrush(QColor(255, 0, 0, 50))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRect(self.rect())
        
        HUD_BG, TEXT_COLOR = QColor("#fde8c9"), QColor("#2d3436")
        
        # Score display - made smaller since lives are removed
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(HUD_BG)
        p.drawRoundedRect(25, 25, 320, 60, 15, 15)
        p.setPen(QPen(TEXT_COLOR, 2))
        p.setFont(QFont("Verdana", 22, QFont.Weight.Bold))
        p.drawText(
            QRect(25, 25, 320, 60),
            Qt.AlignmentFlag.AlignCenter,
            f"L: {self.l_score} | R: {self.r_score}",
        )
        
        # Timer display
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(HUD_BG)
        p.drawRoundedRect(self.width() // 2 - 100, 25, 200, 60, 15, 15)
        m, s = divmod(self.time_elapsed, 60)
        p.setPen(TEXT_COLOR)
        p.setFont(QFont("Verdana", 28, QFont.Weight.ExtraBold))
        p.drawText(
            QRect(self.width() // 2 - 100, 25, 200, 60),
            Qt.AlignmentFlag.AlignCenter,
            f"{m:02d}:{s:02d}",
        )


class SummaryPage(QWidget):
    replay_triggered = pyqtSignal()
    menu_triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        top = QHBoxLayout()
        top.addStretch()
        quit_btn = QPushButton(" QUIT")
        quit_btn.setFixedSize(140, 60)
        quit_btn.setStyleSheet(
            f"QPushButton {{ background-color: {DARK_RED}; color: white; border-radius: 12px; font-weight: bold; font-size: 18px; border: 2px solid white; }}"
        )
        quit_btn.clicked.connect(QApplication.instance().quit)
        top.addWidget(quit_btn)
        layout.addLayout(top)
        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {DARK_OVERLAY}; border-radius: 40px; border: 3px solid {THEME_BLUE};"
        )
        f_lay = QVBoxLayout(frame)
        f_lay.setContentsMargins(70, 50, 70, 50)
        title = QLabel("GAME OVER")
        title.setStyleSheet(
            f"font-size: 44px; color: {THEME_BLUE}; font-weight: 1000; border: none; background: transparent;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f_lay.addWidget(title)
        self.res = QLabel()
        self.res.setStyleSheet(
            "font-size: 30px; font-weight: 300; color: #dfe6e9; margin: 20px; border: none; background: transparent; font-family: 'Segoe UI';"
        )
        self.res.setAlignment(Qt.AlignmentFlag.AlignLeft)
        f_lay.addWidget(self.res)
        self.btn_replay = QPushButton(" ↻ PLAY AGAIN")
        self.btn_menu = QPushButton(" 🏠 MAIN MENU")
        style = f"QPushButton {{ background-color: {PURPLE.name()}; color: white; border-radius: 20px; font-size: 24px; font-weight: bold; min-height: 80px; border: 2px solid white; }} QPushButton:hover {{ background-color: white; color: {PURPLE.name()}; }}"
        self.btn_replay.setStyleSheet(style)
        self.btn_menu.setStyleSheet(style)
        self.btn_replay.clicked.connect(
            lambda: [self.window().play_click(), self.replay_triggered.emit()]
        )
        self.btn_menu.clicked.connect(
            lambda: [self.window().play_click(), self.menu_triggered.emit()]
        )
        f_lay.addWidget(self.btn_replay)
        f_lay.addWidget(self.btn_menu)
        layout.addStretch()
        layout.addWidget(frame, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def show_res(self, l, r):
        self.res.setText(
            f"<div style='line-height: 180%;'><b>TOTAL CATCH:</b> <b style='color: #fabe42;'>{l+r}</b><br><b>LEFT HAND:</b> <b style='color: #00a8ff;'>{l}</b><br><b>RIGHT HAND:</b> <b style='color: #00a8ff;'>{r}</b></div>"
        )


class MainApp(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.sounds = None
        self.bg = QLabel(self)
        self.bg.setPixmap(QPixmap(resource_path("background.jpg")))
        self.bg.setScaledContents(True)
        self.bg.lower()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.showFullScreen()
        
        # Show splash page immediately
        self.splash = SplashPage(self)
        self.addWidget(self.splash)
        
        # Defer the heavy initialization to allow the UI to render right away
        QTimer.singleShot(100, self.init_heavy_components)

    def init_heavy_components(self):
        self.sounds = SoundGenerator()
        self.bg.resize(self.size())
        
        self.setup = SetupPage(self)
        self.instr = InstructionPage(self)
        self.calib = CalibrationPage(self)
        self.game = GamePage(self)
        self.summary = SummaryPage(self)
        
        self.addWidget(self.setup)
        self.addWidget(self.instr)
        self.addWidget(self.calib)
        self.addWidget(self.game)
        self.addWidget(self.summary)
        
        self.splash.finished.connect(lambda: self.setCurrentIndex(1))
        self.setup.start_setup.connect(self.go_instr)
        self.instr.back_triggered.connect(lambda: self.setCurrentIndex(1))
        self.instr.start_triggered.connect(self.go_calib)
        self.calib.back.connect(lambda: self.setCurrentIndex(2))
        self.calib.complete.connect(self.go_game)
        self.game.finished.connect(self.go_summary)
        self.summary.replay_triggered.connect(self.replay)
        self.summary.menu_triggered.connect(lambda: self.setCurrentIndex(1))

    # Audio helper methods
    def play_click(self):
        if self.sounds:
            self.sounds.play_tone(880, 50)

    def play_success(self):
        if self.sounds:
            self.sounds.play_tone(1200, 150)

    def play_fail(self):
        if self.sounds:
            self.sounds.play_tone(200, 300)

    def go_instr(self, dur, diff):
        self.dur = dur
        self.diff = diff
        self.setCurrentIndex(2)
        self.instr.start_t()

    def go_calib(self):
        self.setCurrentIndex(3)
        self.calib.start_c()

    def go_game(self, head_y, hip_y, d_swap):
        self.current_head_y, self.current_hip_y, self.current_swap_dist = head_y, hip_y, d_swap
        self.setCurrentIndex(4)
        self.game.start(head_y, hip_y, d_swap, self.dur, self.diff)

    def go_summary(self, l, r):  # Removed liv parameter
        self.summary.show_res(l, r)
        self.setCurrentIndex(5)

    def replay(self):
        self.setCurrentIndex(4)
        self.game.start(
            self.current_head_y, self.current_hip_y, self.current_swap_dist, self.dur, self.diff
        )

    def resizeEvent(self, e):
        if hasattr(self, "bg"):
            self.bg.resize(self.size())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())