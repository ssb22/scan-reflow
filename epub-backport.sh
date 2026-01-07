#!/bin/bash

# Calibre wrapper that backports a modern
# downloaded EPUB by stripping CSS etc that might
# crash old eInk devices like the Barnes & Noble
# Nook Simple Touch

# Silas S. Brown - public domain - no warranty

# Does not substitute images for fonts that will
# be missing on the old devices, but at least
# should make it so the reader doesn't 'crash'
# with an Application Not Responding (Android 2.1)

# Can take time to run on some EPUBs

if ! [ "$1" ]; then echo "Syntax: $0 epub-files"
                    echo "(backports them inline)"
                    exit 1; fi
T="$(mktemp XXXXXX.epub)"
for N in $@; do
    if ! ebook-convert "$N" "$T" --output-profile nook --epub-version 2 --linearize --no-default-epub-cover; then rm "$T"; exit 1; fi
    mv "$T" "$N"
done
