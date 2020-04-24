#!/usr/bin/env python
# (should work in either Python 2 or Python 3)

# Edit enlarged documents made by reflow.c
# (c) Silas S. Brown, 2006-2009, 2012, 2020.  Version 1.3
# 
# Shows documentation on startup (or you can read it below)

#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

# Where to find history:
# on GitHub at https://github.com/ssb22/scan-reflow
# and on GitLab at https://gitlab.com/ssb22/scan-reflow
# and on BitBucket https://bitbucket.org/ssb22/scan-reflow

print ("""

edit-reflow.py: Allows you to edit documents prepared by
running reflow.c.  The current directory is assumed to
contain all files it produced.

After running reflow.c --edit, look at enlarged.pdf or
enlarged.html - there will be a small red number above
each word or group of words.  (Always remember that the
number of each word is the number above it, not the number
below it.)  These numbers can be copied to the clipboard
by selecting the area in xpdf, or by selecting and doing Copy
in HTML.

If using HTML, you can copy the numbers to the clipboard
whether or not you've used --edit; all --edit does is makes
them visible by default, which might be useful if you're
collaborating.  If you are collaborating, you can also
specify http://url/of/enlarged.html#number to point your
collaborator directly to a numbered word, and in some
browsers it will be highlighted automatically.

This script takes instructions about edit decisions.
Each instruction is a command followed by a list of
numbers; the numbers indicate which parts of the text
to apply the command to, and correspond to the small red
numbers.  It's normally best to work with the edit decisions
in a text editor, and piping or pasting them to the script's
input when they are ready.

After running this script, you should run reflow.c again as
instructed; you can change the scale and paper type then.

Here are the instructions that are understood:

yellow 0 1 2 3 4 - will highlight word numbers 0, 1, 2, 3,
and 4 in yellow. Obviously you can list any word numbers
you like instead of 0 1 2 3 4 (and there is no limit to
the number of words you can list). You can copy and paste
areas of numbers in the PDF as you think of what needs to
be highlighted, but make sure that there is a space between
each number (i.e. make sure that the copy/paste operation
doesn't join two numbers together) and make sure that
there are no digits missing from the end of the selection
(some versions of xpdf have been known to drop a digit
from the last number on each screen when it is copied).

red, green, cyan and magenta are also understood.  (You can
add more colours by editing the "colours" data in this script.)

delete 0 1 2 3 4 will delete words 0 1 2 3 and 4 (or
whichever other numbers you list); this is useful for
removing text that you don't really need and that gets in
the way.

Note that you can abbreviate the lists, for example
instead of saying 0 1 2 3 4 you can just say 0-4. This
can be useful if you're specifying a huge amount of text.
(You can give it a complicated mixed list if you want,
e.g. delete 24-36 231 824 97-153.)
If you are copying numbers by hand then you can
also abbreviate any of the numbers, so e.g. "delete 42-7"
will delete from 42 to 47, or "yellow 672-83" will highlight
672 to 683.

keep 0 1 2 3 4 will keep those words and delete everything
else. This is an alternative approach if you want to delete
most words and keep just a few. Again you can abbreviate
things, so "0 1 2 3 4" can be written as "0-4".

move 47-53 to after 34. This will cut out words 47 through
to 53 inclusive, and paste them in so that they appear
after word 34. Useful for moving around footnotes and other
things that you want to read in a different order. You
can also say "before" instead of "after" (so "before 35"
is equivalent to "after 34"), and "copy" instead of "move".

Note that the delete and move instructions do NOT change
any of the numbers.  So if you delete words 50 to 60,
then word 61 will still be called word 61. It will not
be re-numbered to 50.  Deleting and moving means that the
numbers will no longer be continuous.  This means you can
always copy and paste numbers from the PDF without having
to worry that your instructions might have changed them.

pause after 45 - this will insert 2 blue slashes (//)
after word number 45.  "before" is also acceptable.
""")

import sys,os,struct,time
lines = open("enlarged.tex").readlines()
try:
    open("enlarged-orig.tex")
    print ("WARNING!!!  enlarged-orig.tex already exists.")
    print ("This probably means you are running edit-reflow.py for a second time.")
    print ("Note that your edits WILL BE ADDED to existing edits")
    print ("(in particular, existing deletions will not be reverted)")
    print ("unless you move enlarged-orig.tex to enlarged.tex before running this script.")
    print ("----------------------------------")
    print ("Pausing for 10 seconds to make above warning more noticeable...")
    time.sleep(10)
    # (actually enlarged-orig.tex doesn't have to be kept; it can be re-generated by removing enlarged.* and sequence.dat and re-running reflow with a scale parameter and no filenames)
except IOError:
    os.system("cp enlarged.tex enlarged-orig.tex")

def stripSpaceAroundMinuses(s):
    while True:
        s2 = s.replace(" -","-").replace("- ","-")
        if s==s2: return s
        s = s2

print ("Enter commands (EOF when done)")
commands = stripSpaceAroundMinuses(sys.stdin.read().replace("\r"," ").replace("\n"," ")).split()

