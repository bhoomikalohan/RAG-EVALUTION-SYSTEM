from fastapi import FastAPI, UploadFile, File, Request, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse, JSONResponse, FileResponse
from pydantic import BaseModel
from test import HybridSearcher
from typing import List, Optional
import uuid
import asyncio
import json
import os

# Additional imports for evaluation
from evaluation.eval_framework import RAGEvaluator
from evaluation.metrics import RAGMetrics
import numpy as np
from datetime import datetime
from fastapi import Query as FastAPIQuery  # To avoid clash with your Query model

app = FastAPI()

CHATS_FILE = "chats.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def load_chats():
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_chats(chats):
    with open(CHATS_FILE, 'w') as f:
        json.dump(chats, f, indent=2)

# Store chat sessions and user sessions in memory
sessions = {}
user_sessions = {}

def get_or_create_session_id(session_id: Optional[str]) -> str:
    if session_id is None:
        return str(uuid.uuid4())
    return session_id

def get_hybrid_searcher_for_session(session_id: str) -> HybridSearcher:
    """Get or create a HybridSearcher instance for a chat session"""
    if session_id not in sessions:
        searcher = HybridSearcher()
        # Create chat and store the searcher
        chat_id = searcher.create_new_chat()
        sessions[session_id] = searcher
    else:
        searcher = sessions[session_id]
        # Switch to the correct chat or create new one if needed
        if not searcher.switch_chat(session_id):
            searcher.create_new_chat()
    return sessions[session_id]

def get_or_create_user_session(user_session_id: Optional[str] = None) -> str:
    """Get existing user session ID or create a new one"""
    if user_session_id is None or user_session_id not in user_sessions:
        user_session_id = str(uuid.uuid4())
        user_sessions[user_session_id] = []  # List to store chat IDs for this user
    return user_session_id

def get_chats_for_user(user_session_id: str) -> dict:
    """Get all chats belonging to a user session in chronological order"""
    chats = load_chats()
    user_chat_ids = user_sessions.get(user_session_id, [])
    # Return chats in the order they appear in user_chat_ids to maintain chronological order
    return {chat_id: chats[chat_id] for chat_id in user_chat_ids if chat_id in chats}

def migrate_chats_to_user_sessions():
    """One-time migration function to move existing chats to user sessions"""
    chats = load_chats()
    if not chats:
        return
        
    # Create a default user session for existing chats
    default_user_id = str(uuid.uuid4())
    user_sessions[default_user_id] = list(chats.keys())
    return default_user_id

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]  # Required for FormData uploads
)

class Query(BaseModel):
    text: str
    collections: Optional[List[str]] = None

class Message(BaseModel):
    role: str
    content: str

class SaveChatRequest(BaseModel):
    session_id: str
    message: Message

def cleanup_orphaned_chats():
    """Clean up chats that don't belong to any user session"""
    chats = load_chats()
    if not chats:
        return
        
    # Get all chat IDs from user sessions
    active_chats = set()
    for session_chats in user_sessions.values():
        active_chats.update(session_chats)
    
    # Remove orphaned chats
    orphaned_chats = set(chats.keys()) - active_chats
    if orphaned_chats:
        for chat_id in orphaned_chats:
            del chats[chat_id]
        save_chats(chats)
        print(f"Cleaned up {len(orphaned_chats)} orphaned chats")

# Call cleanup on startup
@app.on_event("startup")
async def startup_event():
    default_user_id = migrate_chats_to_user_sessions()
    if default_user_id:
        print(f"Migrated existing chats to default user session: {default_user_id}")
    cleanup_orphaned_chats()

