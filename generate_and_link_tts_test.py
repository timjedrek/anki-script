import os
import asyncio
import edge_tts
import requests

# Constants
ANKI_CONNECT_URL = "http://localhost:8765"  # AnkiConnect must be running
OUTPUT_DIR = "audio_files"  # Directory to save generated audio
VOICE = "ja-JP-KeitaNeural"  # High-quality male Japanese voice
RATE = "-10%"  # Adjust speech rate (matches AwesomeTTS setting of 0.95)
PITCH = "-10Hz"  # Adjust pitch (converted from +11 semitones)
FIELD_TO_GENERATE = "cleaned expression"  # Field with text to generate audio for
FIELD_TO_UPDATE = "Audio 2"  # Field to update with [sound:filename.mp3]

# Test Note ID
TEST_NOTE_ID = 1459708133938  # Replace with the Note ID of your test card

async def generate_tts(text, file_name):
    """Generate TTS audio using EdgeTTS."""
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(file_name)

def get_note_fields(note_id):
    """Fetch field data for the given note ID."""
    payload = {
        "action": "notesInfo",
        "version": 6,
        "params": {"notes": [note_id]}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload).json()
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
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    return response.json()

async def main():
    # Fetch the note data for the test note ID
    notes = get_note_fields(TEST_NOTE_ID)
    if not notes:
        print(f"No note found with ID {TEST_NOTE_ID}!")
        return

    note = notes[0]  # We are working with a single note
    text = note["fields"][FIELD_TO_GENERATE]["value"]  # Text to generate TTS for

    if not text.strip():
        print(f"Skipping empty text for note {TEST_NOTE_ID}")
        return

    # Generate TTS audio file
    audio_file = f"audio_test123123.mp3"
    audio_path = os.path.join(OUTPUT_DIR, audio_file)
    await generate_tts(text, audio_path)
    print(f"Generated audio: {audio_path}")

    # Update the Audio 2 field in Anki
    response = update_note_field(TEST_NOTE_ID, FIELD_TO_UPDATE, audio_file)
    if response.get("error"):
        print(f"Failed to update note {TEST_NOTE_ID}: {response['error']}")
    else:
        print(f"Updated note {TEST_NOTE_ID} with audio file: {audio_file}")

    print("Test completed!")

# Run the test script
asyncio.run(main())
