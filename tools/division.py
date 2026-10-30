import os
from typing import Optional, Any
import re
from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

_DIVISIONS_CACHE: Optional[list] = None
_EMPLOYEES_CACHE: Optional[list] = None
_EMPLOYEES_CACHE_TS: float = 0.0

def _get_cached_employees(ttl: float = 60.0) -> list:
    from aria_agent.services.request_read_cache import cached_read
    res = cached_read("/api/employees", lambda: make_request("/api/employees"))
    return res if isinstance(res, list) else []

def _populate_divisions_cache():
    from aria_agent.services.request_read_cache import cached_read
    try:
        res = cached_read("/api/divisions", lambda: make_request("/api/divisions", is_chat_metadata=True, timeout=2.0))
        return res if isinstance(res, list) else []
    except Exception:
        return []

def resolve_division_code(div_val: Any) -> Optional[int]:
    """Dynamically resolves any division representation (numeric code, short acronym, or name)
    to its canonical numeric divisioncode from the live database schema. Thread-safe and in-memory cached.
    """
    if div_val is None:
        return None
    s = str(div_val).strip()
    divs = get_all_divisions_cached()
    if not divs:
        return None

    if s.isdigit():
        val = int(s)
        # Prevent 4-digit calendar years (e.g. 2017, 2025) from ever being treated as a division code
        if 1900 <= val <= 2100:
            return None
        valid_codes = {int(d["divisioncode"]) for d in divs if d.get("divisioncode") is not None and str(d.get("divisioncode")).isdigit()}
        if val in valid_codes:
            return val
        return None

    s_clean = s.lower().replace("division", "").strip()

    # 1. Exact match on shCode or full division name
    for d in divs:
        sh = str(d.get("shCode") or "").strip().lower()
        dname = str(d.get("division") or "").strip().lower()
        if s.lower() == sh or s.lower() == dname or s_clean == dname.replace("division", "").strip():
            return d.get("divisioncode")

    # 2. Acronym matching (e.g. 'IT' matches 'ITD' or initials of multi-word division names)
    for d in divs:
        sh = str(d.get("shCode") or "").strip().lower()
        dname = str(d.get("division") or "").strip().lower()
        if len(s_clean) >= 2 and (s_clean == sh or (sh.endswith("d") and s_clean == sh[:-1])):
            return d.get("divisioncode")
        words = [w for w in re.findall(r"[a-zA-Z]+", dname) if w != "division"]
        if len(words) >= 2:
            initials = "".join(w[0] for w in words).lower()
            if s_clean == initials:
                return d.get("divisioncode")

    # 3. Stemmed token matching (require tokens >= 4 chars to prevent arbitrary acronym false positives)
    s_tokens = set(re.findall(r"[a-zA-Z]+", s_clean))
    if s_tokens and all(len(st) >= 4 for st in s_tokens):
        for d in divs:
            dname = str(d.get("division") or "").strip().lower()
            d_tokens = set(re.findall(r"[a-zA-Z]+", dname))
            if all(any(dt.startswith(st[:4]) or st.startswith(dt[:4]) for dt in d_tokens if len(dt) >= 4) for st in s_tokens):
                return d.get("divisioncode")

    # 4. Consonant / disemvoweling abbreviation match (e.g. 'spc' matches 'space' words)
    if len(s_clean) >= 3 and s_clean.isalpha():
        s_consonants = "".join(c for c in s_clean if c not in "aeiou")
        if len(s_consonants) >= 3:
            for d in divs:
                dname = str(d.get("division") or "").strip().lower()
                for w in re.findall(r"[a-zA-Z]{4,}", dname):
                    w_consonants = "".join(c for c in w if c not in "aeiou")
                    if w_consonants.startswith(s_consonants) or s_consonants == w_consonants[:len(s_consonants)]:
                        return d.get("divisioncode")

    return None