@app.post("/api/chat")
async def chat(
    query: Query,
    request: Request,
    response: Response,
    session_id: Optional[str] = Cookie(default=None),
    user_session_id: Optional[str] = Cookie(default=None)
):
    if not session_id:
        return JSONResponse(status_code=400, content={"error": "No active chat session"})
        
    # Get user session
    if not user_session_id or user_session_id not in user_sessions:
        return JSONResponse(status_code=403, content={"error": "Invalid user session"})
    
    # Verify this chat belongs to the user
    if session_id not in user_sessions[user_session_id]:
        return JSONResponse(status_code=403, content={"error": "Chat does not belong to user session"})
    
    # Set cookies
    response.set_cookie(key="session_id", value=session_id, httponly=True, samesite="lax")
    response.set_cookie(key="user_session_id", value=user_session_id, httponly=True, samesite="lax")
    
    # Save user message
    chats = load_chats()
    if session_id not in chats:
        chats[session_id] = []
    chats[session_id].append({"role": "user", "content": query.text})
    save_chats(chats)
    
    # Process query
    hybrid_searcher = get_hybrid_searcher_for_session(session_id)
    collections = query.collections or ["best_practices", "policies", "data"]
    chat_response = hybrid_searcher.process_query(query.text, collections)
    
    async def save_and_stream(response):
        accumulated_response = ""
        async for chunk in response:
            if hasattr(chunk, 'text'):
                text = chunk.text
                accumulated_response += text
            elif isinstance(chunk, dict) and 'text' in chunk:
                text = chunk['text']
                accumulated_response += text
            else:
                continue
            
            yield f"data: {json.dumps(text)}\n\n"
            await asyncio.sleep(0.5)
            
        # Save assistant response
        chats = load_chats()
        if session_id in chats:
            chats[session_id].append({"role": "assistant", "content": accumulated_response})
            save_chats(chats)
    
    return StreamingResponse(
        save_and_stream(chat_response),
        media_type='text/event-stream'
    )

@app.post("/api/new_chat")
async def new_chat(
    response: Response,
    user_session_id: Optional[str] = Cookie(default=None)
):
    # Get or create user session
    user_session_id = get_or_create_user_session(user_session_id)
    
    # Create new chat session
    chat_id = str(uuid.uuid4())
    
    # Set cookies
    response.set_cookie(key="session_id", value=chat_id, httponly=True, samesite="lax")
    response.set_cookie(key="user_session_id", value=user_session_id, httponly=True, samesite="lax")
    
    # Initialize new chat with HybridSearcher
    hybrid_searcher = HybridSearcher()
    hybrid_searcher.create_new_chat()  # Create initial chat session
    sessions[chat_id] = hybrid_searcher
    
    # Initialize chat storage
    chats = load_chats()
    chats[chat_id] = []
    save_chats(chats)
    
    # Add chat to user's session
    if user_session_id not in user_sessions:
        user_sessions[user_session_id] = []
    user_sessions[user_session_id].append(chat_id)
    
    return {"status": "ok", "session_id": chat_id, "user_session_id": user_session_id}

@app.delete("/api/chat/{chat_id}")
async def delete_chat(
    chat_id: str,
    user_session_id: Optional[str] = Cookie(default=None)
):
    # Verify user owns this chat
    user_session_id = get_or_create_user_session(user_session_id)
    if user_session_id not in user_sessions or chat_id not in user_sessions[user_session_id]:
        return JSONResponse(status_code=403, content={"error": "Unauthorized"})
    
    # Remove chat from storage
    chats = load_chats()
    if chat_id in chats:
        del chats[chat_id]
        save_chats(chats)
    
    # Remove from user session while maintaining order of remaining chats
    if chat_id in user_sessions[user_session_id]:
        user_sessions[user_session_id].remove(chat_id)
    
    # Clean up HybridSearcher instance
    if chat_id in sessions:
        searcher = sessions[chat_id]
        del sessions[chat_id]
    
    # Get updated chat list with new numbering
    user_chats = get_chats_for_user(user_session_id)
    chat_ids = list(user_chats.keys())
    chat_list = [{"id": id, "name": f"Chat {idx + 1}"} for idx, id in enumerate(chat_ids)]
    chat_list.reverse()
    
    return JSONResponse(
        content={
            "status": "ok",
            "chats": chat_list
        }
    )

