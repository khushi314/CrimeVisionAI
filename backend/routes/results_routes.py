"""Session lookup, history listing, and downloadable PDF Forensic Report routes."""

from flask import Blueprint, jsonify, send_file

try:
    from backend.services.session_store import session_store
    from backend.services.report_service import generate_forensic_pdf
except ImportError:
    from services.session_store import session_store
    from services.report_service import generate_forensic_pdf

results_bp = Blueprint("results", __name__, url_prefix="/api")


@results_bp.route("/sessions", methods=["GET"])
def list_recent_sessions():
    """Return list of persisted forensic sessions."""
    return jsonify({"status": "success", "sessions": session_store.list_sessions()}), 200


@results_bp.route("/results/<session_id>", methods=["GET"])
def get_session_results(session_id: str):
    """Retrieve stored forensic JSON context for a given session ID."""
    data = session_store.get_session(session_id)
    if not data:
        return jsonify({"status": "error", "error": f"Session '{session_id}' not found."}), 404
    return jsonify({"status": "success", "session_id": session_id, "data": data}), 200


@results_bp.route("/report/<session_id>", methods=["GET"])
def download_pdf_report(session_id: str):
    """Generate and stream downloadable PDF report for `session_id`."""
    data = session_store.get_session(session_id)
    if not data:
        return jsonify({"status": "error", "error": f"Session '{session_id}' not found."}), 404

    pdf_path = generate_forensic_pdf(session_id, data)
    return send_file(
        str(pdf_path),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"CrimeVision_Forensic_Report_{session_id[:8]}.pdf",
    )
