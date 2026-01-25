"""
Medical Chatbot - Flask Application
Main entry point for the web interface.
Chatbot answers user questions via RAG (no file uploads).
"""
from flask import Flask, render_template, request, jsonify, session
from src.chatbot import get_response
from src.memory import conversation_memory
from src.storage import init_db, fetch_messages
import logging
import uuid
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Initialize SQLite storage (conversations only)
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

        # Get response from chatbot with memory
        answer = get_response(question, session_id=session_id)
        
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
