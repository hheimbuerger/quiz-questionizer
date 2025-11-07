import cv2
from contextlib import contextmanager

@contextmanager
def video_capture(camera_index=0):
    """
    Context manager for video capture.
    
    Args:
        camera_index (int): Index of the camera to use.
        
    Yields:
        numpy.ndarray: A video frame if successful.
        
    Raises:
        RuntimeError: If the camera cannot be opened or no frame is captured.
    """
    vc = cv2.VideoCapture(camera_index)
    try:
        if not vc.isOpened():
            raise RuntimeError(f"Could not open camera with index {camera_index}")
            
        rval, frame = vc.read()
        if not rval or frame is None:
            raise RuntimeError("Failed to capture frame from camera")
            
        yield frame
    finally:
        vc.release()

# Example usage:
if __name__ == "__main__":
    try:
        with video_capture(0) as frame:
            print(f"Frame captured successfully! Shape: {frame.shape}")
    except RuntimeError as e:
        print(f"Error: {e}")
