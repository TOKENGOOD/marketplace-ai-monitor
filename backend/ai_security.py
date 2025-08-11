import os, json, math
from datetime import datetime

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

PROMPT = """You are a marketplace fraud and relevance evaluator.
Score security from 0-100 (100 safest, 0 scam) and decide accept/reject.
Be concise. Return ONLY JSON with these keys:
{
  "security_score": <0-100 integer>,
  "relevant": true/false,
  "reasons": ["short, crisp", "..."],
  "final_decision": "accept" | "reject"
}

User needs (profile rules): {profile_rules}

Listing:
- Title: {title}
- Price: £{price}
- Profile name: {profile_name}
- Notes: {notes}
- Description (if any): {description}
- Photos: {photos_count}
- Seller signals: {seller_signals}
"""

def _heuristic(profile: dict, item: dict) -> dict:
    # Fallback when OPENAI_API_KEY is not set
    title = (item.get("title") or "").lower()
    kws = [k.strip().lower() for k in (profile.get("keywords") or "").split(",") if k.strip()]
    hit_ratio = (sum(1 for k in kws if k in title) / max(1, len(kws))) if kws else 0.0
    price = (item.get("price_cents") or 0)/100
    mn = (profile.get("price_min_cents") or 0)/100
    mx = (profile.get("price_max_cents") or 10**9)/100
    in_range = 1.0 if (price >= mn and price <= mx) else 0.0
    # Simple blend -> 0..100
    score = int(round((0.6*in_range + 0.4*hit_ratio) * 30 + 70))  # mostly >=70 when both ok
    score = max(0, min(100, score))
    decision = "accept" if score >= 70 else "reject"
    return {
        "security_score": score,
        "relevant": hit_ratio > 0,
        "reasons": [
            f"{sum(1 for k in kws if k in title)}/{len(kws)} keywords matched" if kws else "no keywords configured",
            "price within desired range" if in_range else "price outside range"
        ],
        "final_decision": decision
    }

def evaluate_listing(profile: dict, item: dict) -> dict:
    if not OPENAI_API_KEY:
        return _heuristic(profile, item)
    try:
        # Lazy import to avoid dependency if user hasn't installed openai
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = PROMPT.format(
            profile_rules=profile.get("keywords") or "(no rules)",
            title=item.get("title",""),
            price=(item.get("price_cents") or 0)/100,
            profile_name=profile.get("name",""),
            notes=item.get("reason",""),
            description=item.get("description",""),
            photos_count=item.get("photos_count", 0),
            seller_signals=item.get("seller_meta","{}")
        )
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL","gpt-4o-mini"),
            messages=[{"role":"system","content":"You return strict JSON."},
                      {"role":"user","content": prompt}],
            max_tokens=120, temperature=0
        )
        txt = resp.choices[0].message.content.strip()
        data = json.loads(txt)
        # Sanity clamp
        data["security_score"] = int(max(0, min(100, int(data.get("security_score", 0)))))
        if data["security_score"] >= 70 and data.get("final_decision") == "reject":
            # Align decision with score unless model insists
            data["final_decision"] = "accept"
        return data
    except Exception as e:
        # On any error, fallback heuristic
        return _heuristic(profile, item)