def get_all_divisions_cached() -> list:
    """Returns cached list of all division records from GET /api/divisions."""
    return _populate_divisions_cache()


def get_division_by_code(div_val: Any) -> Optional[dict]:
    """Returns the full division dictionary for a given numeric code, short acronym, or name."""
    code = resolve_division_code(div_val)
    if code is None:
        return None
    for d in get_all_divisions_cached():
        if d.get("divisioncode") == code:
            return d
    return None


def resolve_all_divisions_from_prompt(prompt: str) -> list:
    """Dynamically detects ALL institutional divisions from GET /api/divisions
    referenced in the user prompt. Returns a deduplicated list of matching division dictionaries.
    Uses universal master data dimension resolver with word-claiming exact matches to prevent token bleeding.
    Zero hardcoded division names or vocabulary.
    """
    if not prompt or not isinstance(prompt, str):
        return []
    try:
        from aria_agent.services.master_data_discovery import UNIVERSAL_DIMENSION_REGISTRY
        dim = UNIVERSAL_DIMENSION_REGISTRY.get("division") or UNIVERSAL_DIMENSION_REGISTRY.get("divisions")
        if dim and dim.records:
            return dim.resolve_entities_from_prompt(prompt)
    except Exception:
        pass

    p_lower = prompt.lower()
    divs = get_all_divisions_cached()
    if not divs:
        return []

    sorted_divs = sorted(divs, key=lambda d: len(str(d.get("division") or "")), reverse=True)
    matched: list = []
    matched_codes = set()

    exact_matched_words: set = set()

    def _add_match(d_item, is_exact: bool = False):
        c = d_item.get("divisioncode")
        if c not in matched_codes:
            matched_codes.add(c)
            matched.append(d_item)
            if is_exact:
                dname = str(d_item.get("division") or "").strip().lower()
                core_name = dname.replace("division", "").strip()
                exact_matched_words.update(re.findall(r'\b[a-zA-Z]{4,}\b', core_name or dname))
                sh = str(d_item.get("shCode") or "").strip().lower()
                if sh:
                    exact_matched_words.add(sh)

    # 1. Exact phrase match on full division name
    for d in sorted_divs:
        dname = str(d.get("division") or "").strip().lower()
        if dname and dname in p_lower:
            _add_match(d, is_exact=True)

    # 2. Match short acronym if present as a distinct word boundary (e.g. 'ITD', 'COM')
    for d in sorted_divs:
        sh = str(d.get("shCode") or "").strip().lower()
        if sh and len(sh) >= 2:
            if re.search(r'\b' + re.escape(sh) + r'\b', p_lower):
                _add_match(d, is_exact=True)

    # 3. Match division core name without 'division' (e.g. 'Information Technology', 'Space Technology')
    for d in sorted_divs:
        dname = str(d.get("division") or "").strip().lower()
        core_name = dname.replace("division", "").strip()
        if core_name and len(core_name) >= 4 and core_name in p_lower:
            _add_match(d, is_exact=True)

    # 4. Contextual short acronym match when accompanying words like 'division', 'divisions', 'dept', 'projects' exist
    has_div_context = any(w in p_lower for w in ("division", "divisions", "dept", "department", "unit", "projects", "hod", "head"))
    if has_div_context:
        for d in sorted_divs:
            sh = str(d.get("shCode") or "").strip().lower()
            if sh and len(sh) >= 3 and sh.endswith("d"):
                acronym = sh[:-1]
                if len(acronym) >= 2:
                    # Require explicit structural proximity or conjunction to prevent English pronouns like 'tell me' matching Media Division ('me')
                    pattern = (
                        r'\b' + re.escape(acronym) + r'\s+(?:division|divisions|dept|department)\b|'
                        r'\b(?:division|divisions|dept|department)\s+(?:of\s+)?' + re.escape(acronym) + r'\b|'
                        r'\b' + re.escape(acronym) + r'\s+(?:and|or|&)\s+\w+\s+(?:division|divisions)\b|'
                        r'\b\w+\s+(?:and|or|&)\s+' + re.escape(acronym) + r'\s+(?:division|divisions)\b'
                    )
                    if re.search(pattern, p_lower):
                        _add_match(d, is_exact=True)

    # 5. Distinctive keyword token match (e.g. 'space' matches 'Space Technology' and 'Space Applications Division')
    # Fully dynamic: checks non-generic prompt words against division name tokens
    generic_stopwords = {
        "about", "tell", "show", "what", "which", "give", "list", "division", "divisions",
        "dept", "department", "departments", "please", "there", "multiple", "with", "name",
        "them", "also", "well", "more", "info", "overview", "detail", "details"
    }
    prompt_tokens = {w for w in re.findall(r'\b[a-zA-Z]{4,}\b', p_lower) if w not in generic_stopwords}
    # Exclude tokens already consumed by exact division matches so shared words don't bleed into other divisions
    remaining_tokens = prompt_tokens - exact_matched_words
    if remaining_tokens:
        for d in sorted_divs:
            if d.get("divisioncode") in matched_codes:
                continue
            dname = str(d.get("division") or "").strip().lower()
            d_words = {w for w in re.findall(r'\b[a-zA-Z]{4,}\b', dname) if w not in ("division", "divisions", "department")}
            if remaining_tokens & d_words or any(
                pt.startswith(dw[:4]) or dw.startswith(pt[:4])
                for pt in remaining_tokens for dw in d_words
                if len(pt) >= 4 and len(dw) >= 4
            ):
                _add_match(d)

    # 6. Consonant / disemvoweling abbreviation token match (e.g. 'spc' matches 'space' divisions)
    if not matched or remaining_tokens:
        prompt_short_words = set(re.findall(r'\b[a-zA-Z]{3}\b', p_lower)) - {
            "and", "the", "for", "are", "not", "but", "all", "who", "why", "how", "can", "may",
            "did", "see", "get", "has", "had", "was", "any", "out", "our", "day", "one", "two"
        }
        for sw in prompt_short_words:
            sw_consonants = "".join(c for c in sw if c not in "aeiou")
            if len(sw_consonants) >= 3:
                for d in sorted_divs:
                    if d.get("divisioncode") in matched_codes:
                        continue
                    dname = str(d.get("division") or "").strip().lower()
                    for w in re.findall(r"[a-zA-Z]{4,}", dname):
                        w_consonants = "".join(c for c in w if c not in "aeiou")
                        if w_consonants.startswith(sw_consonants):
                            _add_match(d)

    return matched


