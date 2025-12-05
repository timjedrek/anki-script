#!/usr/bin/env python3
# convert_to_traditional.py  —  TAG-ONLY version (the safest)
# Run with: python3 convert_to_traditional.py   (Anki must be open)

from aqt import mw
from aqt.utils import showInfo
import opencc

# ─────── CONFIGURE THESE TWO LINES ONLY ───────
simplified_field  = "Hanzi"        # existing field (don’t change)
traditional_field = "Traditional"  # new field name (you can rename if you want)
target_tag        = "Chinese_Shared_Deck"   # ← exact tag from the shared deck
# ─────────────────────────────────────────────

converter = opencc.OpenCC('s2twp')   # Taiwan-standard Traditional

def s2tw(text):
    return "" if not text else converter.convert(text)

def main():
    if not mw or not mw.col:
        showInfo("Please open Anki first!")
        return

    # Find every note that has the exact tag
    note_ids = mw.col.find_notes(f'tag:"{target_tag}"')
    if not note_ids:
        showInfo(f'No notes found with tag "{target_tag}"\nCheck spelling/case.')
        return

    # Add the new field if it doesn’t exist yet
    sample_note = mw.col.get_note(note_ids[0])
    model = sample_note.note_type()
    if traditional_field not in [f["name"] for f in model["flds"]]:
        mw.col.models.add_field(model, mw.col.models.new_field(traditional_field))

    # Convert all of them
    updated = 0
    for nid in note_ids:
        note = mw.col.get_note(nid)
        if simplified_field in note:
            note[traditional_field] = s2tw(note[simplified_field])
            note.flush()
            updated += 1

    mw.reset()
    showInfo(f"All done!\n"
             f"Converted {updated} notes with tag '{target_tag}' to Traditional Chinese (Taiwan).\n\n"
             f"Just add {{{traditional_field}}} to your card templates wherever you want the 傳統漢字.")

if __name__ == "__main__":
    main()