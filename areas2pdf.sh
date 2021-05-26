#!/bin/bash

# Gather saved areas from GIMP temp directory, put them in
# order, and convert to PDF using pdflatex
# (c) Silas S. Brown 2005,2007,2010,2012,2018-2019,2021 (version 1.09).

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Where to find history:
# on GitHub at https://github.com/ssb22/scan-reflow
# and on GitLab at https://gitlab.com/ssb22/scan-reflow
# and on BitBucket https://bitbucket.org/ssb22/scan-reflow
# and at https://gitlab.developers.cam.ac.uk/ssb22/scan-reflow
# and in China: https://gitee.com/ssb22/scan-reflow

if ! which pngtopnm 2>/dev/null >/dev/null; then
    echo "pngtopnm command not found"
    echo "Maybe you need to install netpbm or netpbm-progs on this system"
    exit 1
fi

if ! which pdflatex 2>/dev/null >/dev/null; then
    echo "pdflatex command not found"
    echo "Maybe you need to install texlive or similar on this system"
    exit 1
fi

export TmpDir=$(mktemp -d /tmp/areas2pdfXXXXXX)
cd $TmpDir || exit 1
export Count=1
echo '\documentclass{article}\usepackage[pdftex]{graphicx}\usepackage{geometry}\geometry{verbose,a4paper,tmargin=10mm,bmargin=10mm,lmargin=10mm,rmargin=10mm,headheight=0mm,headsep=0mm,footskip=0mm}\pagestyle{empty}\begin{document}\raggedright\noindent' > handout.tex
export IFS=$'\n' # (NB $HOME may have spaces in it on cygwin)
for N in $(ls -r -t "$HOME"/.config/GIMP/*/tmp/*-area.png "$HOME"/.gimp*/tmp/*-area.png /tmp/gimp/*/*-area.png "$HOME/Library/Application Support/Gimp/tmp"/*-area.png 2>/dev/null); do
  if ! test -e "$N"; then continue; fi # wrong directory
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
if [ $Count == 1 ] ; then
    echo "Couldn't find any area files."
    echo "(Did you set GIMP3_TEMPDIR to somewhere areas2pdf doesn't know about?)"
  rm handout.tex ; cd .. ; rmdir "$TmpDir"
  exit 1
fi
echo '\end{document}' >> handout.tex
pdflatex handout.tex
if [ "$areas2pdf_force_problem" ] || [ ! -e handout.pdf ]; then
  echo "There was a problem producing handout.pdf"
  echo "You will need to pick up the pieces from $TmpDir"
  exit 1
fi
mv handout.pdf "$HOME"
cd
rm -rf $TmpDir
echo
echo "Output was written to ~/handout.pdf"