def resolve_division_from_prompt(prompt: str) -> Optional[dict]:
    """Dynamically detects whether any institutional division from GET /api/divisions
    is referenced in the user prompt. Returns the division dictionary if matched, else None.
    Zero hardcoded division names or vocabulary.
    """
    matches = resolve_all_divisions_from_prompt(prompt)
    return matches[0] if matches else None

@tool
def fetchAllDivisions() -> list:
    """Retrieves all institute division records from GET /api/divisions.

    JSON fields returned per record:
    - divisioncode (int): Primary numeric division identifier [FOREIGN KEY].
    - division (str): Full division name.
    - shCode / sh_code (str): Division short acronym/code (e.g. 'COM', 'DIR', 'ADM', 'ITD', 'ELE').
    - hod (int): Employee number (empno) of Head of Division [FOREIGN KEY].
    - ddg (int): Employee number (empno) of Deputy Director General [FOREIGN KEY].
    - dg (int): Employee number (empno) of Director General [FOREIGN KEY].
    Maps to GET /api/divisions."""
    return make_request("/api/divisions")

@tool
def fetchDivisionByCode(divisioncode: int) -> dict:
    """Retrieves division details by numeric primary division code (divisioncode) from GET /api/divisions.
    JSON fields returned: divisioncode [PK/FK], division (division name), shCode, hod [FK], ddg [FK], dg [FK].
    Maps to GET /api/divisions/{divisioncode}."""
    if not divisioncode:
        return {"error": "divisioncode cannot be empty"}
    return make_request(f"/api/divisions/{clean_id(divisioncode)}")

