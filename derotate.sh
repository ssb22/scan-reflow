#!/bin/bash

# Script to assist in correcting rotations
# (c) Silas S. Brown 2006-2008,2019-2020, v1.1214.  License: GPL

# Where to find history:
# on GitHub at https://github.com/ssb22/scan-reflow
# and on GitLab at https://gitlab.com/ssb22/scan-reflow
# and on BitBucket https://bitbucket.org/ssb22/scan-reflow
# and at https://gitlab.developers.cam.ac.uk/ssb22/scan-reflow

if [ ! "$1" ]; then
  echo "Syntax: $0 image-file image-file ....."
  echo "Helps you de-rotate all images listed on the command-line."
  exit 1
fi

# Remember on cygwin $HOME may have spaces in it
if (cd "$HOME";test -e .gimp*/tmp/*-area.png); then
  echo -n "Error: Some saved areas already exist in "
  echo -n "$HOME/";cd "$HOME";echo .gimp*/tmp
  echo "Please check if they're important, and if not, remove them."
  echo "Then run this script again."
  exit 1
fi

echo "
About to run gimp on all image files, one by one.
When each file loads, do this:
1. Use the selection tool
2. Choose a line of the rotated text
3. Click on the bottom left of this line
4. Drag to the bottom right of this line
5. Use the 'save area' command to save the selection
6. If the line is slanting upwards, REPEAT step 5
7. Quit the GIMP (Control-Q)
This script will then look at the dimensions of the area you
saved (and whether or not you saved it twice) and will use this
information to calculate the angle of rotation of the image.
The image will then be replaced with its de-rotated version
(and converted to PNG if it's not already PNG).
If any image is straight already, just quit (Control-Q)
and the image will be converted to PNG with no rotation.
Press Enter when you have read the above instructions.
"
read

unset NeedRemove
export TempDirectory=$(mktemp -d)
touch $TempDirectory/.ready
while [ "$1" ]; do
if test -d /cygdrive; then
# looks like we're on CygWin - this is tricky
cp "$1" /cygdrive/c/Program*Files/GIMP*/bin
pushd /cygdrive/c/Program*Files/GIMP*/bin
./gimp*.exe -d -s "$1" || exit 1
#echo "Press Enter when Gimp has terminated" ; read
mv "$1" "$OLDPWD"
popd
else gimp -d -s "$1" || exit 1; fi
export NumFiles=$(cd "$HOME";ls .gimp*/tmp/*-area.png 2>/dev/null|wc -l)
export AsPng="$(echo "$1"|sed -e 's/\.[^\.]*$/.png/')"
if ! echo "$1"|grep '\.' >/dev/null; then export AsPng="$1.png"; fi # (if no extension at all)
if test $NumFiles == 0; then
  # it seems this one was straight.  but we might still have to convert it to PNG.
  if test "$1" != "$AsPng"; then
    while ! test -e $TempDirectory/.ready; do echo "Waiting for netpbm to catch up"; sleep 1; done # (TODO unless on an SMP system.  Doing it this way rather than 'wait' for a PID because sometimes Cygwin's wait is broken.)
    rm $TempDirectory/.ready
    (anytopnm "$1" | pnmtopng -compression 9 > "$AsPng" && rm "$1"; touch $TempDirectory/.ready) &
  fi
  shift; continue
fi
pushd "$HOME"
for File in .gimp*/tmp/*-area.png; do
export Geom=$(pngtopnm $File | head -2 | tail -1)
if test $(echo $Geom|sed -e 's/ .*//') -gt 300; then break; else unset Geom; fi
done
popd
if [ ! "$Geom" ]; then
  echo ; echo "ERROR: You did not select a large enough area for reliable rotation (must be at least 300 pixels wide)."
  echo "(This error can also be caused by a timing bug in some versions of the GIMP - try doing it again more slowly.)"
  echo "Press Enter to try again."
  read
elif test $NumFiles -gt 2; then
  echo "ERROR: you need to choose 0, 1 or 2 areas, not $NumFiles"
  echo "Press Enter to try again."
  read
else
  export Deg=$(echo $Geom | python -c 'import sys,math; w,h=sys.stdin.read().split() ; print(math.atan(1.0*int(h)/int(w))*180/math.pi)') # Python 2 and Python 3 should both work
  if test $NumFiles == 2; then export Deg=-$Deg; fi
  while ! test -e $TempDirectory/.ready; do echo "Waiting for netpbm to catch up"; sleep 1; done; rm $TempDirectory/.ready # as above
  # some buggy versions of pnmrotate don't like -background=white on a PPM (2-colour) image, so we need to make sure it's at least greyscale first, ideally in the same pipe.  pnmtopng/pngtopnm doesn't always do it.  Piping through ppmtopcx/pcxtoppm or pnmtorle/rletopnm seems to work.
  # (we also allow for very old versions of pnmrotate that don't have the -background=white switch)
  # (and we use 1.0,1.0,1.0 instead of 'white' in case rgb.txt isn't properly present on the system)
  (anytopnm "$1" | pnmtorle | rletopnm | (pnmrotate -background=1.0,1.0,1.0 -noantialias $Deg 2>/dev/null || pnmrotate -noantialias $Deg) | pnmtopng -compression 9 > "$1.new" && rm "$1" && mv "$1.new" "$AsPng"; touch $TempDirectory/.ready) &
  export NeedRemove="$AsPng $NeedRemove" # hope no spaces in there
  shift
fi
(cd "$HOME";rm .gimp*/tmp/*-area.png)
done
while ! test -e $TempDirectory/.ready; do echo "Waiting for netpbm to catch up"; sleep 1; done
if [ "$NeedRemove" ]; then clear; fi
echo "All images have been de-rotated."
rm -rf $TempDirectory
if [ ! "$NeedRemove" ]; then exit; fi
echo "One more thing: You may need to manually remove any large
marks at the edges of the scan; these are quite likely if
the document was rotated when the area to scan was selected,
and they can confuse further processing (especially marks to
the left and right of the text).  So we will now run gimp
again, on just the files that have been de-rotated last
time.  For each one, select any unwanted marks, Cut
(Control-X), Save (Control-S) and Quit (Control-Q).  (NB if
you need to select more than one mark then you may need to
click outside each selection before making the next one)"
echo "Press Enter to start."
read
for I in $NeedRemove; do
if test -d /cygdrive; then
# looks like we're on CygWin - this is tricky
cp "$I" /cygdrive/c/Program*Files/GIMP*/bin
pushd /cygdrive/c/Program*Files/GIMP*/bin
./gimp*.exe -d -s "$I"
#echo "Press Enter when Gimp has terminated" ; read
mv "$I" "$OLDPWD"
popd
else gimp -d -s "$I"; fi; done
echo "All done."
