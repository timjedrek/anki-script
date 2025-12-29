# hanzi_dict_look_up.py
# Switched to 'pinyin' library for accurate CC-CEDICT data, tone marks, real defs + examples

import requests
import re
import time
import pinyin.cedict

# -------------------------- CONFIG --------------------------
TAG = "Chinese_Shared_Deck"
HANZI_FIELD = "Hanzi"
TARGET_FIELD = "PyScriptLookUp"
ANKICONNECT_URL = "http://localhost:8765"

TEST_MODE = True          # ← Set to False for full run
REQUEST_TIMEOUT = 60
MAX_RETRIES = 3
# -----------------------------------------------------------

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
        # All translations including phrases containing the char
        translations = list(pinyin.cedict.all_phrase_translations(char))
        
        if not translations:
            pinyin_str = "N/A"
            def_str = "no entry"
            example_words = []
        else:
            # Primary: the single char entry
            single_char = [t for t in translations if t[0] == char]
            if single_char:
                primary_defs = single_char[0][1]
                def_str = primary_defs[0] if primary_defs else "no entry"
                # Pinyin from phrase (for single char it's the reading)
                # Extract from known format, or fallback
                pinyin_str = "N/A"  # We'll approximate if needed
            else:
                def_str = "no entry"
                pinyin_str = "N/A"
            
            # Use pinyin.get for tone marks on the char
            char_pinyin = pinyin.get(char, delimiter=" ")
            pinyin_str = char_pinyin if char_pinyin else "N/A"
            
            # Examples: multi-char phrases containing the char
            example_words = [t for t in translations if len(t[0]) > 1][:3]
        
        parts.append('<div class="char-block">')
        parts.append(f'<span class="bigchar">{char}</span>')
        parts.append(f'<span class="pinyin">({pinyin_str})</span>')
        parts.append(f'<span class="def">{def_str}</span>')
        
        if example_words:
            parts.append('<span class="ex-label">Common words:</span>')
            for word, defs in example_words:
                ex_py = pinyin.get(word, delimiter=" ")
                ex_def_short = defs[0].split('/')[0].strip().split()[0].capitalize() if defs else "common"
                parts.append(f'<div class="example">• {word} ({ex_py}): {ex_def_short}</div>')
        
        parts.append('</div>')
        
        if i < len(unique_hanzi) - 1:
            parts.append('<hr class="sep">')
    
    return "\n".join(parts)

def main():
    print("Starting character breakdown script (pinyin.cedict version)...")
    print(f"Tag: {TAG} | Source: {HANZI_FIELD} → Target: {TARGET_FIELD}")
    if TEST_MODE:
        print("🧪 TEST MODE ACTIVE: Updating only the FIRST note")
    print("-" * 60)
    
    try:
        note_ids = invoke("findNotes", query=f'tag:{TAG}')
    except Exception as e:
        print(f"❌ Find notes failed: {e}")
        return
    
    if not note_ids:
        print("No notes found")
        return
    
    print(f"Found {len(note_ids)} notes")
    
    if TEST_MODE:
        note_ids = note_ids[:1]
        print(f"🧪 Processing note ID: {note_ids[0]}")
    
    try:
        notes_info = invoke("notesInfo", notes=note_ids)
    except Exception as e:
        print(f"❌ Get note info failed: {e}")
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
            print("  No content")
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
            print(f"✅ Updated note {note_id} successfully!")
            updated += 1
        except Exception as e:
            print(f"❌ Update failed: {e}")
    
    print(f"Done! {updated} note(s) updated. Check your test card for real defs + examples!")

if __name__ == "__main__":
    main()