import os
from dotenv import load_dotenv
from db import init_db, list_profiles, upsert_listing
from scrape_mock import fetch_mock_results
from filter_simple import score_item
from notify_telegram import send_item
from ai_security import evaluate_listing

BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000")

def badge_text(score: int) -> str:
    if score >= 96: return "Safe"
    if score >= 86: return "Low risk"
    return "Scam alert"  # 70..85

def run_once():
    """Run the matching + AI scoring exactly once (no infinite loop)."""
    load_dotenv()
    init_db()
    items = fetch_mock_results()
    profiles = list_profiles()
    if not profiles:
        print("No profiles yet. Add some at {}/".format(BASE_URL))
        return {"ok": True, "processed": 0, "sent": 0}

    sent = 0
    processed = 0
    for profile in profiles:
        print(f"Processing profile: {profile.get('name')}")
        for it in items:
            processed += 1
            score, reason = score_item(it, profile)
            it["score"] = score
            it["reason"] = reason

            ai = evaluate_listing(profile, it)
            sec = int(ai.get("security_score", 0))
            decision = ai.get("final_decision", "reject")
            it["security_score"] = sec
            it["ai_model"] = os.getenv("OPENAI_MODEL") if os.getenv("OPENAI_API_KEY") else "heuristic"
            it["ai_reasons"] = "; ".join(ai.get("reasons", []))
            it["status"] = "accepted" if (decision == "accept" and sec >= 70) else "rejected"

            item_id = upsert_listing(it, profile.get("name"))
            if it["status"] == "accepted":
                res = send_item(it, profile)
                if res is True:
                    sent += 1
                    print(f"  Sent: {it['title']} {score:.2f} — {sec}/100")
                elif res is None:
                    print(f"  Skipped (Telegram not configured): {it['title']} {score:.2f} — {sec}/100")
                else:
                    print(f"  Failed to send Telegram: {it['title']} {score:.2f} — {sec}/100")
            else:
                print(f"  Rejected (<70): {it['title']} — {sec}/100")
    return {"ok": True, "processed": processed, "sent": sent}
