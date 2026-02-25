"""
Medical Chatbot - RAG Chain Module
Connects to EXISTING Pinecone index (does not create or upload new documents)
"""
from dotenv import load_dotenv
import os
import re
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_openai import AzureChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from src.helper import download_hugging_face_embeddings
from src.prompt import system_prompt
from src.memory import conversation_memory

load_dotenv()

# Initialize chatbot components (only once)
_chatbot_instance = None
_retriever = None
_chat_model = None
_prompt_template = None

# Unicode ranges for emojis and symbols (used to strip from model output)
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"   # emoticons
    "\U0001F300-\U0001F5FF"   # symbols & pictographs
    "\U0001F680-\U0001F6FF"   # transport & map
    "\U0001F1E0-\U0001F1FF"   # flags
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"   # supplemental symbols
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "]+",
    flags=re.UNICODE,
)


def _strip_emojis(text: str) -> str:
    """Remove emoji and similar symbols from text. Preserves newlines."""
    if not text or not isinstance(text, str):
        return text
    cleaned = _EMOJI_PATTERN.sub("", text)
    # Preserve newlines: collapse only horizontal whitespace per line, trim lines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.split("\n")]
    return "\n".join(lines)


def _ensure_space_between_chunks(parts: list) -> str:
    """Join stream chunks with a space when two adjacent chunks would run together (no space/punctuation between).
    Ensures readable text: 'Common symptoms of diabetes' not 'Commonsymptomsofdiabetes'."""
    if not parts:
        return ""
    result = [parts[0]]
    for p in parts[1:]:
        prev = result[-1]
        need_space = (
            prev
            and p
            and prev[-1:] not in " \n\t.,;:!?)-]\"'"
            and p[:1] not in " \n\t.,;:!?(-[\"'"
        )
        if need_space:
            result.append(" ")
        result.append(p)
    return "".join(result)


def _fix_streamed_word_breaks(text: str) -> str:
    """Fix common word breaks from streaming (e.g. 'Di abetes' -> 'Diabetes', 'ur ination' -> 'urination')."""
    if not text or not isinstance(text, str):
        return text
    fixes = [
        (r"Di\s+abetes", "Diabetes"),
        (r"ur\s+ination", "urination"),
        (r"Excess\s+ive", "Excessive"),
        (r"Un\s+expl\s+ained", "Unexplained"),
        (r"Fat\s+igue", "Fatigue"),
        (r"Bl\s+urred", "Blurred"),
        (r"Ting\s+ling", "Tingling"),
        (r"numb\s+ness", "numbness"),
        (r"Ins\s+ulin", "Insulin"),
        (r"Horm\s+onal", "Hormonal"),
        (r"Frequent\s+urination", "Frequent urination"),  # in case broken twice
    ]
    out = text
    for pattern, replacement in fixes:
        out = re.sub(pattern, replacement, out, flags=re.IGNORECASE)
    return out


def _plain_text_answer(text: str) -> str:
    """Remove markdown so ** and ## don't show as raw symbols; keep line breaks; fix run-on lists."""
    if not text or not isinstance(text, str):
        return text
    # Normalize line endings
    out = text.replace("\r\n", "\n").replace("\r", "\n")
    # Strip bold: **text** or __text__ -> text
    out = re.sub(r"\*\*([^*]*)\*\*", r"\1", out)
    out = re.sub(r"__([^_]*)__", r"\1", out)
    # Strip headers: ## Header or # Header -> newline + Header
    out = re.sub(r"^#{1,6}\s*", "\n", out, flags=re.MULTILINE)
    # Fix run-on numbered list: "word.2.Item" -> "word.\n2. Item" so each item is on its own line
    out = re.sub(r"\.(\d+)\.\s*", r".\n\1. ", out)
    # Collapse multiple newlines to at most two, trim
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out