@tool
def fetchDivisionByShortCode(shCode: str) -> dict:
    """Retrieves division details by short code/acronym (shCode, e.g. 'COM', 'ITD', 'IT', 'ELE', 'STD', 'STA', 'SPC') from GET /api/divisions.
    Automatically resolves acronyms to canonical division identifiers.
    JSON fields returned: divisioncode, division, shCode, hod, headOfDivision (name, designation, email), ddg, dg.
    Maps to GET /api/divisions/shcode/{shCode} and GET /api/divisions/{code}."""
    if not shCode or not str(shCode).strip():
        return {"error": "shCode cannot be empty"}
    clean_val = str(shCode).strip()
    code_int = resolve_division_code(clean_val)
    if code_int is not None:
        res = make_request(f"/api/divisions/{code_int}")
        if isinstance(res, dict) and "error" not in res:
            return res
    res = make_request(f"/api/divisions/shcode/{clean_val}")
    if isinstance(res, dict) and "error" not in res:
        return res
    matched = resolve_all_divisions_from_prompt(clean_val)
    if matched:
        res = make_request(f"/api/divisions/{matched[0].get('divisioncode')}")
        if isinstance(res, dict) and "error" not in res:
            return res
    return {"error": f"Division with code/acronym '{clean_val}' not found."}

@tool
def fetchDivisionByName(name: str) -> dict:
    """Retrieves division details by full or partial division name (e.g. 'Information Technology Division', 'Communication Division', 'Space Applications Division') from GET /api/divisions.
    Automatically resolves names to canonical division identifiers.
    JSON fields returned: divisioncode, division, shCode, hod, headOfDivision, ddg, dg.
    Maps to GET /api/divisions/name/{name} and GET /api/divisions/{code}."""
    if not name or not str(name).strip():
        return {"error": "Division name cannot be empty"}
    clean_name = str(name).strip()
    code_int = resolve_division_code(clean_name)
    if code_int is not None:
        res = make_request(f"/api/divisions/{code_int}")
        if isinstance(res, dict) and "error" not in res:
            return res
    matched = resolve_all_divisions_from_prompt(clean_name)
    if matched:
        res = make_request(f"/api/divisions/{matched[0].get('divisioncode')}")
        if isinstance(res, dict) and "error" not in res:
            return res
    res = make_request(f"/api/divisions/name/{clean_name}")
    if isinstance(res, dict) and "error" not in res:
        return res
    return {"error": f"Division '{clean_name}' not found."}

@tool
def fetchDivisionsByHod(hodEmpno: int) -> list:
    """Retrieves division records led by a specific Head of Division (HOD) using their employee number (empno).
    Arguments & Foreign Key:
    - hodEmpno (int) [FOREIGN KEY]: Employee number linking to 'empno' in 'employee'.
    JSON fields returned: divisioncode [FK], division, shCode, hod [FK], ddg [FK], dg [FK].
    Maps to GET /api/divisions/hod/{hodEmpno}."""
    return make_request(f"/api/divisions/hod/{clean_id(hodEmpno)}")

