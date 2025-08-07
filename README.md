# QuizQuestionizer 📚📷

Transform your quiz book screenshots into OBS-ready HTML displays with just a few clicks! Perfect for quizmasters and educators who want to present questions in a clean, professional format during live sessions.

## ✨ Features

- **Webcam Capture**: Take screenshots directly from your quiz book
- **Automatic Processing**: Convert images to text and format them beautifully
- **OBS Integration**: Ready-to-use HTML output for seamless streaming
- **Simple Interface**: User-friendly controls for a smooth experience

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Webcam
- (Optional) OBS Studio for streaming

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/hheimbuerger/quizquestionizer.git
   cd quizquestionizer
   ```

2. Install dependencies (using [uv](https://github.com/astral-sh/uv) for faster installation):
   ```bash
   uv sync
   ```

### Running the Application

1. Create an OpenAI API key and add it to a `.env` file in the root directory of the project, or set it as a `OPENAI_API_KEY` environment variable.

2. You'll have to update the prompt in `app.py` to match your quiz book's structure.

3. Start the application:
   ```bash
   uv run app.py
   ```

4. Add http://localhost:3001 as a `Browser` source to OBS. (Will automatically update when a new question is captured.)

5. Trigger a question capture by sending a POST request to `/questionize`:
   ```bash
   curl -X POST http://localhost:3001/questionize
   ```

   ```bash
   uvx --from=httpie http POST http://localhost:3001/questionize
   ```

    Or add to StreamDeck e.g. using API Ninja.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.