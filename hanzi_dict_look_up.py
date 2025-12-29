# hanzi_dict_look_up.py
# Run this script to fill the "PyScriptLookUp" field for all notes tagged "Chinese_Shared_Deck"
# Requires Anki to be running with AnkiConnect addon installed (default port 8765)

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
    """Helper to talk to AnkiConnect"""
    payload = {"action": action, "version": 6, "params": params}
    response = requests.post(ANKICONNECT_URL, json=payload).json()
    if response.get("error") is not None:
        raise Exception(response["error"])
    return response["result"]

def get_one_word_meaning(full_def):
    if not full_def:
        return "N/A"
    # Take the first English part before '/' or ';', then the first word
    part = re.split(r'[/;]', full_def)[0].strip()
    words = part.split()
    return words[0].capitalize() if words else "N/A"

def generate_breakdown(text):
    if not text:
        return ""
    
    # Unique hanzi in order of appearance
    hanzi_list = re.findall(r'[\u4e00-\u9fff]', text)
    unique_hanzi = []
    seen = set()
    for h in hanzi_list:
        if h not in seen:
            unique_hanzi.append(h)
            seen.add(h)
    
    parts = []
    for i, char in enumerate(unique_hanzi):
        # Pinyin with tone marks
        pinyins = dictionary.get_pinyin(char, tone_marks=True)
        pinyin_str = " / ".join(pinyins) if pinyins else "N/A"
        
        # Primary definition
        entries = dictionary.definition_lookup(char)
        def_str = "no entry"
        if entries and entries[0].get('english'):
            full_def = entries[0]['english']
            def_str = re.split(r'[/;]', full_def)[0].strip()
        
        parts.append('<div class="char-block">')
        parts.append(f'<span class="bigchar">{char}</span>')
        parts.append(f'<span class="pinyin">({pinyin_str})</span>')
        parts.append(f'<span class="def">{def_str}</span>')
        
        # Example words (up to 3 high-frequency)
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
        
        parts.append('</div>')
        
        # Separator except after the last character
        if i < len(unique_hanzi) - 1:
            parts.append('<hr class="sep">')
    
    return "\n".join(parts)

def main():
    # Find all note IDs with the tag
    note_ids = invoke("findNotes", query=f'tag:{TAG}')
    
    if not note_ids:
        print(f"No notes found with tag '{TAG}'")
        return
    
    # Get note info (fields)
    notes_info = invoke("notesInfo", notes=note_ids)
    
    updates = []
    processed = 0
    
    for info in notes_info:
        fields = info["fields"]
        
        # Skip if target field already has content
        if fields.get(TARGET_FIELD, {}).get("value", "").strip():
            continue
        
        # Get the sentence
        hanzi_text = fields.get(HANZI_FIELD, {}).get("value", "")
        if not hanzi_text:
            continue
        
        html = generate_breakdown(hanzi_text)
        if not html:
            continue
        
        updates.append({
            "noteId": info["noteId"],
            "fields": {
                TARGET_FIELD: {"value": html}
            }
        })
        processed += 1
    
    # Batch update
    if updates:
        invoke("updateNoteFields", notes=updates)
        print(f"Successfully filled {len(updates)} notes ({processed} processed total).")
    else:
        print("No new notes needed updating.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Anki is open and AnkiConnect is running.")