@app.get("/api/chats")
async def get_chats(
    user_session_id: Optional[str] = Cookie(default=None)
):
    user_session_id = get_or_create_user_session(user_session_id)
    user_chats = get_chats_for_user(user_session_id)
    # Keep original order (oldest first) but reverse at the end for display
    chat_ids = list(user_chats.keys())
    chat_list = [{"id": id, "name": f"Chat {idx + 1}"} for idx, id in enumerate(chat_ids)]
    chat_list.reverse()  # Most recent chat first, but numbers stay sequential from oldest to newest
    
    return JSONResponse(
        content={"chats": chat_list},
        headers={"Set-Cookie": f"user_session_id={user_session_id}; HttpOnly; SameSite=Lax"}
    )

@app.get("/api/chat_history/{session_id}")
async def get_chat_history(
    session_id: str,
    user_session_id: Optional[str] = Cookie(default=None)
):
    # Verify user owns this chat
    user_session_id = get_or_create_user_session(user_session_id)
    if user_session_id not in user_sessions or session_id not in user_sessions[user_session_id]:
        return JSONResponse(status_code=403, content={"error": "Unauthorized"})
    
    chats = load_chats()
    return {"messages": chats.get(session_id, [])}

class TTSRequest(BaseModel):
    text: str

@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    try:
        # Generate unique filename
        file_name = os.path.join(UPLOAD_DIR, f"tts_{uuid.uuid4()}.wav")
        
        # Get default HybridSearcher instance
        searcher = HybridSearcher()
        
        # Generate audio file
        output_file = searcher.tts(request.text, file_name)
        
        return FileResponse(
            output_file,
            media_type="audio/wav",
            filename="speech.wav"
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"TTS generation failed: {str(e)}"}
        )

@app.post("/api/audio")
async def process_audio(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.content_type.startswith('audio/'):
            return JSONResponse(
                status_code=400,
                content={"error": f"Invalid file type: {file.content_type}. Expected audio/*"}
            )

        # Read the audio file contents
        try:
            contents = await file.read()
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={"error": f"Failed to read audio file: {str(e)}"}
            )
            
        if not contents:
            return JSONResponse(
                status_code=400,
                content={"error": "Empty audio file"}
            )

        # Get default HybridSearcher instance for speech-to-text
        searcher = HybridSearcher()
        
        # Convert speech to text
        transcript = searcher.send_audio(contents)
        
        if not transcript:
            return JSONResponse(
                status_code=422,
                content={"error": "Failed to transcribe audio - no speech detected"}
            )

        return PlainTextResponse(transcript.strip())
    except Exception as e:
        print(f"Speech-to-text error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Speech-to-text conversion failed: {str(e)}"}
        )

# -----------------------
# === Evaluation Endpoints ===
# -----------------------

evaluator = RAGEvaluator()
metrics_calculator = RAGMetrics()


@app.post("/api/evaluate")
async def run_evaluation(
    collections: Optional[List[str]] = FastAPIQuery(default=["best_practices", "policies", "data"])
):
    """
    Run evaluation on your test dataset.
    Optionally override the collections to use.
    """
    test_dataset = evaluator.load_test_dataset()
    results = []
    
    for test_case in test_dataset.get("test_cases", []):
        result = await evaluator.evaluate_single_query(
            test_case["question"],
            test_case["expected_answer"],
            collections
        )
        
        # Calculate semantic similarity
        similarity = metrics_calculator.semantic_similarity(
            result["generated_answer"],
            result["expected_answer"]
        )
        
        result["semantic_similarity"] = similarity
        results.append(result)
    
    average_similarity = np.mean([r["semantic_similarity"] for r in results]) if results else 0.0
    
    return {
        "evaluation_results": results,
        "average_similarity": average_similarity,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/evaluation/status")
async def get_evaluation_status():
    """
    Returns current system health and evaluation metadata.
    """
    # You might want to expand this with real health checks (Qdrant, DB, etc.)
    return {
        "qdrant_status": "running",   # Ideally add code to check Docker/Qdrant health
        "collections_available": ["best_practices", "policies", "data"],
        "last_evaluation": None  # You can update with a timestamp once you integrate persistent logging
    }
