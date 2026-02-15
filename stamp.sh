#!/bin/bash
# PDF filename stamping script (pdflatex + pdftk)
# Stamps the filename of a PDF file on its top right
# Silas S. Brown 2026 - public domain

# (Useful if students have submitted work by email
# but with names/IDs only in the filename and you need
# to identify which is which from printer output.
# As long as top right of page is blank and the info you
# want is in the filename, just run "stamp filename.pdf")

set -e

if [ $# -eq 0 ]; then echo "Usage: $0 pdf-file(s)"
                      exit 1; fi
TEMP_DIR=$(mktemp -d)
output="$TEMP_DIR/stamped.pdf"
for pdf in "$@"; do
    cat > "$TEMP_DIR/stamp.tex" << EOF
\\documentclass[12pt]{article}
\\usepackage[a4paper,margin=0pt]{geometry}
\\usepackage[utf8]{inputenc}\\pagestyle{empty}
\\setlength{\\parindent}{0pt}\\begin{document}\\vspace*{10pt}
\\hfill\\fontsize{14}{16}\\selectfont
$(echo "$(basename "$pdf" .pdf)" | sed 's/[%&#$_{}]/\\&/g; s/[][|]<>/$&$/g')
\\hspace*{10pt}\\end{document}
EOF
    pushd "$TEMP_DIR"
    pdflatex -interaction=nonstopmode stamp.tex
    popd
    pdftk "$pdf" stamp "$TEMP_DIR/stamp.pdf" output "$output"
    mv "$output" "$pdf"
    echo "Done $pdf"
done
rm -rf "$TEMP_DIR"
