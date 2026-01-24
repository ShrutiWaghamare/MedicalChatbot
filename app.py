"""
Medical Chatbot - Flask Application
Main entry point for the web interface
"""
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
from src.chatbot import get_response
from src.memory import conversation_memory
from src.storage import init_db, insert_upload, fetch_latest_upload_text, fetch_messages
import logging
import uuid
import os
from pypdf import PdfReader
from docx import Document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Upload configuration
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".doc", ".docx", ".txt"}
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE

# Initialize SQLite storage
init_db()

@app.route('/')
def index():
    """Serve the main chat interface"""
    # Initialize session ID if not exists
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat API requests with conversation memory"""
    try:
        # Get or create session ID
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        session_id = session['session_id']
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'Please provide a question.'
            }), 400
        
        logger.info(f"Session {session_id[:8]}... - Question: {question}")
        
        # If there's a recent upload and the question seems related, include it
        file_context = fetch_latest_upload_text(session_id)
        if file_context and _looks_like_file_question(question):
            enriched_question = _build_file_context(question, file_context)
        else:
            enriched_question = question

        # Get response from chatbot with memory
        answer = get_response(enriched_question, session_id=session_id)
        
        logger.info(f"Session {session_id[:8]}... - Generated answer: {answer[:100]}...")
        
        return jsonify({
            'success': True,
            'answer': answer
        })
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500


def _looks_like_file_question(question: str) -> bool:
    lower = question.lower()
    keywords = ["file", "document", "resume", "pdf", "above", "attached", "upload"]
    return any(k in lower for k in keywords)


def _build_file_context(question: str, file_text: str) -> str:
    # Limit file text to avoid overly long context
    max_chars = 4000
    snippet = file_text[:max_chars]
    return (
        "User question:\n"
        f"{question}\n\n"
        "Attached file content (truncated):\n"
        f"{snippet}"
    )


@app.route('/api/chat-with-file', methods=['POST'])
def chat_with_file():
    """Handle chat with file upload in a single request."""
    try:
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

        session_id = session['session_id']
        question = request.form.get('question', '').strip()
        if not question:
            return jsonify({'success': False, 'error': 'Please provide a question.'}), 400

        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided.'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected.'}), 400
        if not _allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed.'}), 400

        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_DIR, filename)
        file.save(save_path)

        file_size = os.path.getsize(save_path)
        extracted_text = _extract_text_from_file(save_path)
        insert_upload(
            session_id=session_id,
            filename=filename,
            path=save_path,
            mime_type=file.mimetype or 'application/octet-stream',
            size=file_size,
            extracted_text=extracted_text,
        )

        enriched_question = _build_file_context(question, extracted_text) if extracted_text else question
        answer = get_response(enriched_question, session_id=session_id)

        return jsonify({'success': True, 'answer': answer})
    except Exception as e:
        logger.error(f"Error processing chat-with-file request: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/clear', methods=['POST'])
def clear_memory():
    """Clear conversation memory for current session"""
    try:
        if 'session_id' in session:
            conversation_memory.clear_conversation(session['session_id'])
            logger.info(f"Cleared memory for session {session['session_id'][:8]}...")
            return jsonify({'success': True, 'message': 'Conversation history cleared'})
        return jsonify({'success': False, 'error': 'No active session'}), 400
    except Exception as e:
        logger.error(f"Error clearing memory: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


@app.route('/api/history', methods=['GET'])
def history():
    """Return conversation history for current session."""
    try:
        if 'session_id' not in session:
            return jsonify({'success': True, 'messages': []})
        session_id = session['session_id']
        messages = fetch_messages(session_id)
        return jsonify({'success': True, 'messages': messages})
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def _allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS


def _extract_text_from_file(path: str) -> str:
    _, ext = os.path.splitext(path.lower())
    try:
        if ext == ".txt":
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        if ext == ".pdf":
            reader = PdfReader(path)
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
            return "\n".join(text_parts)
        if ext in {".doc", ".docx"}:
            doc = Document(path)
            return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        logger.warning(f"Failed to extract text from file: {e}")
    return ""


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file uploads and persist metadata in SQLite."""
    try:
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided.'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected.'}), 400

        if not _allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed.'}), 400

        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_DIR, filename)

        file.save(save_path)

        file_size = os.path.getsize(save_path)
        extracted_text = _extract_text_from_file(save_path)
        upload_meta = insert_upload(
            session_id=session['session_id'],
            filename=filename,
            path=save_path,
            mime_type=file.mimetype or 'application/octet-stream',
            size=file_size,
            extracted_text=extracted_text,
        )

        return jsonify({'success': True, 'upload': upload_meta})
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'}), 500

if __name__ == '__main__':
    # Initialize chatbot on startup (lazy loading)
    logger.info("Starting Medical Chatbot application...")
    try:
        from src.chatbot import initialize_chatbot
        initialize_chatbot()
        logger.info("✅ Chatbot initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Chatbot initialization warning: {str(e)}")
        logger.info("Chatbot will initialize on first query")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
