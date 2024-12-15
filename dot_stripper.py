import requests
import re

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

def update_note_fields(note_id, updated_fields):
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
    try:
        response = requests.post(ANKI_CONNECT_URL, json=payload)
        if response is None:
            print(f"Error: No response from AnkiConnect when updating note {note_id}")
            return None
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code} from AnkiConnect when updating note {note_id}")
            print(f"Response content: {response.content}")
            return None

        response_json = response.json()
        if "error" in response_json and response_json["error"]:
            print(f"Error updating note {note_id}: {response_json['error']}")
        else:
            print(f"Successfully updated note {note_id}: {updated_fields}")
        return response_json
    except Exception as e:
        print(f"Exception occurred while updating note {note_id}: {e}")
        return None

def clean_field(value):
    """Remove leading '•' and any non-alphanumeric or non-Japanese characters."""
    # Regex to match leading non-alphanumeric or non-Japanese characters
    cleaned_value = re.sub(r"^[^a-zA-Z0-9\u3000-\u30FF\u4E00-\u9FFF]+", "", value)
    return cleaned_value.strip()

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
                cleaned_value = clean_field(original_value)

                if original_value != cleaned_value:
                    print(f"Cleaning note {note_id} field '{field}': {original_value} -> {cleaned_value}")
                    updated_fields[field] = cleaned_value
                else:
                    print(f"Field '{field}' in note {note_id} already clean. Skipping.")

        if updated_fields:
            update_note_fields(note_id, updated_fields)

    print("Processing complete!")

# Run the script
if __name__ == "__main__":
    main()