# Some versions of ppmchange recognise colour names, but
# it depends on the setup.  Using values to make sure.
colours = {"yellow":"#ff0",
           "red":"#f00",
           "green":"#0f0",
           # green could use "rgbi:0.7/1/0.7" - slightly more readable, especially on (non-EPOC) laptops.  But DON'T do this - it works when gs to bmp16, but not when gs to png16m followed by quantise (which is sometimes needed if o/p from seamonkey etc, see comments in tex2mbm.py) - in that case it quantises to a shade of grey.  TODO dither *here*?  but difficult to make it nice and there could be compression issues.  (Or add this colour to the 'EPOC map' in tex2mbm.py?  IF 4-bit mbm files have a palette.  I'm not sure that they do - seems just RGBI.  But on the other hand Bmconv may be able to specify some dithering and keep the high compression.  It would be nice if there were some documentation on the MBM *format*; psiconv doesn't say much about colours/palettes or compression.)
           "cyan":"#0ff",
           "magenta":"#f0f"}

mode = colourToUse = "start" ; beforeOrAfter = "before"
keep_deleteList = None
lines_to_move = []
copy_mode = 0

def findLines(firstWord,lastWord): return map(lambda i:lines[i], findLineIndices(firstWord,lastWord))

def findLineIndices(firstWord,lastWord):
    return filter(lambda i:".png}" in lines[i] and line2int(lines[i]) in range(firstWord,lastWord+1),range(len(lines)))

def line2int(line):
    # need to catch both \wordnumber{..} and \resizebox.. variants, so pick up on the {000000000.png}
    return int(line[line.find(".png}")-9:line.find(".png}")])

def findIndex(firstWord,lastWord):
    indexList = findLineIndices(firstWord,lastWord)
    if not indexList:
        print ("WARNING: findIndex failed on words %d-%d" % (firstWord,lastWord))
        return None
    index = indexList[0]
    if beforeOrAfter=="after": index += 1
    return index

def process(firstWord,lastWord):
    global lines_to_move,keep_deleteList,copy_mode
    if lastWord<firstWord: lastWord=int(str(firstWord)[:len(str(firstWord))-len(str(lastWord))]+str(lastWord)) # so can say things like 124-8, 572-83, etc
    if mode=="delete":
        for l in findLines(firstWord,lastWord): lines.remove(l)
    elif mode=="keep":
        if not keep_deleteList: keep_deleteList=filter(lambda x:".png}" in x,lines)
        for l in findLines(firstWord,lastWord):
            try:
                keep_deleteList.remove(l)
            except ValueError: pass
    elif mode=="move" or mode=="copy":
        lines_to_move += findLines(firstWord,lastWord)
        copy_mode = (mode=="copy")
    elif mode=="to":
        if not copy_mode:
            for l in lines_to_move: lines.remove(l)
        index = findIndex(firstWord,lastWord)
        if index:
            lines_to_move.reverse()
            for l in lines_to_move: lines.insert(index,l)
        else: print ("WARNING: could not find where word %d is (in '... to %d'); ignoring that instruction" % (firstWord,firstWord))
        lines_to_move = []
    elif mode=="pause":
        index = findIndex(firstWord,lastWord)
        if index: lines.insert(index,"\\textcolor{blue}") # will sort out the rest later
        else: print ("WARNING: could not find where word %d is (in 'pause .. %d'); ignoring that instruction" % (firstWord,firstWord))
    elif mode=="colour":
        for w in range(firstWord,lastWord+1): os.system("pngtopnm %09d.png | pnmdepth 16 | ppmchange \"#fff\" \"%s\" | pnmtopng -compression 9 > n && mv n %09d.png" % (w,colourToUse,w))

################################################

for cc in commands:
    c = cc.lower()
    if c in colours:
        mode = "colour"
        colourToUse = colours[c]
    elif c in ["delete","keep","move","copy","to","pause"]: mode = c
    elif c in ["before","after"]: beforeOrAfter = c
    elif "-" in c:
        if mode in ["colour","delete","keep","move"]: process(int(c[:c.find("-")]),int(c[c.find("-")+1:]))
        else: print ("WARNING: '%s' cannot accept a range of values like '%s'; ignoring" % (mode,c))
    else: process(int(c),int(c))

if keep_deleteList:
    for l in keep_deleteList: lines.remove(l)

seq=open("sequence.dat","wb")
for l in lines:
    if ".png}" in l: i=line2int(l)
    elif l.startswith("\\textcolor{blue}"): i=-1 # covers pauses that we added and also pauses that were already there (in case we're editing for a second time)
    else: continue
    seq.write(struct.pack("i",i))
seq.close()

print ("""\n\n\n
All done.  You now need to run reflow.c again, specifying
the final scale factor, possibly preceded by paper type
(--slides or --slides=X,Y), and NO OTHER OPTIONS OR FILENAMES
(although you can specify --edit again if you really want to).

Note: If you run edit-reflow again, further edits will be
ADDED to the edits you've made.  If you don't want this
(e.g. because the source images contain multiple scans and
you want to produce completely different documents on
different occasions), move enlarged-orig.tex to enlarged.tex
before running edit-reflow.py again.
""")
