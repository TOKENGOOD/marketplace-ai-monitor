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

def main():
    load_dotenv()
    init_db()
    items = fetch_mock_results()
    profiles = list_profiles()
    if not profiles:
        print("No profiles yet. Open the web UI to add some: {}/".format(BASE_URL))
        return

    for profile in profiles:
        print(f"Processing profile: {profile.get('name')}")
        for it in items:
            # First, simple keyword score (legacy field)
            score, reason = score_item(it, profile)
            it["score"] = score
            it["reason"] = reason

            # AI / heuristic security scoring
            ai = evaluate_listing(profile, it)
            sec = ai.get("security_score", 0)
            decision = ai.get("final_decision", "reject")
            it["security_score"] = sec
            it["ai_model"] = os.getenv("OPENAI_MODEL") if os.getenv("OPENAI_API_KEY") else "heuristic"
            it["ai_reasons"] = "; ".join(ai.get("reasons", []))
            it["status"] = "accepted" if (decision == "accept" and sec >= 70) else "rejected"

            # Store and get id
            item_id = upsert_listing(it, profile.get("name"))

            if it["status"] == "accepted":
                # Include link to item page on our site + direct FB link
                site_link = f"{BASE_URL}/item/{item_id}" if item_id else BASE_URL
                suffix = f"[{badge_text(sec)} — {sec}/100]"
                result = send_item(it, profile, site_link=site_link, reason=suffix)
                # Our notify function does not include the site_link; send second line as reason
                if result is True:
                    print(f"  Sent: {it['title']} {score:.2f} — {sec}/100")
                elif result is None:
                    print(f"  Skipped (Telegram not configured): {it['title']} {score:.2f} — {sec}/100")
                else:
                    print(f"  Failed to send Telegram: {it['title']} {score:.2f} — {sec}/100")
            else:
                print(f"  Rejected (<70): {it['title']} — {sec}/100")

if __name__ == "__main__":
    main()
