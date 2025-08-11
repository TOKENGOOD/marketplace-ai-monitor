def score_item(item, profile):
    # profile keys: name, keywords (comma string), price_min_cents, price_max_cents, min_score
    title = (item.get("title") or "").lower()
    kws = [k.strip().lower() for k in (profile.get("keywords") or "").split(",") if k.strip()]
    hits = sum(1 for k in kws if k in title)
    score_kw = hits / max(1, len(kws)) if kws else 0.0

    price = item.get("price_cents") or 0
    pmin = profile.get("price_min_cents")
    pmax = profile.get("price_max_cents")
    price_ok = True
    price_reason = ""
    if pmin is not None and price < pmin:
        price_ok = False
        price_reason = f"price {price/100:.2f} < min {(pmin or 0)/100:.2f}"
    if pmax is not None and price > pmax:
        price_ok = False
        price_reason = f"price {price/100:.2f} > max {(pmax or 0)/100:.2f}"

    score = score_kw if price_ok else 0.0
    reason = f"{hits}/{len(kws)} keywords matched"
    if not price_ok:
        reason += f"; {price_reason}"
    return score, reason
