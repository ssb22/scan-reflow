#!/bin/bash

# Gather saved areas from GIMP temp directory, put them in
# order, and convert to PDF using pdflatex
# (c) Silas S. Brown 2005,2007,2010,2012,2018 (version 1.04).
# License: GPL

export TmpDir=$(mktemp -d /tmp/areas2pdfXXXXXX)
cd $TmpDir || exit 1
export Count=1
echo '\documentclass{article}\usepackage[pdftex]{graphicx}\usepackage{geometry}\geometry{verbose,a4paper,tmargin=10mm,bmargin=10mm,lmargin=10mm,rmargin=10mm,headheight=0mm,headsep=0mm,footskip=0mm}\pagestyle{empty}\begin{document}\raggedright\noindent' > handout.tex
export IFS=$'\n' # (NB $HOME may have spaces in it on cygwin)
for N in $(ls -r -t "$HOME"/.gimp*/tmp/*-area.png "$HOME/Library/Application Support/Gimp/tmp"/*.png 2>/dev/null); do
  if ! test -e "$N"; then continue; fi
  mv "$N" $Count.png || (cp "$N" $Count.png && rm "$N")
  export Geom=$(pngtopnm $Count.png | head -2 | tail -1)
  if test $(echo $Geom | sed -e 's/ / -gt /'); then
    # Width is greater than height - better put it landscape
    export RotStart='\rotatebox{90}{'
    export RotEnd='}'
  else unset RotStart RotEnd; fi
  export Aspect=$[1000*$(echo $Geom|sed -e 's/ /\//g')]
  if test $Aspect -gt 1414 || test $Aspect -lt 707; then
    # better scale by the longest side
    export ResizeParams="{$(echo $'\041')}{1\\textheight}"
  else
    export ResizeParams="{1\\columnwidth}{$(echo $'\041')}"
  fi
  # if ! test $Count == 1; then echo '\newpage' >> handout.tex; fi # not needed if \raggedright + can sometimes save paper if 2+ tall+thin images will fit on 1 page
  echo "\\resizebox*$ResizeParams{$RotStart\\includegraphics{$Count.png}$RotEnd}" >> handout.tex
  export Count=$[$Count+1]
done
echo '\end{document}' >> handout.tex
pdflatex handout.tex
if ! test "a$areas2pdf_force_problem" == a || ! test -e handout.pdf; then
  echo "There was a problem producing handout.pdf"
  echo "You will need to pick up the pieces from $TmpDir"
  exit 1
fi
mv handout.pdf "$HOME"
cd
rm -rf $TmpDir
echo
echo "Output was written to ~/handout.pdf"
