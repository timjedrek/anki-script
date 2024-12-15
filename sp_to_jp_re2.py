import os
import asyncio
import edge_tts
import requests
import time

# Constants
ANKI_CONNECT_URL = "http://localhost:8765"  # AnkiConnect must be running
OUTPUT_DIR = "audio_files"  # Local directory to save generated audio files
VOICE = "ja-JP-KeitaNeural"  # High-quality male Japanese voice
RATE = "-10%"  # Adjust speech rate
PITCH = "-10Hz"  # Adjust pitch
TAG_NAME = "spanish_7500sentences"  # Tag used for filtering notes
FIELD_TO_GENERATE = "japanese"  # Field with text to generate audio for
FIELD_TO_UPDATE = "japanese audio"  # Field to update with [sound:filename.mp3]
MAX_RETRIES = 5  # Maximum number of retries before prompting

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
            print(f"Successfully updated note {note_id} with audio file: {audio_file}")
        return response_json
    except Exception as e:
        print(f"Exception occurred while updating note {note_id}: {e}")
        return None

def handle_empty_field(note_id):
    """Handle empty 'japanese' field with retries and prompting."""
    retries = 0
    while retries < MAX_RETRIES:
        print(f"Retrying note {note_id}... ({retries + 1}/{MAX_RETRIES})")
        time.sleep(5)  # Wait before retrying
        note = get_note_fields([note_id])[0]
        japanese_text = note["fields"][FIELD_TO_GENERATE]["value"].strip()
        if japanese_text:  # If the field is now populated
            print(f"Field 'japanese' for note {note_id} is now populated: {japanese_text}")
            return japanese_text
        retries += 1

    # If retries are exhausted, prompt the user
    while True:
        print(f"The 'japanese' field for note {note_id} is still empty after {MAX_RETRIES} retries.")
        action = input("Retry (r) or Skip (s)? ").strip().lower()
        if action == "r":
            retries = 0  # Reset retries and continue looping
        elif action == "s":
            print(f"Skipping note {note_id}.")
            return None
        else:
            print("Invalid input. Please enter 'r' to retry or 's' to skip.")

async def main():
    # Fetch notes by tag
    note_ids = fetch_notes_by_tag(TAG_NAME)
    if not note_ids:
        print("No notes found!")
        return

    print(f"Found {len(note_ids)} notes to process.")

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Fetch fields for all notes
    notes = get_note_fields(note_ids)
    if not notes:
        print("No note fields retrieved!")
        return

    file_number = 1  # Start numbering from 1 for this run
    for note in notes:
        note_id = note["noteId"]

        # Check if the FIELD_TO_GENERATE exists
        if FIELD_TO_GENERATE not in note["fields"]:
            print(f"Field '{FIELD_TO_GENERATE}' not found in note {note_id}. Skipping.")
            continue

        text = note["fields"][FIELD_TO_GENERATE]["value"].strip()

        # Skip if the FIELD_TO_UPDATE already contains audio
        if FIELD_TO_UPDATE in note["fields"] and note["fields"][FIELD_TO_UPDATE]["value"].strip():
            print(f"Note {note_id} already has audio in '{FIELD_TO_UPDATE}'. Skipping.")
            continue

        if not text:  # Handle empty 'japanese' field
            text = handle_empty_field(note_id)
            if not text:  # If user chose to skip, continue to the next note
                continue

        # Generate unique audio file name
        audio_file = f"sp_sent_turned_nihonjin_resume5_{file_number}.mp3"
        audio_path = os.path.join(OUTPUT_DIR, audio_file)

        print(f"TTS Text for note {note_id}: {text}")
        await generate_tts(text, audio_path)
        print(f"Generated audio: {audio_path}")

        # Update the FIELD_TO_UPDATE in Anki
        response = update_note_field(note_id, FIELD_TO_UPDATE, audio_file)
        if response is None:
            print(f"Skipping note {note_id} due to an error during update.")
            continue

        file_number += 1

    print("Processing complete! Manually move the files to the Anki media folder.")

# Run the script
asyncio.run(main())
