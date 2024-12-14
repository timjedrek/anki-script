import requests
from googletrans import Translator  # Install with `pip install googletrans==4.0.0-rc1`

# AnkiConnect settings
ANKI_CONNECT_URL = "http://localhost:8765"
TAG_NAME = "spanish_7500sentences"  # Change to the tag you're using

def get_notes_by_tag(tag_name):
    """Fetch notes with the specified tag."""
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {"query": f"tag:{tag_name}"}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    return response.json()["result"]

def get_note_fields(note_ids):
    """Fetch note fields for each note ID."""
    payload = {
        "action": "notesInfo",
        "version": 6,
        "params": {"notes": note_ids}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    return response.json()["result"]

def update_note_field(note_id, japanese_text):
    """Update the Japanese field of a note."""
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

def translate_sentences(sentences):
    """Translate Spanish sentences to Japanese."""
    translator = Translator()
    translations = [translator.translate(sentence, src="es", dest="ja").text for sentence in sentences]
    return translations

def main():
    # Step 1: Get notes with the specified tag
    note_ids = get_notes_by_tag(TAG_NAME)

    # Step 2: Fetch note fields and identify notes with blank Japanese fields
    notes = get_note_fields(note_ids)
    sentences_to_translate = []
    notes_to_update = []

    for note in notes:
        sentence = note["fields"]["sentence"]["value"]
        japanese = note["fields"]["japanese"]["value"]
        if not japanese.strip():  # If the Japanese field is blank
            sentences_to_translate.append(sentence)
            notes_to_update.append(note["noteId"])

    # Step 3: Translate Spanish sentences to Japanese
    japanese_translations = translate_sentences(sentences_to_translate)

    # Step 4: Update the Japanese field in Anki
    for note_id, japanese_text in zip(notes_to_update, japanese_translations):
        update_note_field(note_id, japanese_text)

    print("Finished updating notes!")

if __name__ == "__main__":
    main()
