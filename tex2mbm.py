#!/usr/bin/env python2

print "tex2mbm v1.121 (c) 2007 Silas S. Brown.  License: Apache 2" # see below

import sys
# NB if you have more files than will fit on sys.argv,
# you can add to them here by doing something like
# import os ; sys.argv += filter(lambda x:x.startswith("myfile-"), os.listdir("."))
if len(sys.argv)<2:
    print "Syntax: python2 tex2mbm.py input-files"
    print "Input files can be .tex or .ps or .pdf"
    print "CHANGE THE VARIABLES AT THE START OF THE SCRIPT FIRST."
    print "Creates contents.dat, sequence.dat and *.mbm"
    print "which should be loaded onto the EPOC device with MbmShow"
    print "Each input file will be indexed in contents.dat, so you can choose a document by its number"
    print "TeX files must not depend on anything else in the current directory, unless they specify it by absolute path"
    sys.exit()

# ---- Change these variables : --------------

device_resolution = (640, 480)  # for S7
# device_resolution = (480, 160)  # for Revo

# bmconv_command = "Bmconv.exe"
bmconv_command = "wine Bmconv.exe"

# The following variables are used for setting the
# font size etc of TeX files, and are ignored for
# .ps files which the program assumes are already
# at your desired size :

lines_per_screen = 3 # number of lines you want
# to fit on the screen at a time
# (if not integer, leading can be added)

baseSize_points = 25 # the font size of the
# document at the moment (e.g. 25 if you're
# using \huge in 12pt, see latex-papersize.py)
documentClass = "\\documentclass[12pt]{article}"
max_symbol_height = 1.67 # the number of (document) lines
# that the biggest symbol will take - this will
# be used to make one screen line

path_to_latexPapersize = "/usr/local/bin/latex-papersize.py"
# Make sure to point this at a latex-papersize.py,
# must be at least version 1.4

just_make_PS = False # if True, will just make
# .ps files - this script can later be run again
# on those .ps files instead of the .tex files
# (but set ps_input_is_Whole_Slides = False below).
# This is useful if your machine is the only one
# that has CJK-LaTeX on it but you want to do
# the bitmap processing on a more powerful
# machine later.

ps_input_is_Whole_Slides = True # if True, assumes that,
# if there is no .tex input, then the input files (.ps
# and .pdf) are whole slides not 1 line only.  Set this
# to False if the .ps files are from a just_make_PS run.

just_print_Bmconv_commands = False # if non-False,
# should be open("some-file","w") - will just
# print the bmconv.exe commands to that file,
# rather than trying to run them (and will not
# delete the temporary *.bmp files they need).
# Useful if this is running on a machine that is
# powerful for doing the bitmap work but that
# does not have bmconv.exe on it, and you want
# to run bmconv.exe later.

# --- End of variables that need changing -----

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

import os, sys, zlib

baseFilename = "font"
if not ".tex" in ''.join(sys.argv):
    startString = None
    if ps_input_is_Whole_Slides:
        lines_per_screen = 1
        baseFilename = "slides" # call it slides.mbm rather than font.mbm

dpi_to_set_at = 100 # regardless of actual device DPI - be nice to metafont
papersize_px = (device_resolution[0],device_resolution[1]/lines_per_screen)
fontsize_px = papersize_px[1] / max_symbol_height
fontsize_pt = fontsize_px * 72.0 / dpi_to_set_at
papersize_mm = tuple(map(lambda x: x*25.4/dpi_to_set_at, papersize_px))
latex_paper_command = "margin_left=0 margin_top=0 paper_width="+str(papersize_mm[0])+" paper_height="+str(papersize_mm[1])+" python \""+path_to_latexPapersize+"\" "+str(baseSize_points)+" "+str(fontsize_pt)+" "

if ".tex" in ''.join(sys.argv):
    # (note: don't need to do this if we're dealing with only .ps files)
    assert open(path_to_latexPapersize), "path_to_latexPapersize does not appear to be set properly" # (more likely to raise IOError than AssertionError, but still)
    startString = documentClass + os.popen(latex_paper_command+"tex").read()
    startString += "\\usepackage[T1]{fontenc}" # hack to ensure uses bitmaps not outlines in teTeX 2 (not needed in teTeX 1) (TODO: will it work in teTeX 3?)

