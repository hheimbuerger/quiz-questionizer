from flask import Flask, render_template, request, jsonify, Response
from camera import video_capture
from fluent_llm import llm
import cv2
import json
import os
import numpy as np
import time
import threading
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Global set to track SSE clients
sse_clients = set()

# LLM Prompt for extracting quiz data
PROMPT = r"""
You're seeing a photo of a page from a German quiz book.

It will have the following basic structure. I'll mark named sections with `{section_name, section_notes}`. Images and other markup I'll described with brackets like `[image of X]`.

"
------- Kapitel {chapter_number} -------


Frage #{question_number}

[big question mark] {question, across multiple paragraphs}


[line across the page]

{answers, four sections, each prefixed with an uppercase letter A, B, C, D, then a possible answer}
"

Extract all the sections as JSON. Format like this:
{
    "chapter_number": 2,
    "question_number": 4,
    "question": "Hier ist eine Frage aus der Kategorie 'Geografie'.\n\nWas ist die Hauptstadt von Frankreich?",
    "answers": {
        "A": "Paris",
        "B": "London",
        "C": "Berlin",
        "D": "Madrid"
    }
}

Preserve explicit line and paragraph breaks.

Be very precise in the capturing of the text -- especially in the answers! They might contain hints
or intentional misleading elements. Do not modify, even when you think something is misspelled or
incorrectly set. For example, do not add punctuation where there is none!

Return JSON only, no markup.
"""

