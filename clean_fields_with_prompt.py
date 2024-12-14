import requests

# AnkiConnect settings
ANKI_CONNECT_URL = "http://localhost:8765"
TAG_NAME = "spanish_7500sentences"  # Tag used for filtering notes
FIELDS_TO_CLEAN = ["sentence", "japanese"]  # Fields to clean

def fetch_notes_by_tag(tag_name):
    """Fetch notes with the specified tag."""
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {"query": f"tag:{tag_name}"}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload).json()
    if response.get("error"):
        print(f"Error fetching notes: {response['error']}")
        return []
    return response.get("result", [])

def get_note_fields(note_ids):
    """Fetch field data for the given notes."""
    payload = {
        "action": "notesInfo",
        "version": 6,
        "params": {"notes": note_ids}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload).json()
    if response.get("error"):
        print(f"Error fetching note fields: {response['error']}")
        return []
    return response.get("result", [])

def update_note_field(note_id, updated_fields):
    """Update the specified fields of a note."""
    payload = {
        "action": "updateNoteFields",
        "version": 6,
        "params": {
            "note": {
                "id": note_id,
                "fields": updated_fields
            }
        }
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload).json()
    if response.get("error"):
        print(f"Error updating note {note_id}: {response['error']}")
    else:
        print(f"Successfully updated note {note_id} | Sentence: '{updated_fields.get('sentence', 'N/A')}' | Japanese: '{updated_fields.get('japanese', 'N/A')}'")

def clean_field(value):
    """Remove the leading '•' if present."""
    if value.startswith("•"):
        return value[1:].strip()
    return value

def prompt_for_empty_field(note_id, field_name):
    """Prompt the user for action when a field is empty."""
    while True:
        print(f"The '{field_name}' field for note {note_id} is empty.")
        action = input("Retry (r) or Skip (s)? ").strip().lower()
        if action == "r":
            return "retry"
        elif action == "s":
            return "skip"
        else:
            print("Invalid input. Please enter 'r' to retry or 's' to skip.")

def main():
    # Fetch notes by tag
    note_ids = fetch_notes_by_tag(TAG_NAME)
    if not note_ids:
        print("No notes found!")
        return

    print(f"Found {len(note_ids)} notes to process.")

    # Fetch fields for all notes
    notes = get_note_fields(note_ids)
    if not notes:
        print("No note fields retrieved!")
        return

    for note in notes:
        note_id = note["noteId"]
        updated_fields = {}

        for field in FIELDS_TO_CLEAN:
            if field in note["fields"]:
                original_value = note["fields"][field]["value"]

                # Handle empty fields for "japanese" specifically
                if field == "japanese" and not original_value.strip():
                    action = prompt_for_empty_field(note_id, field)
                    if action == "retry":
                        # Re-fetch the note fields and retry
                        note = get_note_fields([note_id])[0]
                        original_value = note["fields"][field]["value"]
                    elif action == "skip":
                        print(f"Skipping note {note_id}.")
                        break

                cleaned_value = clean_field(original_value)

                if original_value != cleaned_value:
                    print(f"Cleaning note {note_id} field '{field}': {original_value} -> {cleaned_value}")
                    updated_fields[field] = cleaned_value
                else:
                    print(f"Field '{field}' in note {note_id} already clean. Skipping.")

        if updated_fields:
            update_note_field(note_id, updated_fields)

    print("Processing complete!")

# Run the script
if __name__ == "__main__":
    main()
