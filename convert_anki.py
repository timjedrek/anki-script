cat << 'EOF' > convert_anki.py
import json
import urllib.request
import opencc
import sys

# --- CONFIGURATION ---
TAG_TO_SEARCH = "Chinese_Shared_Deck"
SOURCE_FIELD = "Hanzi"
TARGET_FIELD = "Traditional"
CONVERTER_CONFIG = 's2twp.json' 
ANKI_CONNECT_URL = 'http://127.0.0.1:8765'

def invoke(action, **params):
    requestJson = json.dumps({'action': action, 'params': params, 'version': 6}).encode('utf-8')
    try:
        response = json.load(urllib.request.urlopen(urllib.request.Request(ANKI_CONNECT_URL, requestJson)))
        if len(response) != 2:
            raise Exception('Response has an unexpected number of fields')
        if 'error' not in response:
            raise Exception('Response is missing required error field')
        if response['error'] is not None:
            raise Exception(response['error'])
        return response['result']
    except Exception as e:
        print(f"\n[Error] Could not connect to Anki: {e}")
        print("Please ensure Anki is running and the AnkiConnect add-on is installed.")
        sys.exit(1)

def main():
    print("--- Anki Simplified to Taiwan Traditional Converter ---")
    
    print(f"Loading OpenCC with config '{CONVERTER_CONFIG}'...")
    converter = opencc.OpenCC(CONVERTER_CONFIG)
    
    print(f"Searching for notes with tag: {TAG_TO_SEARCH}...")
    try:
        note_ids = invoke('findNotes', query=f'tag:{TAG_TO_SEARCH}')
    except Exception as e:
        print(f"Error finding notes: {e}")
        return

    total_notes = len(note_ids)
    print(f"Found {total_notes} notes. Fetching details...")

    if total_notes == 0:
        print("No notes found. Check your tag spelling.")
        return

    batch_size = 50
    converted_count = 0
    skipped_count = 0
    
    for i in range(0, total_notes, batch_size):
        batch_ids = note_ids[i:i + batch_size]
        notes_info = invoke('notesInfo', notes=batch_ids)
        
        for note in notes_info:
            fields = note['fields']
            note_id = note['noteId']
            
            if SOURCE_FIELD not in fields:
                # print(f"\n[Warning] Note {note_id} missing source field '{SOURCE_FIELD}'. Skipping.")
                skipped_count += 1
                continue
            
            if TARGET_FIELD not in fields:
                print(f"\n[Error] Target field '{TARGET_FIELD}' does not exist on Note {note_id}.")
                print("Please add the 'Traditional' field to your Note Type in Anki first.")
                sys.exit(1)

            source_text = fields[SOURCE_FIELD]['value']

            if not source_text:
                skipped_count += 1
                continue

            trad_text = converter.convert(source_text)
            
            invoke('updateNoteFields', note={'id': note_id, 'fields': {TARGET_FIELD: trad_text}})
            converted_count += 1

        progress = min(i + batch_size, total_notes)
        percent = (progress / total_notes) * 100
        sys.stdout.write(f"\rProgress: {progress}/{total_notes} ({percent:.1f}%)")
        sys.stdout.flush()

    print("\n\n--- Conversion Complete ---")
    print(f"Total notes processed: {total_notes}")
    print(f"Successfully converted: {converted_count}")
    print(f"Skipped (empty/missing source): {skipped_count}")
    print("You may need to force a sync in Anki if you use AnkiWeb.")

if __name__ == '__main__':
    main()
EOF