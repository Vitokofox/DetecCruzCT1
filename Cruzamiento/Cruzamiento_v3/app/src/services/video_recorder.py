import os
import cv2
from typing import Any
from datetime import datetime

DEFAULT_TARGET_FPS = 30.0

def now_str() -> str:
    """Retorna la fecha y hora actual en formato YYYYMMDD_HHMMSS."""
    return datetime.now().strftime('%Y%m%d_%H%M%S')

class VideoRecorder:
    """Manejador de grabación de video dual."""
    def __init__(self, target_fps: float = DEFAULT_TARGET_FPS):
        self.target_fps = target_fps
        self.recording = False
        self.record_with_detections = False
        self.writer1 = None
        self.writer2 = None
        self.writer_size1 = None
        self.writer_size2 = None
        self.grab_dir = None

    def setup_directories(self, base_dir: str):
        self.grab_dir = os.path.join(base_dir, "grabaciones")
        os.makedirs(self.grab_dir, exist_ok=True)

    def start_recording(self, frame1: Any, frame2: Any, with_detections: bool = False) -> bool:
        if self.recording:
            return False
        if frame1 is None and frame2 is None:
            return False
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        timestamp = now_str()
        success = False
        if frame1 is not None:
            h1, w1 = frame1.shape[:2]
            self.writer_size1 = (w1, h1)
            filename1 = f"{'conDet' if with_detections else 'sinDet'}_C1_{timestamp}.mp4"
            path1 = os.path.join(self.grab_dir, filename1)
            self.writer1 = cv2.VideoWriter(path1, fourcc, self.target_fps, self.writer_size1)
            if self.writer1.isOpened():
                print(f"📹 Grabación C1 iniciada: {path1}")
                success = True
            else:
                self.writer1 = None
        if frame2 is not None:
            h2, w2 = frame2.shape[:2]
            self.writer_size2 = (w2, h2)
            filename2 = f"{'conDet' if with_detections else 'sinDet'}_C2_{timestamp}.mp4"
            path2 = os.path.join(self.grab_dir, filename2)
            self.writer2 = cv2.VideoWriter(path2, fourcc, self.target_fps, self.writer_size2)
            if self.writer2.isOpened():
                print(f"📹 Grabación C2 iniciada: {path2}")
                success = True
            else:
                self.writer2 = None
        if success:
            self.recording = True
            self.record_with_detections = with_detections
            print(f"🔴 Grabación {'con' if with_detections else 'sin'} detecciones iniciada")
        return success

    def stop_recording(self):
        for writer in [self.writer1, self.writer2]:
            if writer:
                try:
                    writer.release()
                except Exception as e:
                    print(f"⚠️ Error cerrando writer: {e}")
        self.writer1 = None
        self.writer2 = None
        self.writer_size1 = None
        self.writer_size2 = None
        self.recording = False
        self.record_with_detections = False
        print("⏹️ Grabación detenida")

    def write_frames(self, frame1: Any, frame2: Any, frame1_det: Any = None, frame2_det: Any = None):
        """
        Escribe frames en el video.
        
        Args:
            frame1: Frame crudo cámara 1
            frame2: Frame crudo cámara 2
            frame1_det: Frame con detecciones cámara 1
            frame2_det: Frame con detecciones cámara 2
        """
        if not self.recording:
            return
        if self.writer1 and frame1 is not None:
            frame_to_write = frame1_det if (self.record_with_detections and frame1_det is not None) else frame1
            if frame_to_write.shape[:2][::-1] != self.writer_size1:
                frame_to_write = cv2.resize(frame_to_write, self.writer_size1)
            self.writer1.write(frame_to_write)
        if self.writer2 and frame2 is not None:
            frame_to_write = frame2_det if (self.record_with_detections and frame2_det is not None) else frame2
            if frame_to_write.shape[:2][::-1] != self.writer_size2:
                frame_to_write = cv2.resize(frame_to_write, self.writer_size2)
            self.writer2.write(frame_to_write)
