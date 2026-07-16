from langgraph.graph import (
    StateGraph,
    START,
    END
)

from typing import TypedDict, Annotated

from langchain_core.messages import BaseMessage, SystemMessage

from langchain_core.tools import tool

from langgraph.graph.message import add_messages

from dotenv import load_dotenv

from langchain_groq import ChatGroq


from langgraph.prebuilt import (
    ToolNode,
    tools_condition
)


from langchain_community.tools import DuckDuckGoSearchRun


from langchain_community.document_loaders import PyPDFLoader


from langchain_text_splitters import RecursiveCharacterTextSplitter


from langchain_google_genai import GoogleGenerativeAIEmbeddings


from langchain_community.vectorstores import FAISS


from langgraph.checkpoint.sqlite import SqliteSaver


import sqlite3

import requests

import os


# =====================================================
# Environment
# =====================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GROQ_API_KEY:
    # Fail fast with a clear message instead of a confusing downstream
    # authentication error the first time the model is invoked.
    raise RuntimeError(
        "GROQ_API_KEY is missing. Add it to your .env file before starting the app."
    )


# =====================================================
# LLM
# =====================================================

model = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY
)


# =====================================================
# State
# =====================================================

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# =====================================================
# RAG Variables
# =====================================================

# NOTE: This app uses a single shared knowledge base for all chats/users
# (a common pattern for "chat with your docs" apps). If per-user or
# per-thread isolation is needed later, swap these globals for a
# dict keyed by thread_id / session_id.
vectorstore = None
retriever = None
indexed_files = set()  # tracks which files have already been embedded


# =====================================================
# Upload Document Function
# =====================================================

def upload_document(file_path: str):
    """
    Add an uploaded PDF into the shared RAG knowledge base.

    Documents are ACCUMULATED (not replaced) so previously uploaded
    files remain queryable after a new file is added.
    """

    global vectorstore
    global retriever
    global indexed_files

    file_name = os.path.basename(file_path)

    if file_name in indexed_files:
        return {
            "status": f"'{file_name}' is already indexed.",
            "chunks": 0
        }

    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        if not documents:
            return {
                "status": f"Could not extract any text from '{file_name}'.",
                "chunks": 0
            }

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=200
        )

        chunks = splitter.split_documents(documents)

        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001"
        )

        if vectorstore is None:
            vectorstore = FAISS.from_documents(chunks, embeddings)
        else:
            vectorstore.add_documents(chunks)

        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )

        indexed_files.add(file_name)

        return {
            "status": f"'{file_name}' indexed successfully.",
            "chunks": len(chunks)
        }

    except Exception as e:
        return {
            "status": f"Failed to index '{file_name}': {e}",
            "chunks": 0
        }


# =====================================================
# RAG Tool
# =====================================================

@tool
def rag_tool(query: str) -> dict:
    """
    Search uploaded documents.
    Use when user asks questions about uploaded files.
    """

    global retriever

    if retriever is None:
        return {
            "message": "No document uploaded."
        }

    try:
        docs = retriever.invoke(query)
    except Exception as e:
        return {"message": f"Document search failed: {e}"}

    return {
        "query": query,
        "context": [doc.page_content for doc in docs],
        "metadata": [doc.metadata for doc in docs]
    }


# =====================================================
# Calculator Tool
# =====================================================

@tool
def calculator(
    first_num: float,
    second_num: float,
    operation: str
) -> str:
    """
    Perform arithmetic calculations.

    Operations:
    add
    subtract
    multiply
    divide
    """

    try:
        if operation == "add":
            return str(first_num + second_num)
        elif operation == "subtract":
            return str(first_num - second_num)
        elif operation == "multiply":
            return str(first_num * second_num)
        elif operation == "divide":
            if second_num == 0:
                return "Cannot divide by zero"
            return str(first_num / second_num)
        return "Invalid operation"
    except Exception as e:
        return f"Calculation error: {e}"


