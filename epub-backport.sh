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
set -e
T="$(mktemp XXXXXX.epub)"
for N in $@; do
    if ! ebook-convert "$N" "$T" --output-profile nook --epub-version 2 --linearize --no-default-epub-cover; then rm "$T"; exit 1; fi
    # Work around bug in old Nook Simple Touch: when an inserted &shy; becomes visible on the last word of an otherwise 1-line "display: block" element (usually a heading in big print) the rest of the word disappears.  Workaround is to set the heading to display inline: it's still separated from the surrounding paragraphs that are display block (unless two headings together) but the old software is kludged into rendering it more correctly:
    mkdir "$T-unpacked" && cd "$T-unpacked" && unzip "../$T" stylesheet.css && $( (which python || which python3 || which python2.7)2>/dev/null) -c 'import re;o="{".join((i.replace("display: block","display: inline") if re.search("font-size: 1.[1-9]",i) else i) for i in open("stylesheet.css").read().split("{"));open("stylesheet.css","w").write(o)' && zip -9X ../"$T" stylesheet.css && cd .. && rm -rf "$T-unpacked"
    mv "$T" "$N"
done