def _build_single_division_summary(div_info: dict, all_emp: Optional[list] = None) -> dict:
    """Constructs a comprehensive 360 overview for a single division record."""
    if all_emp is None:
        all_emp = _get_cached_employees()

    eff_code = div_info.get("divisioncode")
    staff_info = []
    if isinstance(all_emp, list) and eff_code is not None:
        staff_info = [
            r for r in all_emp
            if isinstance(r, dict) and (
                r.get("divisioncode") == eff_code
                or str(r.get("divisioncode") or "") == str(eff_code)
                or (isinstance(r.get("division"), dict) and r.get("division", {}).get("divisioncode") == eff_code)
            )
        ]

    proj_info = make_request(f"/api/pr-projects/division/{eff_code}") if eff_code else []

    staff_recs = staff_info if isinstance(staff_info, list) else []
    proj_recs = proj_info if isinstance(proj_info, list) else []

    if proj_recs:
        from aria_agent.utils.record_utils import sort_records_chronologically
        proj_recs = sort_records_chronologically(proj_recs)

    sample_projects = []
    for p in proj_recs[:10]:
        if isinstance(p, dict):
            p_name = p.get("projectname") or p.get("pname") or p.get("title") or p.get("name")
            p_code = p.get("apCode") or p.get("projectCode") or p.get("id") or ""
            p_year = p.get("year") or p.get("startdate") or ""
            p_type = p.get("ptype") or p.get("type") or ""
            if p_name:
                sample_projects.append({
                    "code": str(p_code),
                    "name": str(p_name),
                    "year": str(p_year)[:4] if p_year else "",
                    "type": str(p_type)
                })

    from aria_agent.utils.record_utils import extract_record_name

    sample_staff = []
    def _staff_priority_key(s):
        st = str(s.get("status") or "").upper()
        is_active = 0 if st in ("C", "AC", "ACTIVE") else 1
        return (is_active, str(extract_record_name(s) or ""))

    sorted_staff = sorted([s for s in staff_recs if isinstance(s, dict)], key=_staff_priority_key)
    for s in sorted_staff[:8]:
        s_name = extract_record_name(s)
        desig_raw = s.get("designation")
        s_desig = desig_raw.get("designation") if isinstance(desig_raw, dict) else (desig_raw or s.get("desig") or "")
        s_status = str(s.get("status") or "").upper()
        status_label = "Active" if s_status in ("C", "AC", "ACTIVE") else ("Retired" if s_status == "RT" else ("Resigned" if s_status == "RS" else (s_status or "Active")))
        s_email = s.get("email") or ""
        if s_name:
            sample_staff.append({
                "name": str(s_name).strip(),
                "designation": str(s_desig).strip(),
                "status": status_label,
                "email": str(s_email).strip() if s_email else ""
            })

    active_cnt = sum(1 for s in staff_recs if isinstance(s, dict) and str(s.get("status") or "").upper() in ("C", "AC", "ACTIVE"))

    hod_obj = div_info.get("headOfDivision") if isinstance(div_info.get("headOfDivision"), dict) else {}
    ddg_obj = div_info.get("deputyDirectorGeneral") if isinstance(div_info.get("deputyDirectorGeneral"), dict) else {}
    dg_obj = div_info.get("directorGeneral") if isinstance(div_info.get("directorGeneral"), dict) else {}

    hod_empno = div_info.get("hod") or (hod_obj.get("empno") if hod_obj else None)
    hod_name = hod_obj.get("fullname") if hod_obj else None
    if not hod_name and hod_empno and isinstance(all_emp, list):
        hod_emp = next((e for e in all_emp if isinstance(e, dict) and (e.get("empNo") == hod_empno or e.get("empno") == hod_empno)), None)
        if hod_emp:
            hod_name = extract_record_name(hod_emp)
            if not hod_obj:
                hod_obj = {
                    "name": hod_name,
                    "title": hod_emp.get("title"),
                    "email": hod_emp.get("email"),
                    "empno": hod_empno,
                    "mobile": hod_emp.get("mobileno")
                }

    return {
        "divisioncode": eff_code,
        "division": str(div_info.get("division") or "").strip(),
        "shCode": str(div_info.get("shCode") or "").strip(),
        "leadership": {
            "headOfDivision": {
                "name": hod_name or hod_obj.get("fullname"),
                "title": hod_obj.get("title"),
                "email": hod_obj.get("email"),
                "empno": hod_empno,
                "mobile": hod_obj.get("mobileno")
            } if (hod_obj or hod_name) else {"empno": hod_empno},
            "deputyDirectorGeneral": ddg_obj.get("fullname") if ddg_obj else div_info.get("ddg"),
            "directorGeneral": dg_obj.get("fullname") if dg_obj else div_info.get("dg")
        },
        "total_staff_count": len(staff_recs),
        "active_staff_count": active_cnt,
        "sample_staff": sample_staff,
        "total_projects_count": len(proj_recs),
        "sample_projects": sample_projects,
        "raw_division": div_info
    }