# =====================================================
# Stock Price Tool
# =====================================================

@tool
def get_stock_price(symbol: str) -> dict:
    """
    Get stock price using Alpha Vantage API.

    Example:
    AAPL
    """

    if not ALPHAVANTAGE_API_KEY:
        return {"error": "ALPHAVANTAGE_API_KEY is not configured."}

    url = (
        "https://www.alphavantage.co/query"
        "?function=GLOBAL_QUOTE"
        f"&symbol={symbol}"
        f"&apikey={ALPHAVANTAGE_API_KEY}"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": f"Failed to fetch stock price: {e}"}


# =====================================================
# Web Search Tool
# =====================================================

search = DuckDuckGoSearchRun()


@tool
def web_search(query: str) -> str:
    """
    Search the internet for latest information.

    Use this when user asks about:
    - current information
    - latest news
    - online examples
    - documentation
    """

    try:
        return search.run(query)
    except Exception as e:
        return f"Web search failed: {e}"


# =====================================================
# Tools List
# =====================================================

tools = [
    calculator,
    get_stock_price,
    web_search,
    rag_tool
]


# =====================================================
# Bind Tools With LLM
# =====================================================

llm_with_tools = model.bind_tools(tools)


# =====================================================
# Chat Node
# =====================================================

def chat_node(state: ChatState):
    messages = state["messages"]

    system = SystemMessage(
        content="""
You are an AI assistant.

Rules:
- Use calculator for mathematical operations.
- Use web_search only when information requires internet.
- Use rag_tool only for uploaded documents.
- Do not call tools unnecessarily.
- If a tool returns an error, tell the user clearly what went wrong
  and continue helping instead of failing silently.
"""
    )

    try:
        response = llm_with_tools.invoke([system] + messages)
    except Exception as e:
        # Surface model/API failures as a normal assistant message instead
        # of letting the exception bubble up and crash the app.
        from langchain_core.messages import AIMessage
        response = AIMessage(
            content=f"Sorry, I ran into an error talking to the language model: {e}"
        )

    return {"messages": [response]}


# =====================================================
# SQLite Database
# =====================================================

conn = sqlite3.connect(
    "chatbot.db",
    check_same_thread=False
)

cursor = conn.cursor()

# Chat table
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS chats
    (
        thread_id TEXT PRIMARY KEY,
        chat_name TEXT
    )
    """
)

conn.commit()


# =====================================================
# LangGraph Checkpointer
# =====================================================

checkpointer = SqliteSaver(conn)


# =====================================================
# Graph Creation
# =====================================================

graph = StateGraph(ChatState)

graph.add_node("chat_node", chat_node)
graph.add_node("tools", ToolNode(tools))

graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")

workflow = graph.compile(checkpointer=checkpointer)


# =====================================================
# Chat Management Functions
# =====================================================

def get_all_threads():
    """
    Get all LangGraph thread IDs
    """

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT DISTINCT thread_id
        FROM checkpoints
        """
    )
    rows = cursor.fetchall()
    return [row[0] for row in rows]


def create_chat_record(thread_id):
    """
    Create new chat entry
    """

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO chats
        (thread_id, chat_name)
        VALUES (?, ?)
        """,
        (thread_id, "New Chat")
    )
    conn.commit()


def get_all_chats():
    """
    Get all saved chats
    """

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT thread_id, chat_name
        FROM chats
        ORDER BY rowid DESC
        """
    )
    return cursor.fetchall()


def rename_chat(thread_id, new_name):
    """
    Rename existing chat
    """

    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE chats
        SET chat_name=?
        WHERE thread_id=?
        """,
        (new_name, thread_id)
    )
    conn.commit()


def delete_chat(thread_id):
    """
    Delete chat record
    """

    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM chats
        WHERE thread_id=?
        """,
        (thread_id,)
    )
    conn.commit()


def show_tables():
    """
    Debug database tables
    """

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        """
    )
    return cursor.fetchall()