# hanzi_dict_look_up.py
# Fixed: updateNoteFields uses singular "note"
# Test mode active: updates only the first note

import requests
import json
import re
import time
from hanzipy.dictionary import HanziDictionary

# -------------------------- CONFIG --------------------------
TAG = "Chinese_Shared_Deck"
HANZI_FIELD = "Hanzi"
TARGET_FIELD = "PyScriptLookUp"
ANKICONNECT_URL = "http://localhost:8765"

TEST_MODE = True          # ← Set to False for full run later
REQUEST_TIMEOUT = 60
MAX_RETRIES = 3
# -----------------------------------------------------------

dictionary = HanziDictionary()

def invoke(action, **params):
    payload = {"action": action, "version": 6, "params": params}
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                ANKICONNECT_URL,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
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

def get_one_word_meaning(full_def):
    if not full_def:
        return "N/A"
    part = re.split(r'[/;]', full_def)[0].strip()
    words = part.split()
    return words[0].capitalize() if words else "N/A"

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
    
    # Helper to convert numbered pinyin to tone marks
    def add_tone_marks(pinyin_num):
        if not pinyin_num or 'N/A' in pinyin_num:
            return "N/A"
        # Mapping for tone marks
        marks = {"1": "̄", "2": "́", "3": "̌", "4": "̀", "5": ""}
        vowels = "aeiouüAEIOUÜ"
        tone = pinyin_num[-1]
        if tone not in "12345":
            return pinyin_num  # no tone number
        base = pinyin_num[:-1]
        mark = marks.get(tone, "")
        # Find vowel to place mark (a/e > o > i/u > ü)
        pos = -1
        for v in "aeoiuü":
            if v in base:
                pos = base.rfind(v)
                if v == 'ü':
                    base = base.replace('ü', 'v')  # temp for u:
                break
        if pos == -1:
            return base + tone
        return base[:pos] + base[pos] + mark + base[pos+1:]
    
    parts = []
    for i, char in enumerate(unique_hanzi):
        # Pinyin (numbered → with marks)
        pinyins_num = dictionary.get_pinyin(char)
        pinyins = [add_tone_marks(py) for py in pinyins_num] if pinyins_num else ["N/A"]
        pinyin_str = " / ".join(pinyins)
        
        # Primary definition (use first entry's english)
        entries = dictionary.definition_lookup(char)
        def_str = "no entry"
        if entries and 'english' in entries[0]:
            full_def = entries[0]['english']
            def_str = re.split(r'[/;]', full_def)[0].strip()
        
        parts.append('<div class="char-block">')
        parts.append(f'<span class="bigchar">{char}</span>')
        parts.append(f'<span class="pinyin">({pinyin_str})</span>')
        parts.append(f'<span class="def">{def_str}</span>')
        
        # Examples — better fallback
        try:
            examples = dictionary.get_examples(char)
            high_freq = examples.get('high_frequency', [])[:3]
            if high_freq:
                parts.append('<span class="ex-label">Common words:</span>')
                for ex in high_freq:
                    word = ex.get('simplified', 'N/A')
                    # Try to build pinyin from individual chars
                    ex_py_parts = []
                    for c in word:
                        c_py = dictionary.get_pinyin(c)
                        ex_py_parts.append(add_tone_marks(c_py[0]) if c_py else "?")
                    ex_py = " ".join(ex_py_parts)
                    # Short def fallback
                    ex_def_short = get_one_word_meaning(ex.get('english', '')) or "common"
                    parts.append(f'<div class="example">• {word} ({ex_py}): {ex_def_short}</div>')
        except Exception as e:
            print(f"  ⚠️  Examples failed for '{char}': {e}")
        
        parts.append('</div>')
        
        if i < len(unique_hanzi) - 1:
            parts.append('<hr class="sep">')
    
    return "\n".join(parts)

def main():
    print("Starting AnkiConnect character breakdown script...")
    print(f"Tag: {TAG} | Source: {HANZI_FIELD} → Target: {TARGET_FIELD}")
    if TEST_MODE:
        print("🧪 TEST MODE ACTIVE: Updating only the FIRST note found")
    print("-" * 60)
    
    try:
        note_ids = invoke("findNotes", query=f'tag:{TAG}')
    except Exception as e:
        print(f"❌ Could not find notes: {e}")
        return
    
    if not note_ids:
        print(f"No notes found with tag '{TAG}'")
        return
    
    print(f"Found {len(note_ids)} notes total.")
    
    if TEST_MODE:
        note_ids = note_ids[:1]
        print(f"🧪 Processing only note ID: {note_ids[0]}")
    
    try:
        notes_info = invoke("notesInfo", notes=note_ids)
    except Exception as e:
        print(f"❌ Failed to get note info: {e}")
        return
    
    updated_count = 0
    
    for info in notes_info:
        fields = info["fields"]
        note_id = info["noteId"]
        
        hanzi_text = fields.get(HANZI_FIELD, {}).get("value", "").strip()
        
        if not hanzi_text:
            print(f"Note {note_id}: ⚠️ empty Hanzi field → skipped")
            continue
        
        if fields.get(TARGET_FIELD, {}).get("value", "").strip():
            print(f"Note {note_id}: ⏭️ already filled → skipped")
            continue
        
        print(f"Note {note_id}: Generating for → \"{hanzi_text}\"")
        
        html = generate_breakdown(hanzi_text)
        if not html:
            print("  ⚠️ No HTML generated")
            continue
        
        # Fixed: singular "note"
        update_payload = {
            "note": {
                "id": note_id,
                "fields": {
                    TARGET_FIELD: html
                }
            }
        }
        
        print(f"Updating note {note_id}...")
        try:
            invoke("updateNoteFields", **update_payload)
            print(f"✅ SUCCESS! Note {note_id} updated.")
            updated_count += 1
        except Exception as e:
            print(f"❌ Update failed for note {note_id}: {e}")
    
    if updated_count == 0:
        print("No notes were updated.")
    else:
        print(f"✅ Done! {updated_count} note(s) successfully updated.")
        print("   Check the card in Anki to see the new breakdown!")

if __name__ == "__main__":
    main()