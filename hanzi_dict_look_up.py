# hanzi_dict_look_up.py
# Final version with dictionary_search for real multi-char compounds + tone mark conversion

import requests
import re
import time
from hanzipy.dictionary import HanziDictionary

# -------------------------- CONFIG --------------------------
TAG = "Chinese_Shared_Deck"
HANZI_FIELD = "Hanzi"
TARGET_FIELD = "PyScriptLookUp"
ANKICONNECT_URL = "http://localhost:8765"

TEST_MODE = False          # ← Set to False for full run
REQUEST_TIMEOUT = 60
MAX_RETRIES = 3
# -----------------------------------------------------------

dictionary = HanziDictionary()

# Pure Python numbered pinyin to tone marks converter
def convert_to_tone_marks(pinyin_str):
    if not pinyin_str:
        return "N/A"
    tone_map = {
        '1': ('ā', 'ō', 'ē', 'ī', 'ū', 'ǖ'),
        '2': ('á', 'ó', 'é', 'í', 'ú', 'ǘ'),
        '3': ('ǎ', 'ǒ', 'ě', 'ǐ', 'ǔ', 'ǚ'),
        '4': ('à', 'ò', 'è', 'ì', 'ù', 'ǜ'),
    }
    vowel_order = "aoeiuvü"
    result = []
    for syllable in pinyin_str.lower().split():
        if syllable and syllable[-1].isdigit():
            tone = syllable[-1]
            base = syllable[:-1]
        else:
            tone = '0'
            base = syllable
        if tone == '0' or tone == '5':
            result.append(base)
            continue
        pos = -1
        marked_vowel = base
        for v in vowel_order:
            if v in base:
                pos = base.rfind(v)
                replacement = tone_map.get(tone, ('a', 'o', 'e', 'i', 'u', 'ü'))[vowel_order.index(v)]
                if v == 'ü':
                    base = base.replace('ü', 'v')
                marked_vowel = base[:pos] + replacement + base[pos+1:]
                marked_vowel = marked_vowel.replace('v', 'ü')
                break
        result.append(marked_vowel)
    return " ".join(result)

def invoke(action, **params):
    payload = {"action": action, "version": 6, "params": params}
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(ANKICONNECT_URL, json=payload, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            result = response.json()
            if result.get("error") is not None:
                raise Exception(result["error"])
            return result["result"]
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"  ⚠️  Retry {attempt+2}/{MAX_RETRIES}: {e}")
                time.sleep(5)
            else:
                raise Exception(f"Failed after {MAX_RETRIES} attempts: {e}")

def generate_breakdown(text):
    if not text:
        return ""
    
    hanzi_list = re.findall(r'[\u4e00-\u9fff]', text)
    unique_hanzi = []
    seen = set()
    for h in hanzi_list:
        if h not in seen:
            unique_hanzi.append(h)
            seen.add(h)
    
    parts = []
    for i, char in enumerate(unique_hanzi):
        # Single char pinyin with tone marks
        pinyins_num = dictionary.get_pinyin(char)
        pinyin_str = " / ".join(convert_to_tone_marks(py) for py in pinyins_num) if pinyins_num else "N/A"
        
        # Primary definition
        entries = dictionary.definition_lookup(char)
        def_str = "no entry"
        if entries:
            full_def = entries[0].get('english') or entries[0].get('definition', '')
            if full_def:
                full_def = re.sub(r'\[.*?\]', '', full_def).strip()
                def_str = re.split(r'[/;]', full_def)[0].strip()
        
        parts.append('<div class="char-block">')
        parts.append(f'<span class="bigchar">{char}</span>')
        parts.append(f'<span class="pinyin">({pinyin_str})</span>')
        parts.append(f'<span class="def">{def_str}</span>')
        
        # Multi-char compounds via dictionary_search
        search_results = dictionary.dictionary_search(char)
        compounds = [e for e in search_results if len(e['simplified']) > 1]
        compounds.sort(key=lambda e: len(e['simplified']))  # shorter = more common
        top_compounds = compounds[:3]
        
        if top_compounds:
            parts.append('<span class="ex-label">Common words:</span>')
            for e in top_compounds:
                word = e['simplified']
                numbered_py = e['pinyin']
                toned_py = convert_to_tone_marks(numbered_py)
                full_eng = e.get('english', '') or e.get('definition', '')
                cleaned = re.sub(r'\[.*?\]', '', full_eng)
                short_meaning = re.split(r'[/;]', cleaned)[0].strip().split()[0].capitalize() if cleaned else "common"
                parts.append(f'<div class="example">• {word} ({toned_py}): {short_meaning}</div>')
        
        parts.append('</div>')
        
        if i < len(unique_hanzi) - 1:
            parts.append('<hr class="sep">')
    
    return "\n".join(parts)

def main():
    print("Starting character breakdown fill (dictionary_search + tone marks)...")
    print(f"Tag: {TAG} | Source: {HANZI_FIELD} → Target: {TARGET_FIELD}")
    if TEST_MODE:
        print("🧪 TEST MODE ACTIVE: Updating only the FIRST note")
    print("-" * 60)
    
    try:
        note_ids = invoke("findNotes", query=f'tag:{TAG}')
    except Exception as e:
        print(f"❌ Failed to find notes: {e}")
        return
    
    if not note_ids:
        print("No notes found with the tag")
        return
    
    print(f"Found {len(note_ids)} notes")
    
    if TEST_MODE:
        note_ids = note_ids[:1]
        print(f"🧪 Processing only note ID: {note_ids[0]}")
    
    try:
        notes_info = invoke("notesInfo", notes=note_ids)
    except Exception as e:
        print(f"❌ Failed to get note info: {e}")
        return
    
    updated = 0
    for info in notes_info:
        fields = info["fields"]
        note_id = info["noteId"]
        
        hanzi_text = fields.get(HANZI_FIELD, {}).get("value", "").strip()
        if not hanzi_text:
            print(f"Note {note_id}: empty Hanzi → skip")
            continue
        
        if fields.get(TARGET_FIELD, {}).get("value", "").strip():
            print(f"Note {note_id}: already filled → skip")
            continue
        
        print(f"Note {note_id}: Generating for \"{hanzi_text}\"")
        
        html = generate_breakdown(hanzi_text)
        if not html:
            print("  No content generated")
            continue
        
        update_payload = {
            "note": {
                "id": note_id,
                "fields": {TARGET_FIELD: html}
            }
        }
        
        print(f"Updating note {note_id}...")
        try:
            invoke("updateNoteFields", **update_payload)
            print(f"✅ Successfully updated note {note_id}")
            updated += 1
        except Exception as e:
            print(f"❌ Update failed: {e}")
    
    print(f"Done! {updated} note(s) updated. Check your test card — real multi-char compounds now!")

if __name__ == "__main__":
    main()