import requests

# Constants
ANKI_CONNECT_URL = "http://localhost:8765"  # AnkiConnect URL
TAG_TO_FIX = "cloze_fix"  # Tag to filter cards
FIELD_TO_FIX = "Text"  # Field containing the cloze
FIXED_BRACKET = "{{{0}}}"  # Proper cloze format

def find_notes_by_tag(tag):
    """Fetch all note IDs with the specified tag."""
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {"query": f"tag:{tag}"}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload).json()
    return response.get("result", [])

def get_note_info(note_ids):
    """Retrieve field content for all note IDs."""
    payload = {
        "action": "notesInfo",
        "version": 6,
        "params": {"notes": note_ids}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload).json()
    return response.get("result", [])

def fix_cloze_field(text):
    """Ensure the cloze field has proper brackets {{ and }}."""
    import re
    # Search for broken cloze deletions
    fixed_text = re.sub(r"{c(\d+)::(.*?)}", r"{{c\1::\2}}", text)
    return fixed_text

def update_note_field(note_id, updated_text):
    """Update a note's field with corrected text."""
    payload = {
        "action": "updateNoteFields",
        "version": 6,
        "params": {
            "note": {
                "id": note_id,
                "fields": {
                    FIELD_TO_FIX: updated_text
                }
            }
        }
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload).json()
    return response.get("error")

def main():
    print("Fetching notes tagged with cloze_fix...")
    note_ids = find_notes_by_tag(TAG_TO_FIX)
    if not note_ids:
        print("No notes found with the specified tag.")
        return
    
    print(f"Found {len(note_ids)} notes. Processing...")
    notes = get_note_info(note_ids)

    for note in notes:
        note_id = note["noteId"]
        text = note["fields"][FIELD_TO_FIX]["value"]

        # Fix the cloze field
        updated_text = fix_cloze_field(text)
        if updated_text != text:  # Only update if changes were made
            error = update_note_field(note_id, updated_text)
            if error:
                print(f"Failed to update note {note_id}: {error}")
            else:
                print(f"Fixed and updated note {note_id}")
        else:
            print(f"No changes needed for note {note_id}")

    print("Processing complete!")

if __name__ == "__main__":
    main()
