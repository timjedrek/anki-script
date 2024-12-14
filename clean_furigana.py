import re
import requests

ANKI_CONNECT_URL = "http://localhost:8765"

def remove_furigana(text):
    """Remove furigana enclosed in square brackets [] from Japanese text."""
    return re.sub(r'\[.*?\]', '', text)

def fetch_cards_with_field(field_name, note_type):
    """Fetch all notes with the specified field and note type."""
    query = f'note:"{note_type}"'
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {"query": query}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload).json()
    return response['result']

def get_note_fields(note_ids):
    """Fetch all field data for the given note IDs."""
    payload = {
        "action": "notesInfo",
        "version": 6,
        "params": {"notes": note_ids}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload).json()
    return response['result']

def update_note_field(note_id, field_name, new_text):
    """Update a specific field in a note."""
    payload = {
        "action": "updateNoteFields",
        "version": 6,
        "params": {
            "note": {
                "id": note_id,
                "fields": {
                    field_name: new_text
                }
            }
        }
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    return response

# Customize these variables
note_type = "Japanese Shared Deck"  # Replace with your actual note type name
source_field = "Expression"         # Field to clean (contains furigana)
target_field = "cleaned expression" # Field to populate with cleaned text

# Fetch all notes in the specified note type
note_ids = fetch_cards_with_field(source_field, note_type)
if not note_ids:
    print("No notes found.")
    exit()

# Fetch fields for the notes
notes = get_note_fields(note_ids)

# Process and update each note
for note in notes:
    note_id = note['noteId']
    original_text = note['fields'][source_field]['value']
    cleaned_text = remove_furigana(original_text)
    update_note_field(note_id, target_field, cleaned_text)
    print(f"Updated note {note_id}: {cleaned_text}")

print("All cards have been processed.")