# Data storage functions
def load_quiz_data():
    """Load quiz data from JSON file if it exists."""
    if os.path.exists('quiz_data.json'):
        try:
            with open('quiz_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None

def save_quiz_data(data):
    """Save quiz data to JSON file."""
    with open('quiz_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_quiz_html(data):
    """Generate HTML for the quiz question using Flask's application context."""
    with app.app_context():
        return render_template('quiz_display.html', quiz_data=data)

def test_camera(camera_id):
    """Test a single camera by capturing and displaying an image."""
    print(f"\n=== Testing Camera ID: {camera_id} ===")
    
    try:
        with video_capture(camera_id) as frame:
            print(f"✓ Camera {camera_id} is working!")
            print(f"  Resolution: {frame.shape[1]}x{frame.shape[0]}")
            print(f"  Channels: {frame.shape[2] if len(frame.shape) > 2 else 1}")
            
            # Save test image
            filename = f"camera_{camera_id}_test.jpg"
            cv2.imwrite(filename, frame)
            print(f"  Test image saved as: {filename}")
            
            # Display the image
            cv2.imshow(f"Camera {camera_id} Test", frame)
            print(f"  Press any key to close the preview window...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
            return True
            
    except RuntimeError as e:
        print(f"✗ Camera {camera_id} failed: {e}")
        return False

def discover_cameras(max_cameras=10):
    """Discover available cameras by testing multiple IDs."""
    print(f"\n=== Discovering Cameras (testing IDs 0-{max_cameras-1}) ===")
    
    available_cameras = []
    
    for camera_id in range(max_cameras):
        print(f"\nTesting camera ID {camera_id}...", end=" ")
        
        try:
            with video_capture(camera_id) as frame:
                print(f"✓ Available ({frame.shape[1]}x{frame.shape[0]})")
                available_cameras.append(camera_id)
        except RuntimeError:
            print("✗ Not available")
    
    print(f"\n=== Discovery Results ===")
    if available_cameras:
        print(f"Available cameras: {available_cameras}")
        print(f"\nTo test a specific camera:")
        for cam_id in available_cameras:
            print(f"  python app.py --camera {cam_id} --test")
    else:
        print("No cameras found!")
    
    return available_cameras

def preview_camera(camera_id):
    """Show live preview of camera feed."""
    print(f"\n=== Camera {camera_id} Live Preview ===")
    print("Press 'q' to quit, 's' to save a snapshot")
    
    try:
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open camera {camera_id}")
        
        snapshot_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame")
                break
            
            # Add overlay text
            cv2.putText(frame, f"Camera {camera_id} - Press 'q' to quit, 's' for snapshot", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow(f"Camera {camera_id} Preview", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                snapshot_count += 1
                filename = f"camera_{camera_id}_snapshot_{snapshot_count}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Snapshot saved: {filename}")
        
        cap.release()
        cv2.destroyAllWindows()
        
    except RuntimeError as e:
        print(f"Preview failed: {e}")

def broadcast_to_clients(event_type, data=None):
    """Broadcast an event to all connected SSE clients."""
    if not sse_clients:
        print(f"No SSE clients to broadcast {event_type} to")
        return
    
    # Format the message based on event type
    if event_type == 'quiz_update':
        html = generate_quiz_html(data) if data else ''
        message = f"data: {json.dumps({'type': 'update', 'html': html, 'quiz_data': data})}\n\n"
    elif event_type == 'quiz_reset':
        message = f"data: {json.dumps({'type': 'reset'})}\n\n"
    else:
        message = f"data: {json.dumps({'type': event_type, 'data': data})}\n\n"

    # Send to all clients, removing dead ones
    dead_clients = set()
    for client in sse_clients.copy():
        try:
            client.put(message)
        except:
            dead_clients.add(client)

    # Remove dead clients
    sse_clients.difference_update(dead_clients)
    print(f"Broadcasted {event_type} to {len(sse_clients)} clients")

@app.route('/')
def index():
    """Main page showing the current quiz question or empty state."""
    quiz_data = load_quiz_data()
    return render_template('index.html', quiz_data=quiz_data)

@app.route('/events')
def events():
    """SSE endpoint for real-time updates."""
    import queue

    def event_stream():
        client_queue = queue.Queue()
        sse_clients.add(client_queue)

        try:
            # Send current quiz data immediately upon connection
            current_quiz = load_quiz_data()
            if current_quiz:
                html = generate_quiz_html(current_quiz)
                initial_message = f"data: {json.dumps({'type': 'initial', 'html': html, 'quiz_data': current_quiz})}\n\n"
            else:
                initial_message = f"data: {json.dumps({'type': 'reset'})}\n\n"
            yield initial_message

            # Keep connection alive and send updates
            while True:
                try:
                    # Wait for new messages with timeout
                    message = client_queue.get(timeout=30)
                    yield message
                except queue.Empty:
                    # Send keepalive
                    yield ": keepalive\n\n"

        except GeneratorExit:
            # Client disconnected
            pass
        finally:
            sse_clients.discard(client_queue)
            print(f"SSE client disconnected. Remaining clients: {len(sse_clients)}")

    return Response(event_stream(), mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache',
                           'Connection': 'keep-alive',
                           'Access-Control-Allow-Origin': '*'})

@app.route('/questionize', methods=['POST'])
def questionize():
    """Capture a new quiz question from the camera."""
    try:
        print("Capturing frame...")
        # Capture a frame from the camera
        camera_id = app.config.get('CAMERA_ID', 0)  # Default to 0 if not set
        with video_capture(camera_id) as frame:
            result, openai_image = cv2.imencode(".png", frame)
            if not result:
                raise Exception("Failed to capture frame")

            # Process the image with the language model
            print('Extracting question...')
            response = llm.image(openai_image.tobytes()).request(PROMPT).prompt()
            print(response)
            response_dict = json.loads(response)

            # Store the quiz data
            print('Notifying clients...')
            save_quiz_data(response_dict)

            # Broadcast the update to all connected SSE clients
            broadcast_to_clients('quiz_update', response_dict)

            return jsonify({"status": "success", "message": "Question captured successfully"})

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse LLM response as JSON: {str(e)}"
        print(f"JSON Error: {error_msg}")
        return jsonify({"status": "error", "error": error_msg}), 500

    except Exception as e:
        error_msg = f"Error processing image: {str(e)}"
        print(f"Processing Error: {error_msg}")
        return jsonify({"status": "error", "error": error_msg}), 500

@app.route('/reset', methods=['POST'])
def reset():
    """Reset the quiz by removing stored data."""
    try:
        if os.path.exists('quiz_data.json'):
            os.remove('quiz_data.json')

        # Broadcast the reset to all connected SSE clients
        broadcast_to_clients('quiz_reset')

        return jsonify({"status": "success", "message": "Quiz reset successfully"})
    except Exception as e:
        error_msg = f"Error resetting quiz: {str(e)}"
        print(f"Reset Error: {error_msg}")
        return jsonify({"status": "error", "error": error_msg}), 500

def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser(description='Quiz Questionizer - Generate quiz questions from camera input')
    parser.add_argument('--camera', type=int, default=0,
                       help='Camera device ID (default: 0)')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: capture and display a single image, then exit')
    parser.add_argument('--discover', action='store_true',
                       help='Discovery mode: test multiple camera IDs to find available cameras')
    parser.add_argument('--preview', action='store_true',
                       help='Preview mode: show live video feed for camera verification')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arguments()
    
    # Handle test modes
    if args.discover:
        discover_cameras()
        exit(0)
    
    if args.test:
        success = test_camera(args.camera)
        exit(0 if success else 1)
    
    if args.preview:
        preview_camera(args.camera)
        exit(0)
    
    # Store the camera ID in the app config
    app.config['CAMERA_ID'] = args.camera
    
    print("Starting Quiz Questionizer Flask App...")
    print(f"Using camera device ID: {app.config['CAMERA_ID']}")
    print("\nAvailable endpoints:")
    print("  http://localhost:3001/         - View the current quiz")
    print("  http://localhost:3001/questionize - Capture a new quiz from camera (POST)")
    print("  http://localhost:3001/reset     - Reset quiz data (POST)")
    print("\nTest modes:")
    print("  python app.py --discover       - Find available cameras")
    print("  python app.py --camera X --test - Test specific camera")
    print("  python app.py --camera X --preview - Live camera preview")
    print("\nPress Ctrl+C to stop the server\n")

    app.run(host='localhost', port=3001, debug=True)
