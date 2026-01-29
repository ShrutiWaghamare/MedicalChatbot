"""
Medical Chatbot - RAG Chain Module
Connects to EXISTING Pinecone index (does not create or upload new documents)
"""
from dotenv import load_dotenv
import os
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

def initialize_chatbot():
    """
    Initialize the RAG chain by connecting to EXISTING Pinecone index.
    This function only READS from the index, never creates or uploads.
    """
    global _chatbot_instance
    
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
    
    # Create retriever (k=1 = faster retrieval; still good for short answers)
    retriever = docsearch.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 1}
    )
    
    # Initialize Azure OpenAI chat model
    chat_model = AzureChatOpenAI(
        azure_deployment="gpt-5.2-chat",
        api_version="2024-02-15-preview",
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        temperature=1,
        max_completion_tokens=800
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
    return rag_chain


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
        
        # Get conversation history (limit turns for faster response)
        history = conversation_memory.get_formatted_history(session_id, max_turns=2)
        
        # Build context with conversation history
        if history:
            # Include recent conversation context in the prompt
            context_with_history = f"Previous conversation:\n{history}\n\nCurrent question: {question}"
        else:
            context_with_history = question
        
        rag_chain = initialize_chatbot()
        response = rag_chain.invoke({"input": context_with_history})
        answer = response["answer"]
        
        # Add assistant response to memory
        conversation_memory.add_message(session_id, 'assistant', answer)
        
        return answer
    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        conversation_memory.add_message(session_id, 'assistant', error_msg)
        return error_msg


def get_response_stream(question: str, session_id: str = "default"):
    """
    Stream response from the chatbot token-by-token for faster perceived response.
    Yields chunks of the answer; saves full answer to memory when done.
    Falls back to non-streaming if stream not supported.
    """
    try:
        conversation_memory.add_message(session_id, 'user', question)
        history = conversation_memory.get_formatted_history(session_id, max_turns=2)
        context_with_history = (
            f"Previous conversation:\n{history}\n\nCurrent question: {question}"
            if history else question
        )
        rag_chain = initialize_chatbot()
        full_answer = ""
        try:
            for chunk in rag_chain.stream({"input": context_with_history}):
                part = chunk.get("answer", "") if isinstance(chunk, dict) else ""
                if isinstance(part, str) and part:
                    if part.startswith(full_answer):
                        delta = part[len(full_answer):]
                        full_answer = part
                    else:
                        delta = part
                        full_answer += part
                    if delta:
                        yield delta
        except (TypeError, AttributeError):
            # Chain may not support .stream(); fall back to invoke and yield once
            response = rag_chain.invoke({"input": context_with_history})
            answer = response.get("answer", "") or ""
            if answer:
                conversation_memory.add_message(session_id, 'assistant', answer)
                yield answer
            return
        if full_answer:
            conversation_memory.add_message(session_id, 'assistant', full_answer)
    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        conversation_memory.add_message(session_id, 'assistant', error_msg)
        yield error_msg
