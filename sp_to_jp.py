import requests
from googletrans import Translator  # Install with `pip install googletrans==4.0.0-rc1`

# AnkiConnect settings
ANKI_CONNECT_URL = "http://localhost:8765"
TAG_NAME = "spanish_7500sentences"  # Change to the tag you're using

def get_notes_by_tag(tag_name):
    """Fetch notes with the specified tag."""
    print(f"Fetching notes with tag: {tag_name}...")
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {"query": f"tag:{tag_name}"}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    note_ids = response.json()["result"]
    print(f"Found {len(note_ids)} notes.")
    return note_ids

def get_note_fields(note_id):
    """Fetch note fields for a single note ID."""
    payload = {
        "action": "notesInfo",
        "version": 6,
        "params": {"notes": [note_id]}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    notes = response.json()["result"]
    return notes[0] if notes else None

def update_note_field(note_id, japanese_text):
    """Update the Japanese field of a note."""
    print(f"Updating note ID {note_id} with translation: {japanese_text}")
    payload = {
        "action": "updateNoteFields",
        "version": 6,
        "params": {
            "note": {
                "id": note_id,
                "fields": {
                    "japanese": japanese_text
                }
            }
        }
    }
    requests.post(ANKI_CONNECT_URL, json=payload)

def translate_sentence(sentence):
    """Translate a single sentence to Japanese."""
    translator = Translator()
    try:
        print(f"Translating: {sentence}")
        translation = translator.translate(sentence, src="es", dest="ja").text
        print(f"Translation result: {translation}")
        return translation
    except Exception as e:
        print(f"Error translating sentence: {sentence}. Error: {e}")
        return None

def main():
    # Step 1: Get notes with the specified tag
    note_ids = get_notes_by_tag(TAG_NAME)

    # Step 2: Process each note one by one
    for index, note_id in enumerate(note_ids, start=1):
        print(f"Processing note {index}/{len(note_ids)} (ID: {note_id})...")

        # Fetch the note fields
        note = get_note_fields(note_id)
        if not note:
            print(f"Note ID {note_id} not found. Skipping...")
            continue

        # Extract Spanish sentence and Japanese field
        sentence = note["fields"]["sentence"]["value"]
        japanese = note["fields"]["japanese"]["value"]

        # Skip if the Japanese field is already filled
        if japanese.strip():
            print(f"Note ID {note_id} already has a Japanese translation. Skipping...")
            continue

        # Translate the sentence
        translation = translate_sentence(sentence)
        if not translation:
            print(f"Failed to translate sentence for Note ID {note_id}. Skipping...")
            continue

        # Update the note with the translation
        update_note_field(note_id, translation)

    print("Finished processing all notes!")

if __name__ == "__main__":
    main()
