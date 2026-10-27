"""Forensic Chatbot Blueprint (`/api/chat/<mode>`) — Grounded Q&A & Regex Time Lookup."""

from flask import Blueprint, request, jsonify

try:
    from backend.services.chat_service import query_chat
except ImportError:
    from services.chat_service import query_chat

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@chat_bp.route("/<mode>", methods=["POST"])
def chat(mode: str):
    """Query analyzed session context in `image`, `audio`, `video`, or `fusion` mode."""
    payload = request.get_json(silent=True) or {}
    session_id = payload.get("session_id", "")
    question = payload.get("question", "")

    if not session_id:
        return jsonify({"status": "error", "error": "Missing 'session_id' in chat request."}), 400
    if not question or not str(question).strip():
        return jsonify({"status": "error", "error": "Missing 'question' in chat request."}), 400

    answer = query_chat(session_id=session_id, question=str(question), mode=mode)
    return jsonify({"status": "success", "mode": mode, "answer": answer}), 200
