"""
Medical Chatbot - Flask Application
Main entry point for the web interface.
Chatbot answers user questions via RAG (no file uploads).
"""
from flask import Flask, render_template, request, jsonify, session, Response, stream_with_context
from src.chatbot import get_response, stream_response
from src.memory import conversation_memory
from src.storage import init_db, fetch_messages, insert_reaction, delete_reaction, fetch_reactions, record_visit, fetch_visits, get_visit_counts
import logging
import uuid
import os
import threading

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
    # Record visitor (page load) off critical path so response is not delayed (PERF_PLAN)
    from datetime import datetime
    def _record_visit():
        try:
            record_visit(
                session['session_id'],
                datetime.utcnow().isoformat(),
                user_agent=request.headers.get('User-Agent'),
                referrer=request.referrer,
            )
        except Exception as e:
            logger.warning(f"Could not record visit: {e}")
    t = threading.Thread(target=_record_visit, daemon=True)
    t.start()
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


# SSE comment padding to force WSGI/server to flush each event (avoid buffering full response)
_SSE_FLUSH_PADDING = ": " + (" " * 2048) + "\n"


def _stream_events(session_id: str, question: str):
    """Generate SSE events from stream_response. Sends 'data: <chunk>' per token and final 'data: [DONE]'.
    Uses padding so each yield is sent immediately (stream-wise) instead of being buffered."""
    try:
        for chunk in stream_response(question, session_id=session_id):
            if chunk:
                # Send chunk + padding so server flushes immediately (token-wise streaming)
                yield f"data: {chunk}\n{_SSE_FLUSH_PADDING}\n"
        yield f"data: [DONE]\n{_SSE_FLUSH_PADDING}\n"
    except Exception as e:
        logger.error(f"Stream error: {str(e)}", exc_info=True)
        yield f"data: [ERROR] {str(e)}\n{_SSE_FLUSH_PADDING}\n"


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Handle chat with Server-Sent Events streaming."""
    try:
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        session_id = session['session_id']
        data = request.get_json()
        question = (data.get('question') or '').strip()
        if not question:
            return jsonify({'success': False, 'error': 'Please provide a question.'}), 400
        logger.info(f"Session {session_id[:8]}... - Stream question: {question}")
        return Response(
            stream_with_context(_stream_events(session_id, question)),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
            },
        )
    except Exception as e:
        logger.error(f"Error starting stream: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


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


@app.route('/api/reaction', methods=['POST'])
def reaction():
    """Save like/dislike feedback for a message."""
    try:
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        session_id = session['session_id']
        data = request.get_json() or {}
        message_id = data.get('message_id')
        reaction_val = data.get('reaction')
        if not message_id:
            return jsonify({'success': False, 'error': 'message_id required'}), 400
        if reaction_val is None or reaction_val == '':
            delete_reaction(session_id, message_id)
            return jsonify({'success': True, 'message': 'Reaction removed'})
        if reaction_val not in ('like', 'dislike'):
            return jsonify({'success': False, 'error': 'reaction must be like or dislike'}), 400
        from datetime import datetime
        message_content = (data.get('message_content') or '').strip()[:2000]
        insert_reaction(
            session_id, message_id, reaction_val, datetime.utcnow().isoformat(),
            message_content=message_content or None,
        )
        logger.info(f"Session {session_id[:8]}... - Reaction: {reaction_val} for message {message_id}")
        return jsonify({'success': True, 'message': 'Reaction saved'})
    except Exception as e:
        logger.error(f"Error saving reaction: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def _admin_allowed():
    """Allow admin if ADMIN_SECRET is unset, or if request has ?key=ADMIN_SECRET."""
    secret = os.environ.get('ADMIN_SECRET')
    if not secret:
        return True
    return request.args.get('key') == secret


@app.route('/api/feedback', methods=['GET'])
def feedback():
    """Return recent feedback (reactions) for viewing/export. Optional: limit=200. When ADMIN_SECRET is set, ?key= required."""
    if not _admin_allowed():
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        limit = request.args.get('limit', 200, type=int)
        limit = min(max(1, limit), 500)
        reactions = fetch_reactions(limit=limit)
        return jsonify({'success': True, 'feedback': reactions})
    except Exception as e:
        logger.error(f"Error fetching feedback: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/visits', methods=['GET'])
def visits():
    """Return recent visitor records for admin/analytics. Optional: limit=500. When ADMIN_SECRET is set, ?key= required."""
    if not _admin_allowed():
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        limit = request.args.get('limit', 500, type=int)
        limit = min(max(1, limit), 1000)
        visits_list = fetch_visits(limit=limit)
        counts = get_visit_counts()
        return jsonify({'success': True, 'visits': visits_list, 'total_visits': counts['total_visits'], 'unique_visitors': counts['unique_visitors']})
    except Exception as e:
        logger.error(f"Error fetching visits: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin')
def admin():
    """Admin dashboard: visits and feedback. Optional: set ADMIN_SECRET and use ?key=... to protect."""
    if not _admin_allowed():
        return jsonify({'error': 'Unauthorized'}), 403
    visits_list = []
    feedback_list = []
    visit_counts = {"total_visits": 0, "unique_visitors": 0}
    try:
        visits_list = fetch_visits(limit=200)
    except Exception as e:
        logger.warning(f"Could not load visits for admin: {e}")
    try:
        feedback_list = fetch_reactions(limit=200)
    except Exception as e:
        logger.warning(f"Could not load feedback for admin: {e}")
    try:
        visit_counts = get_visit_counts()
    except Exception as e:
        logger.warning(f"Could not load visit counts for admin: {e}")
    return render_template(
        'admin.html',
        visits=visits_list,
        feedback=feedback_list,
        visit_counts=visit_counts,
        api_base=request.script_root.rstrip('/') if request.script_root else '',
    )


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
