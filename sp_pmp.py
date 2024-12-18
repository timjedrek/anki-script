import os
import asyncio
import edge_tts
import requests
import re
from bs4 import BeautifulSoup

# Constants
ANKI_CONNECT_URL = "http://localhost:8765"  # AnkiConnect must be running
OUTPUT_DIR = "audio_files"  # Local directory to save generated audio files
VOICE = "es-ES-AlvaroNeural"  # Spanish male voice
RATE = "-10%"  # Speech rate
PITCH = "-10Hz"  # Speech pitch
TAG = "spanish_pmp_grammar_ch4"  # Filter notes by this tag
NOTE_TYPE = "Cloze"  # Filter notes by this note type
TEXT_FIELD = "Text"  # Field containing Spanish sentence
SOUND_FIELD = "Sound"  # Field to populate with TTS audio

async def generate_tts(text, file_name):
    """Generate TTS audio using EdgeTTS."""
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(file_name)

def fetch_notes():
    """Fetch all notes with the specified tag and note type."""
    query = f"tag:{TAG} note:Cloze"
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {"query": query}
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

def clean_spanish_sentence(html_text):
    """Extract only the first Spanish sentence, remove HTML tags, and strip cloze formatting."""
    # Remove all HTML tags
    soup = BeautifulSoup(html_text, "html.parser")
    clean_text = soup.get_text(separator=" ")  # Extract plain text

    # Match the first line containing 'Español:' and isolate the sentence
    match = re.search(r"Español:\s*(.+?)\s*(?=(English:|$))", clean_text, re.DOTALL)
    if match:
        spanish_sentence = match.group(1)
    else:
        return ""

    # Remove cloze formatting like {{c1::...}}
    spanish_sentence = re.sub(r"\{\{c\d+::(.*?)\}\}", r"\1", spanish_sentence)

    return spanish_sentence.strip()

def update_note_field(note_id, field_name, audio_file):
    """Update the specified field of a note with the generated audio."""
    payload = {
        "action": "updateNoteFields",
        "version": 6,
        "params": {
            "note": {
                "id": note_id,
                "fields": {
                    field_name: f"[sound:{audio_file}]"
                }
            }
        }
    }
    print(f"Updating note {note_id} with audio file: {audio_file}")
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    return response.json()

async def main():
    # Fetch notes with the specified tag and note type
    note_ids = fetch_notes()
    if not note_ids:
        print("No notes found with the specified tag and note type!")
        return

    print(f"Found {len(note_ids)} notes to process.")
    os.makedirs(OUTPUT_DIR, exist_ok=True)  # Ensure the output directory exists

    # Fetch fields for all notes
    notes = get_note_fields(note_ids)
    if not notes:
        print("No note fields retrieved!")
        return

    for i, note in enumerate(notes):
        note_id = note["noteId"]
        text_field = note["fields"].get(TEXT_FIELD, {}).get("value", "")

        if not text_field.strip():
            print(f"Skipping empty text for note {note_id}")
            continue

        # Clean and extract the Spanish sentence
        stripped_text = clean_spanish_sentence(text_field)
        if not stripped_text:
            print(f"No valid Spanish sentence in note {note_id}. Skipping.")
            continue

        print(f"Processing note {note_id}: {stripped_text}")

        # Generate unique audio file for each note
        audio_file = f"{TAG}_audio_{i + 1}.mp3"
        audio_path = os.path.join(OUTPUT_DIR, audio_file)
        await generate_tts(stripped_text, audio_path)
        print(f"Generated audio: {audio_path}")

        # Update the Sound field in Anki
        response = update_note_field(note_id, SOUND_FIELD, audio_file)
        if response.get("error"):
            print(f"Failed to update note {note_id}: {response['error']}")
        else:
            print(f"Successfully updated note {note_id}")

    print("Processing complete! Move audio files to the Anki media folder.")

# Run the script
asyncio.run(main())
