# __init__.py  –  put this in ~/Library/Application Support/Anki2/addons21/traditional_converter/__init__.py

from aqt import mw, gui_hooks
from aqt.utils import showInfo
import opencc

def convert_to_traditional():
    converter = opencc.OpenCC('s2twp.json')  # Taiwan standard + phrases
    tag = "Chinese_Shared_Deck"

    note_ids = mw.col.find_notes(f'tag:{tag}')
    total = len(note_ids)
    if total == 0:
        showInfo("No notes found with tag 'Chinese_Shared_Deck'")
        return

    mw.progress.start(label=f"Converting {total:,} notes to Taiwan Traditional…", immediate=True)

    updated = 0
    for i, nid in enumerate(note_ids):
        note = mw.col.get_note(nid)

        # Safety filters
        if note.note_type()["name"] not in {"Recognize A...", "Learn New C..."}:
            continue
        if "Hanzi" not in note or "Traditional" not in note:
            continue

        hanzi = note["Hanzi"].strip()
        if not hanzi:
            continue
        if note["Traditional"].strip() and note["Traditional"].strip() != hanzi:
            continue  # don't overwrite manual edits

        traditional = converter.convert(hanzi)
        if traditional != hanzi:
            note["Traditional"] = traditional
            note.flush()
            updated += 1

        if i % 500 == 0:
            mw.progress.update(label=f"{i+1:,}/{total:,} processed — {updated:,} updated")

    mw.progress.finish()
    showInfo(
        f"Done! Taiwan Traditional conversion complete\n\n"
        f"• Scanned: {total:,} notes\n"
        f"• Updated: {updated:,} 'Traditional' fields\n"
        f"• Used OpenCC s2twp (Taiwan standard + common phrases)"
    )

# Add a menu entry so you can run it with one click
action = mw.form.menuTools.addAction("→ Convert Chinese_Shared_Deck to Traditional (Taiwan)")
action.triggered.connect(convert_to_traditional)