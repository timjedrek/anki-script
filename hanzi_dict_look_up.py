# hanzi_dict_look_up.py
# Enhanced version with detailed terminal logging for debugging 8000+ notes
# Shows progress, skips, successes, and any errors per note

import requests
import json
import re
from hanzipy.dictionary import HanziDictionary

# -------------------------- CONFIG --------------------------
TAG = "Chinese_Shared_Deck"
HANZI_FIELD = "Hanzi"
TARGET_FIELD = "PyScriptLookUp"
ANKICONNECT_URL = "http://localhost:8765"
# -----------------------------------------------------------

dictionary = HanziDictionary()

def invoke(action, **params):
    payload = {"action": action, "version": 6, "params": params}
    try:
        response = requests.post(ANKICONNECT_URL, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get("error") is not None:
            raise Exception(result["error"])
        return result["result"]
    except requests.exceptions.RequestException as e:
        raise Exception(f"AnkiConnect request failed: {e}")
    except Exception as e:
        raise Exception(f"AnkiConnect error: {e}")

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
    
    parts = []
    for i, char in enumerate(unique_hanzi):
        try:
            pinyins = dictionary.get_pinyin(char, tone_marks=True)
            pinyin_str = " / ".join(pinyins) if pinyins else "N/A"
            
            entries = dictionary.definition_lookup(char)
            def_str = "no entry"
            if entries and entries[0].get('english'):
                full_def = entries[0]['english']
                def_str = re.split(r'[/;]', full_def)[0].strip()
        except Exception as e:
            print(f"  ⚠️  Dictionary lookup failed for '{char}': {e}")
            pinyin_str = "ERROR"
            def_str = "lookup failed"
        
        parts.append('<div class="char-block">')
        parts.append(f'<span class="bigchar">{char}</span>')
        parts.append(f'<span class="pinyin">({pinyin_str})</span>')
        parts.append(f'<span class="def">{def_str}</span>')
        
        try:
            examples = dictionary.get_examples(char)
            high_freq = examples.get('high_frequency', [])[:3]
            if high_freq:
                parts.append('<span class="ex-label">Common words:</span>')
                for ex in high_freq:
                    word = ex.get('simplified', 'N/A')
                    ex_py_list = ex.get('pinyin_list', ['N/A'])
                    ex_py = " / ".join(ex_py_list)
                    ex_def_short = get_one_word_meaning(ex.get('english', ''))
                    parts.append(f'<div class="example">• {word} ({ex_py}): {ex_def_short}</div>')
        except Exception as e:
            print(f"  ⚠️  Examples lookup failed for '{char}': {e}")
        
        parts.append('</div>')
        
        if i < len(unique_hanzi) - 1:
            parts.append('<hr class="sep">')
    
    return "\n".join(parts)

def main():
    print("Starting character breakdown fill via AnkiConnect...")
    print(f"Looking for notes with tag: {TAG}")
    print(f"Source field: {HANZI_FIELD} → Target field: {TARGET_FIELD}")
    print("-" * 60)
    
    try:
        note_ids = invoke("findNotes", query=f'tag:{TAG}')
    except Exception as e:
        print(f"❌ Failed to find notes: {e}")
        print("Make sure Anki is open and AnkiConnect is running.")
        return
    
    if not note_ids:
        print(f"No notes found with tag '{TAG}'")
        return
    
    print(f"Found {len(note_ids)} notes with the tag.")
    
    try:
        notes_info = invoke("notesInfo", notes=note_ids)
    except Exception as e:
        print(f"❌ Failed to retrieve note info: {e}")
        return
    
    updates = []
    processed = 0
    skipped = 0
    errors = 0
    
    for i, info in enumerate(notes_info, 1):
        note_id = info["noteId"]
        fields = info["fields"]
        
        print(f"[{i}/{len(notes_info)}] Processing note ID {note_id}...", end=" ")
        
        # Skip if already filled
        if fields.get(TARGET_FIELD, {}).get("value", "").strip():
            print("⏭️  skipped (already filled)")
            skipped += 1
            continue
        
        hanzi_text = fields.get(HANZI_FIELD, {}).get("value", "")
        if not hanzi_text.strip():
            print("⚠️  skipped (empty Hanzi field)")
            skipped += 1
            continue
        
        print(f"generating for: \"{hanzi_text}\"")
        
        try:
            html = generate_breakdown(hanzi_text)
            if not html:
                print("  ⚠️  No content generated")
                skipped += 1
                continue
            
            updates.append({
                "noteId": note_id,
                "fields": {TARGET_FIELD: {"value": html}}
            })
            processed += 1
        except Exception as e:
            print(f"  ❌ Error generating breakdown: {e}")
            errors += 1
    
    # Batch update
    if updates:
        try:
            invoke("updateNoteFields", notes=updates)
            print("-" * 60)
            print(f"✅ Successfully updated {len(updates)} notes!")
        except Exception as e:
            print(f"❌ Failed to update notes in Anki: {e}")
    else:
        print("-" * 60)
        print("No updates needed.")
    
    print(f"Summary: {processed} filled | {skipped} skipped | {errors} errors")

if __name__ == "__main__":
    main()