tempDir = os.popen("mktemp -d").read().strip()

datToCharNo = {} ; charNoToDat = {} # maps between bitmap data and character number
bmconv_params = []
if just_make_PS: seq=contents=None
else:
    seq=open("sequence.dat","w")
    contents = open("contents.dat","w")

oldDir = os.getcwd()
for inputFile in sys.argv[1:]:
    try: dat = open(inputFile).read()
    except IOError: dat = "" # the argument might be a scale factor, see below
    os.chdir(tempDir)
    gsInput = "tmp.ps"
    if inputFile.endswith(".tex"):
        for thing in "documentclass textwidth textheight topmargin marginparwidth oddsidemargin evensidemargin".split(): assert not "\\"+thing in dat, "TeX files must NOT contain \\"+thing+" (this will be added by the script)"
        os.system("rm -f tmp.*")
        open("tmp.tex","w").write(startString+dat)
        ret = os.system("latex tmp.tex")
        assert not ret, "TeX error"
        ret = os.system(os.popen(latex_paper_command+"tmp.dvi").read().strip()+" -o tmp.ps -D "+str(dpi_to_set_at))
        assert not ret, "dvips error"
    elif inputFile.endswith(".ps") or inputFile.endswith(".pdf"):
        if inputFile.endswith(".pdf"): gsInput="tmp.pdf"
        open(gsInput,"w").write(dat)
    else:
        try: i=float(inputFile)
        except: i=0
        if i: # an extra scale factor for .ps input
            assert not ".tex" in " ".join(sys.argv[1:]), "Scale factors on the command line should be used only with .ps or .pdf input.  For scaling .tex input, change the variables at the start of the script."
            dpi_to_set_at *= i # papersize is already ok
            os.chdir(oldDir) ; continue
        else: assert 0, "Extension of filename '"+inputFile+"' not supported"
    if just_make_PS:
        # just copy that .ps out, clean up, and don't do any more
        open(oldDir+os.sep+inputFile[:inputFile.rfind(".")]+".ps","w").write(open("tmp.ps").read())
        os.system("rm *") ; os.chdir(oldDir)
        continue
    # otherwise go ahead and make the bitmaps
    print "Running gs to get PNGs"
    ret = os.system("gs -sDEVICE=png16m -sOutputFile=tmp%%08d.png -g%dx%d -r%dx%d -q -dNOPAUSE - < %s" % (papersize_px[0],papersize_px[1],dpi_to_set_at,dpi_to_set_at,gsInput)) # need to write to png16m to stop awful dithering from some source PDFs when writing to png16 (e.g. Seamonkey output)
    assert not ret, "gs error"
    # Now look at those PNG files and add to the sequence ('seq') :
    print "Examining PNGs"
    def lsbmsb16(num): return chr(num%256)+chr(num/256)
    def lsbmsb32(num): return lsbmsb16(num%65536)+lsbmsb16(num/65536)
    if contents: contents.write(lsbmsb32(seq.tell()))
    pngs = os.listdir(os.getcwd()) ; pngs.sort()
    open("epoc16","w").write('P6\n16 1\n255\n\x00\x00\x00\x00\xff\xff\x00\xff\x00UUU\x88\x00\x00\x00\x00\x88\xaa\xaa\xaa\xff\x00\xff\xff\x00\x00\x99\x99\x00\x00\x99\x99\x99\x00\x99\xff\xff\xff\xff\xff\x00\x00\x88\x00\x00\x00\xff') # the 16 colours used by Sketch on S7 - probably safest to keep to those
    open("epoc2","w").write('P6\n2 1\n255\n\x00\x00\x00\xff\xff\xff') # black & white
    open("epoc4","w").write('P6\n4 1\n255\n\x00\x00\x00UUU\xaa\xaa\xaa\xff\xff\xff') # 4 greys
    for f in pngs:
        if not f.endswith(".png"): continue # ignore
        dat=os.popen('pngtopnm "'+f+'" | pnmcrop -white -left -right -bottom | pnmremap -nofs -mapfile=epoc16 2>/dev/null').read() # (don't crop top because we're using it for alignment)
        if not dat: continue # maybe it was a blank page (pnmcrop error) - ignore it
        compressed_dat = zlib.compress(dat,9) # save VM
        if not datToCharNo.has_key(compressed_dat): # new image
            # work out how many colours we need.  Don't use P6/P5/P4 because it often overstates things.
            os.popen("pnmremap -nofs -mapfile=epoc4 2>/dev/null | pnmremap -nofs -mapfile=epoc16 >testfile 2>/dev/null","wb").write(dat)
            if open("testfile").read()==dat:
                # Can at least take it down to greymap.  B&W ?
                os.popen("pnmremap -nofs -mapfile=epoc2 2>/dev/null | pnmremap -nofs -mapfile=epoc16 >testfile 2>/dev/null","wb").write(dat)
                if open("testfile").read()==dat: flag="/1" # B&W
                else: flag="/2" # grey
            else: flag="/c4" # 16 colours
            fname="%08d.bmp" % len(datToCharNo)
            bmconv_params.append(flag+fname)
            charNoToDat[len(datToCharNo)]=compressed_dat
            datToCharNo[compressed_dat]=len(datToCharNo)
        seq.write(lsbmsb16(datToCharNo[compressed_dat]))
        if contents: docs=contents.tell()/4
        else: docs=1
        print "Docs="+str(docs),"chars="+str(seq.tell()/2),"unique="+str(len(datToCharNo))
    os.system("rm *") ; os.chdir(oldDir)

