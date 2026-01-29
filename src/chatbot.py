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
        
        # Add assistant response to memory
        conversation_memory.add_message(session_id, 'assistant', answer)
        
        return answer
    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        conversation_memory.add_message(session_id, 'assistant', error_msg)
        return error_msg
