# Quiz Questionizer

A simple Flask web application that captures quiz questions from a quiz book using your webcam and converts them into OBS-ready HTML displays.

## Features

- 📷 **Camera Integration**: Capture quiz pages directly from your webcam
- 🤖 **AI-Powered OCR**: Uses LLM to extract structured quiz data from images
- 🎯 **Real-time Updates**: Server-Sent Events (SSE) for live quiz display updates
- 🎨 **OBS-Ready HTML**: Clean, formatted quiz display perfect for streaming
- 🔄 **Multiple Camera Support**: Test and discover available cameras
- 📱 **Web Interface**: Simple web UI for capturing and managing quiz questions

## Quick Start

### Preparations

1. Install dependencies: `uv sync`
2. Copy '.env.example' to '.env' and fill in your LLM API keys

### Basic Operation

1. **Start the server**: `uv run python app.py`
2. **Add output to OBS**: Add a browser source with `http://localhost:3001` to your OBS scene
3. **Capture a quiz**: Send a POST request to `http://localhost:3001/questionize`, e.g. using the [API Ninja](https://marketplace.elgato.com/product/api-ninja-fd59edeb-e7e5-412f-91ef-304c3e03f035) plugin for StreamDeck
4. **View results**: The extracted quiz question will appear in OBS automatically

### Camera Management

**Discover available cameras:**
```bash
uv run python app.py --discover
```

**Test a specific camera:**
```bash
uv run python app.py --camera 1 --test
```

**Live camera preview:**
```bash
uv run python app.py --camera 1 --preview
```

**Use a specific camera for the app:**
```bash
uv run python app.py --camera 1
```

### API Endpoints

- `GET /` - Main quiz display page
- `POST /questionize` - Capture and process a new quiz question
- `POST /reset` - Clear current quiz data
- `GET /events` - SSE endpoint for real-time updates

## Project Structure

```
├── app.py              # Main Flask application
├── camera.py           # Camera capture utilities
├── templates/          # HTML templates
│   ├── base.html       # Base template
│   ├── index.html      # Main page
│   └── quiz_display.html # Quiz question display
└── quiz_data.json      # Current quiz data (auto-generated)
```

## Configuration

The app expects quiz books with this structure:
- Chapter numbers
- Question numbers with question mark icons
- Four multiple choice answers (A, B, C, D)
- Clear text formatting

## License

MIT License - see LICENSE file for details.
