#!/usr/bin/osascript
tell application "Anki"
    do shell script "echo $ANKI_SITE_PACKAGES"
end tell