if just_make_PS:
    os.system("rm -rf \"%s\"" % (tempDir,))
    print "Made *.ps files - you now need to run this script on a more powerful machine, with just_make_PS and ps_input_is_Whole_Slides both set to False"
    sys.exit()

AllUnique = (seq.tell()/2 == len(datToCharNo))
ContentsNotNeeded = (contents.tell() == 4) # only 1 document
del datToCharNo, contents, seq
# Finish by doing the conversion to MBM from the in-memory unique bitmaps :
startPoints=range(0,len(bmconv_params),510)+[len(bmconv_params)]
# (note that bmconv can't take more than 510 slides at a time - confirmed by using short filenames that this limit is in number of slides, not in number of characters on the command line)
os.chdir(tempDir)
for i in range(len(startPoints)-1):
    for charNo in range(startPoints[i],startPoints[i+1]): os.popen("ppmtobmp > %08d.bmp" % (charNo,),"w").write(zlib.decompress(charNoToDat[charNo]))
    if i==0: extra=""
    else: extra=hex(i)[2:].upper() # (drop '0x' at beginning)
    this_cmd = bmconv_command+" "+baseFilename+extra+".mbm "+' '.join(bmconv_params[startPoints[i]:startPoints[i+1]])
    if just_print_Bmconv_commands: just_print_Bmconv_commands.write(this_cmd+"\n")
    else: 
        ret=os.system(this_cmd)
        assert not ret, "bmconv_command exitted with an error"
        os.system("mv "+baseFilename+extra+".mbm \""+oldDir+"\" ; rm *")
os.chdir(oldDir)
# clean up, zip, print report
toPrint = ["\n--------------------------"] ; toZip = []
if not ContentsNotNeeded:
    toPrint.append("Made contents.dat")
    toZip.append("contents.dat")
    AllUnique = False # because we DO make sequence.dat if we made contents.dat
else:
    toPrint.append("Didn't make contents.dat, as there was only one input document")
    os.remove("contents.dat")
    if AllUnique:
        toPrint.append("Didn't make sequence.dat, as all images were unique")
        os.remove("sequence.dat")
if not AllUnique:
    toPrint.append("Made sequence.dat")
    toZip.append("sequence.dat")
if just_print_Bmconv_commands:
    print "\n".join(toPrint)
    print "Made bmconv commands (which should be run using the *.bmp files in %s)" % (tempDir,)
else:
    os.system("rm -rf \"%s\"" % (tempDir,))
    toPrint.append("Made "+baseFilename+"*.mbm")
    toZip.append(baseFilename+"*.mbm")
    assert not " " in baseFilename, "you'll be sorry..."
    os.system("zip -9 to-epoc.zip "+" ".join(toZip)+" && rm "+" ".join(toZip))
    print "\n".join(toPrint)
    print "Zipped into to-epoc.zip for transfer to the device"
