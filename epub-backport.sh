#!/bin/bash

# Calibre wrapper that backports a modern
# downloaded EPUB by stripping CSS etc that might
# crash old eInk devices like the Barnes & Noble
# Nook Simple Touch made in 2011

# (c) Silas S. Brown 2026.  License: Apache 2
# (I did say "public domain no warranty" but apparently
# some corporate offices don't trust that.  Apache 2 lets
# them know I don't have a silly patent up my sleeve that
# I'd try to enforce, so their policy might accept it more
# easily if you need to use this at work.)

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
for N in "$@"; do
    if ! ebook-convert "$N" "$T" --output-profile nook --epub-version 2 --linearize --no-default-epub-cover; then rm "$T"; exit 1; fi
    # Work around bug in old Nook Simple Touch: when an inserted &shy; becomes visible on the last word of an otherwise 1-line "display: block" element (usually a heading in big print) the rest of the word disappears.  Workaround is to set the heading to display inline: it's still separated from the surrounding paragraphs that are display block (unless two headings together) but the old software is kludged into rendering it more correctly
    # Also left-justify text because justify can stretch letters too much when a single word fits on the line at medium-large font sizes (especially in a margin'd block), and compress a couple of common fat-margin situations that can result in words being awkward to read (although you can make this slightly less bad on the device anyway with Publisher Defaults cleared in text settings and the bottom-right margin-override option set to its leftmost narrowest setting)
    mkdir "$T-unpacked"
    cd "$T-unpacked"
    unzip "../$T"
    "$( (which python || which python3 || which python2.7)2>/dev/null)" -c 'import re;o="{".join((i.replace("display: block","display: inline") if re.search("font-size: 1.[1-9]",i) else i).replace("text-align: justify","text-align: left").replace("padding-left: 3em;\n  text-indent: -3em;","padding-left: 1em; text-indent: -1em;").replace("padding-left: 2.5em;\n  text-indent: -1em;","padding-left: 1em; text-indent: -0.5em;") for i in open("stylesheet.css").read().split("{"));open("stylesheet.css","w").write(o)'
    # (EPUBs can still crash Nook's reader if they contain lots of MathJax: we can remove .mjx-* from the CSS to stop the crash but most mathematical symbols are missing from the font so we'd need glyph image substitution anyway, unless removing the equations but the kinds of texts that crash tend to be the kinds that are unusable without the equations)
    # Prime can be translated to a supported character; also make better use of full lines on some navigation pages:
    find . -name '*.xhtml' -exec sed -i "s/′/´/g;s/ʹ/´/g;s,<div class=\"[^\"]*w_navigation[^\"]*\"> *\\(<a href[^>]*>[^<]*</a>\\)</div>, \\1,g;s,<div class=\"[^\"]*w_navigation[^\"]*\"> *\\(\\( *<a href[^>]*>[^<]*</a>\\)*\\)</div>, \\1,g" '{}' + # assumes GNU sed for -i behaviour
    # also add in-page index if it has verses:
    find . -name '*.xhtml' -exec "$( (which python || which python3 || which python2.7)2>/dev/null)" -c 'import sys,re;d=open(sys.argv[-1]).read();V=["<a href=\"#"+m.group(1)+m.group(2)+"\">"+m.group(2)+"</a>" for m in re.finditer(r"id=\"([^\"_]*_verse)([0-9]+)\"",d)];open(sys.argv[-1],"w").write(d.replace("<p","<p>"+" ".join(V)+"</p><p",1) if V else d)' '{}' ';'
    zip -r9DX ../"$T" . -x mimetype
    #echo "Trying advzip..."; advzip -z -4 ../"$T" $(zipinfo -1 ../"$T"|grep -v '^mimetype$'|grep -v /$) || echo "advzip failed but epub should still be OK" # test run at -3: 1.6% saving for 1min/15M; -4: 1.9% saving for 7min/15M
    cd .. && rm -rf "$T-unpacked"
    mv "$T" "$N" ; du -h "$N"
done
