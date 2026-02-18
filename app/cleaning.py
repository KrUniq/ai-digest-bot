import re

SERVICE_LINE_PATTERNS = [
    r"^\s*дайджест\s*:\s*$",
    r"^\s*summary\s*:\s*$",
    r"^\s*обсуждение\s*:\s*$",
    r"^\s*digest\s*:\s*$",
    r"^\s*key facts\s*:\s*$",
    r"^\s*topics\s*:\s*$",
]

def is_service_line(line: str) -> bool:
    l = line.strip().lower()
    return any(re.match(p, l, flags=re.IGNORECASE) for p in SERVICE_LINE_PATTERNS)

def strip_bad_latin_inside_ru(line: str) -> str:
    """
    Remove random latin words inside Russian text like 'concert', 'Maslennitsa'.
    Keep short Titlecase tokens like 'Ozon', 'Louis' (<= 6 chars).
    """
    tokens = line.split()
    out = []
    for t in tokens:
        core = re.sub(r"^[\(\[\{«\"'“”]+|[\)\]\}»\"'“”\.\,\!\?\:\;]+$", "", t)
        if re.fullmatch(r"[A-Za-z]+", core):
            if len(core) <= 6 and core[0].isupper() and core[1:].islower():
                out.append(t)
                continue
            continue
        out.append(t)
    return " ".join(out)

def cleanup_output(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]{2,}", " ", text).strip()

    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    # one-line bullets -> split on "— "
    if len(lines) == 1 and "— " in lines[0]:
        parts = lines[0].split("— ")
        lines = ["— " + p.strip() for p in parts if p.strip()]

    cleaned = []
    for ln in lines:
        ln = re.sub(r"^\s*—\s*", "— ", ln.strip())
        if is_service_line(ln):
            continue
        if re.match(r"^—\s*(дайджест|summary|обсуждение)\s*:\s*$", ln, flags=re.IGNORECASE):
            continue
        cleaned.append(ln)

    topics_line = None
    kept = []
    for ln in cleaned:
        if re.match(r"^(темы|topics)\s*:\s*", ln, flags=re.IGNORECASE):
            topics_line = re.sub(r"^topics\s*:\s*", "Темы: ", ln, flags=re.IGNORECASE).strip()
            continue
        kept.append(ln)

    merged = []
    for ln in kept:
        if ln.startswith("— "):
            merged.append(ln)
        else:
            if merged:
                merged[-1] = merged[-1].rstrip() + " " + ln
            else:
                merged.append("— " + ln)

    merged = [strip_bad_latin_inside_ru(b) for b in merged]

    def fix_line(s: str) -> str:
        s = re.sub(r"\s{2,}", " ", s).strip()
        s = re.sub(r"\s+\.$", ".", s)
        s = re.sub(r"\(\s*\)", "", s)
        s = s.replace("В также", "Также")
        s = s.replace("В вкусе", "Во вкусе")
        return s.strip()

    merged = [fix_line(b) for b in merged]
    merged = [b for b in merged if b.strip() not in ("—", "— .", "— ,")]
    merged = [b for b in merged if not re.search(r"\bразличн\w*\s*\.\s*$", b.lower())]

    out = "\n".join(merged).strip()
    if topics_line:
        out = (out + "\n" + topics_line).strip()

    return out
