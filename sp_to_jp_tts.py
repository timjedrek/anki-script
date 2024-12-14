import os
import asyncio
import edge_tts
import requests

# Constants
ANKI_CONNECT_URL = "http://localhost:8765"  # AnkiConnect must be running
OUTPUT_DIR = "audio_files"  # Local directory to save generated audio files
VOICE = "ja-JP-KeitaNeural"  # High-quality male Japanese voice
RATE = "-10%"  # Adjust speech rate
PITCH = "-10Hz"  # Adjust pitch
TAG_NAME = "spanish_7500sentences"  # Tag used for filtering notes
FIELD_TO_GENERATE = "japanese"  # Field with text to generate audio for
FIELD_TO_UPDATE = "japanese audio"  # Field to update with [sound:filename.mp3]

async def generate_tts(text, file_name):
    """Generate TTS audio using EdgeTTS."""
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(file_name)

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
    # Fetch notes by tag
    note_ids = fetch_notes_by_tag(TAG_NAME)
    if not note_ids:
        print("No notes found!")
        return

    print(f"Found {len(note_ids)} notes to process.")
    os.makedirs(OUTPUT_DIR, exist_ok=True)  # Ensure the output directory exists

    # Fetch fields for all notes
    notes = get_note_fields(note_ids)
    if not notes:
        print("No note fields retrieved!")
        return

    for i, note in enumerate(notes, start=1):
        note_id = note["noteId"]

        # Check if the FIELD_TO_GENERATE exists
        if FIELD_TO_GENERATE not in note["fields"]:
            print(f"Field '{FIELD_TO_GENERATE}' not found in note {note_id}. Skipping.")
            continue

        text = note["fields"][FIELD_TO_GENERATE]["value"]  # Text to generate TTS for

        # If the field is empty, prompt the user
        while not text.strip():
            print(f"The 'japanese' field for note {note_id} is empty.")
            user_input = input("Retry (r) or Skip (s)? ").strip().lower()
            if user_input == "s":
                print(f"Skipping note {note_id}.")
                break
            elif user_input == "r":
                # Retry fetching the note
                note = get_note_fields([note_id])[0]
                text = note["fields"][FIELD_TO_GENERATE]["value"]
            else:
                print("Invalid input. Please enter 'r' to retry or 's' to skip.")

        # Skip if the user chose to skip
        if not text.strip():
            continue

        # Log the text being TTS'd
        print(f"TTS Text for note {note_id}: {text}")

        # Generate unique audio file for each note
        audio_file = f"spanish_sentences_turned_nihonjin_{i}.mp3"
        audio_path = os.path.join(OUTPUT_DIR, audio_file)
        await generate_tts(text, audio_path)
        print(f"Generated audio: {audio_path}")

        # Update the FIELD_TO_UPDATE in Anki
        response = update_note_field(note_id, FIELD_TO_UPDATE, audio_file)
        if response.get("error"):
            print(f"Failed to update note {note_id}: {response['error']}")
        else:
            print(f"Successfully updated note {note_id}")

    print("Processing complete! Manually move the files to the Anki media folder.")

# Run the script
asyncio.run(main())