@tool
def fetchDivisionSummary(division: str = "", divisionCode: str = "", divCode: str = "") -> Any:
    """Composite domain router tool for institute divisions.
    Retrieves complete division overview:
    1. Division identity: Official name, short acronym (shCode), numeric divisioncode.
    2. Leadership: Head of Division (HOD), Deputy Director General (DDG), and Director General (DG) with names, emails, and designations.
    3. Official staff / staffing headcount in the division, including key active personnel.
    4. Technical & institutional research projects (PR projects) managed by the division, including project count and notable flagship initiatives.
    Accepts division name, abbreviation, or numeric code (e.g. 'IT', 'ITD', 'COM', 'Communication', 'Electronics', 'Space', 'Admin', 9, 5, 11, 7).
    When multiple divisions match an umbrella category (e.g. 'Space' matching both Space Applications and Space Technology), returns full summaries for ALL matching divisions.
    Maps to /api/divisions/{code}, /api/employees, and /api/pr-projects/division/{code}.
    """
    raw_code = str(divCode or divisionCode or "").strip()
    target = str(division or "").strip() or raw_code
    target_clean = str(target or raw_code).strip()
    if not target and not raw_code:
        return {"error": "Please provide a division name, abbreviation, or code (e.g. 'IT', 'COM', 9)."}

    matching_divs = []
    # If caller explicitly passed a numeric code or short code in divCode/divisionCode, or target is pure digits:
    code_cand = raw_code or (target if target.isdigit() else "")
    if code_cand:
        code_int = resolve_division_code(code_cand)
        if code_int is not None:
            exact_d = next((d for d in get_all_divisions_cached() if d.get("divisioncode") == code_int), None)
            if exact_d:
                matching_divs = [exact_d]

    if not matching_divs:
        target_clean = str(target or raw_code).strip()
        exact_sh = next((d for d in get_all_divisions_cached() if str(d.get("shCode") or "").strip().lower() == target_clean.lower()), None)
        if exact_sh:
            matching_divs = [exact_sh]
        else:
            all_matched = resolve_all_divisions_from_prompt(target_clean)
            if all_matched:
                matching_divs = all_matched
            else:
                code_int = resolve_division_code(target_clean)
                if code_int is not None:
                    d = next((d for d in get_all_divisions_cached() if d.get("divisioncode") == code_int), None)
                    matching_divs = [d] if d else []
                else:
                    matching_divs = []

    if not matching_divs:
        div_info = make_request(f"/api/divisions/shcode/{target_clean}")
        if not isinstance(div_info, dict) or "error" in div_info:
            div_info = make_request(f"/api/divisions/name/{target_clean}")
        if isinstance(div_info, dict) and "error" not in div_info:
            matching_divs = [div_info]

    if not matching_divs:
        return {"error": f"Division '{target_clean}' could not be resolved in institute records."}

    all_emp = _get_cached_employees()

    summaries = []
    for div_record in matching_divs:
        c = div_record.get("divisioncode")
        full_d = make_request(f"/api/divisions/{c}") if c else div_record
        if not isinstance(full_d, dict) or "error" in full_d:
            full_d = div_record
        s = _build_single_division_summary(full_d, all_emp)
        summaries.append(s)

    if len(summaries) == 1:
        return summaries[0]
    return summaries