def initialize_chatbot():
    """
    Initialize the RAG chain by connecting to EXISTING Pinecone index.
    This function only READS from the index, never creates or uploads.
    """
    global _chatbot_instance, _retriever, _chat_model, _prompt_template

    if _chatbot_instance is not None:
        return _chatbot_instance
    
    # Get environment variables
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    if not all([PINECONE_API_KEY, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT]):
        raise ValueError("Missing required environment variables. Check .env file.")
    
    # Initialize embeddings (same model used for indexing)
    embeddings = download_hugging_face_embeddings()
    
    # Connect to EXISTING Pinecone index (do not create)
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_name = "medical-chatbot"
    
    # Verify index exists
    if index_name not in [idx.name for idx in pc.list_indexes()]:
        raise ValueError(f"Index '{index_name}' does not exist. Please run store_index.py first.")
    
    # Connect to existing index
    index = pc.Index(index_name)
    
    # Create vector store from EXISTING index (read-only operation)
    docsearch = PineconeVectorStore(
        index=index,
        embedding=embeddings,
        text_key="text"
    )
    
    # Create retriever (reads from existing index)
    retriever = docsearch.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )
    
    # Initialize Azure OpenAI chat model
    chat_model = AzureChatOpenAI(
        azure_deployment="gpt-5.2-chat",
        api_version="2024-02-15-preview",
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        temperature=1
    )
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    
    # Create RAG chain
    question_answer_chain = create_stuff_documents_chain(chat_model, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    _chatbot_instance = rag_chain
    _retriever = retriever
    _chat_model = chat_model
    _prompt_template = prompt
    return rag_chain


def _get_context_and_messages(context_with_history: str):
    """Retrieve documents and build messages for the LLM. Used by both invoke and stream."""
    rag_chain = initialize_chatbot()
    if _retriever is None or _chat_model is None or _prompt_template is None:
        raise RuntimeError("Chatbot not fully initialized")
    docs = _retriever.invoke(context_with_history)
    context_str = "\n\n".join(doc.page_content for doc in docs)
    messages = _prompt_template.invoke({"context": context_str, "input": context_with_history})
    return messages


def stream_response(question: str, session_id: str = "default"):
    """
    Stream response tokens from the medical chatbot with conversation memory.
    Yields raw text chunks. Caller must accumulate for full answer and post-process for memory.
    """
    try:
        conversation_memory.add_message(session_id, "user", question)
        history = conversation_memory.get_formatted_history(session_id)
        context_with_history = f"Previous conversation:\n{history}\n\nCurrent question: {question}" if history else question

        messages = _get_context_and_messages(context_with_history)
        full_answer_parts = []
        for chunk in _chat_model.stream(messages):
            if hasattr(chunk, "content") and chunk.content:
                text = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                full_answer_parts.append(text)
                yield text
        full_answer = _ensure_space_between_chunks(full_answer_parts)
        full_answer = _fix_streamed_word_breaks(full_answer)
        full_answer = _strip_emojis(full_answer)
        full_answer = _plain_text_answer(full_answer)
        conversation_memory.add_message(session_id, "assistant", full_answer)
    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        conversation_memory.add_message(session_id, "assistant", error_msg)
        yield error_msg


def get_response(question: str, session_id: str = "default") -> str:
    """
    Get response from the medical chatbot with conversation memory.
    
    Args:
        question: User's question
        session_id: Unique session identifier for conversation memory
        
    Returns:
        Bot's response string
    """
    try:
        # Add user message to memory
        conversation_memory.add_message(session_id, 'user', question)
        
        # Get conversation history
        history = conversation_memory.get_formatted_history(session_id)
        
        # Build context with conversation history
        if history:
            # Include recent conversation context in the prompt
            context_with_history = f"Previous conversation:\n{history}\n\nCurrent question: {question}"
        else:
            context_with_history = question
        
        rag_chain = initialize_chatbot()
        response = rag_chain.invoke({"input": context_with_history})
        answer = response["answer"]
        answer = _fix_streamed_word_breaks(answer)
        answer = _strip_emojis(answer)
        answer = _plain_text_answer(answer)
        
        # Add assistant response to memory
        conversation_memory.add_message(session_id, 'assistant', answer)
        
        return answer
    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        conversation_memory.add_message(session_id, 'assistant', error_msg)
        return error_msg
