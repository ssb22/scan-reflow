#!/usr/bin/env python

print "tex2mbm-fast v1.2 (c) 2008,2009 Silas S. Brown.  License: Apache 2" # see below

import sys

# NB if you have more files than will fit on sys.argv,
# you can add to them here by doing something like
# import os ; sys.argv += filter(lambda x:x.startswith("myfile-"), sorted(os.listdir(".")))
if len(sys.argv)<2:
    print "Syntax: python tex2mbm-fast.py .tex-files"
    print "Creates contents.dat, sequence.dat and *.mbm"
    print "which should be loaded onto the EPOC device with MbmShow"
    sys.exit()

# ---- Change these variables : --------------

device_resolution = (640, 480)  # for S7
# device_resolution = (480, 160) # for Revo
# device_resolution = (320, 240) # for many Windows Mobile handsets

# bmconv_command = "Bmconv.exe"
# bmconv_command = "wine Bmconv.exe"
# bmconv_command = "cp /other/downloads/bmconv/Bmconv.exe . && wine Bmconv.exe"
bmconv_command = "~/bin/Bmconv.exe"

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

just_print_Bmconv_commands = False # if non-False,
# should be open("some-file","w") - will just
# print the bmconv.exe commands to that file,
# rather than trying to run them (and will not
# delete the temporary *.bmp files they need).

also_make_HTML_files = False
also_make_compressed_XBM = False

leave_tex_logs = False # set if you don't want them deleted

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

import os, re
baseFilename = "font"
dpi_to_set_at = 100 # regardless of actual device DPI - be nice to metafont
papersize_px = (device_resolution[0],device_resolution[1]/lines_per_screen)
fontsize_px = papersize_px[1] / max_symbol_height
fontsize_pt = fontsize_px * 72.0 / dpi_to_set_at
papersize_mm = tuple(map(lambda x: x*25.4/dpi_to_set_at, papersize_px))
latex_paper_command = "margin_left=0 margin_top=0 paper_width="+str(papersize_mm[0])+" paper_height="+str(papersize_mm[1])+" python \""+path_to_latexPapersize+"\" "+str(baseSize_points)+" "+str(fontsize_pt)+" "

assert open(path_to_latexPapersize), "path_to_latexPapersize does not appear to be set properly" # (more likely to raise IOError than AssertionError, but still)
startString = documentClass + os.popen(latex_paper_command+"tex").read()
startString += "\\usepackage[T1]{fontenc}" # hack to ensure uses bitmaps not outlines in teTeX 2+ (not needed in teTeX 1)

tempDir = os.popen("mktemp -d").read().strip()

texToCharNo = {} ; charNoToTex = {} ; charNoToFlag = {}
bmconv_params = []
seq=open("sequence.dat","w")
contents = open("contents.dat","w")

oldDir = os.getcwd()

first_file_preamble = last_file_end = None

def lsbmsb16(num): return chr(num%256)+chr(num/256)
def lsbmsb32(num): return lsbmsb16(num%65536)+lsbmsb16(num/65536)

for inputFile in sys.argv[1:]:
    dat = open(inputFile).read().replace("\r\n","\n")
    if not first_file_preamble:
        first_file_preamble=dat[:dat.index("\n%StartWord\n")]+"\n"
        for thing in "documentclass textwidth textheight topmargin marginparwidth oddsidemargin evensidemargin".split(): assert not "\\"+thing in first_file_preamble, "TeX files must NOT contain \\"+thing+" (this will be added by the script)"
    else: assert first_file_preamble==dat[:dat.index("\n%StartWord\n")]+"\n", "All TeX files must contain identical material before the first %StartWord"
    last_file_end = dat[dat.rindex("\n%EndWord\n"):]
    if also_make_HTML_files:
        fileNo = contents.tell()/4
        htmlFile=open("%05d.html" % fileNo,"w")
        htmlFile.write("<HTML><BODY>\n")
    contents.write(lsbmsb32(seq.tell()))
    for word in dat.split("\n%StartWord\n")[1:]:
        word += "\n" ; word=word[:word.index("\n%EndWord\n")+1] # +1 to include the \n
        if not word.strip(): continue # ignore any completely-blank 'words'
        if word not in texToCharNo:
            c=len(texToCharNo)
            charNoToTex[c]=word
            if "%Colour" in word: charNoToFlag[c]="/c4"
            elif "%Grey" in word: charNoToFlag[c]="/2"
            else: charNoToFlag[c]="/1"
            texToCharNo[word]=c
        seq.write(lsbmsb16(texToCharNo[word]))
        if also_make_HTML_files: htmlFile.write("<IMG SRC=%08d.png>\n" % texToCharNo[word])
    if also_make_HTML_files:
        htmlFile.write("<BR>")
        if not inputFile==sys.argv[-1]: htmlFile.write("<A HREF=%05d.html>Next</A>\n" % (fileNo+1))
        if fileNo: htmlFile.write("<A HREF=%05d.html>Previous</A>\n" % (fileNo-1))
        htmlFile.write("</BODY></HTML>")
        htmlFile.close()
l = charNoToTex.items() ; l.sort()
os.chdir(tempDir)
open("tmp.tex","w").write(startString+first_file_preamble+"\n".join(map(lambda (x,y): y, l))+last_file_end)
ret = os.system("latex tmp.tex")
assert not ret, "TeX error"
ret = os.system(os.popen(latex_paper_command+"tmp.dvi").read().strip()+" -o tmp.ps -D "+str(dpi_to_set_at))
assert not ret, "dvips error"
print "Running gs to get PNGs"
ret = os.system("gs -sDEVICE=png16 -sOutputFile=tmp%%08d.png -g%dx%d -r%dx%d -q -dNOPAUSE - < tmp.ps" % (papersize_px[0],papersize_px[1],dpi_to_set_at,dpi_to_set_at))
assert not ret, "gs error"
print "Trimming PNGs"
pngs = os.listdir(os.getcwd()) ; pngs.sort()
assert len(pngs)>=len(texToCharNo), "Not enough pages were generated (maybe some of your words did not actually generate pages?)"
count = 0
for f in pngs:
    if count==len(texToCharNo): break # already had enough pages - rest is probably a blank one at the end
    if not f.endswith(".png"): continue # ignore
    dat=os.popen('pngtopnm "'+f+'" | pnmcrop -white -left -right -bottom').read() # (don't crop top because we're using it for alignment)
    if not dat: continue # maybe it was a blank page (pnmcrop error) - ignore it
    flag = charNoToFlag[count]
    fname="%08d.bmp" % count
    bmconv_params.append(flag+fname)
    if also_make_HTML_files: os.popen("pnmtopng -compression 9 > \""+oldDir+os.sep+("%08d.png" % count)+"\"","w").write(dat)
    if also_make_compressed_XBM: os.popen("ppmtopgm|pgmtopbm -threshold | pbmtoxbm > \""+oldDir+os.sep+("%08d.xbm" % count)+"\"","w").write(dat)
    count += 1
    os.popen("ppmtobmp > "+fname,"w").write(dat)
    print "Done",count,"of",len(texToCharNo)
if not leave_tex_logs: os.system("find . -name 'tmp*' | xargs rm") # leaves the .bmp files
AllUnique = (seq.tell()/2 == len(texToCharNo))
ContentsNotNeeded = (contents.tell() == 4) # only 1 document
del texToCharNo, charNoToTex, charNoToFlag, contents, seq
startPoints=range(0,len(bmconv_params),510)+[len(bmconv_params)]
for i in range(len(startPoints)-1):
    if i==0: extra=""
    else: extra=hex(i)[2:].upper() # (drop '0x' at beginning)
    this_cmd = bmconv_command+" "+baseFilename+extra+".mbm "+' '.join(bmconv_params[startPoints[i]:startPoints[i+1]])
    if just_print_Bmconv_commands: just_print_Bmconv_commands.write(this_cmd+"\n")
    else: 
        ret=os.system(this_cmd)
        assert not ret, "bmconv_command exitted with an error"
        os.system("mv "+baseFilename+extra+".mbm \""+oldDir+"\"")
os.chdir(oldDir)
# clean up, zip, print report
toPrint = ["\n--------------------------"] ; toZip = []
if ContentsNotNeeded:
    toPrint.append("Didn't make contents.dat, as there was only one input document")
    os.remove("contents.dat")
else:
    toPrint.append("Made contents.dat")
    toZip.append("contents.dat")
    AllUnique = False # because we DO make sequence.dat if we made contents.dat
if AllUnique:
    toPrint.append("Didn't make sequence.dat, as all images were unique")
    os.remove("sequence.dat")
else:
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
if also_make_HTML_files: os.system("echo zipping HTML files... && find . -maxdepth 1 -name '*.png' -o -name '*.html' | xargs zip -9q htmlfiles.zip && find . -maxdepth 1 '(' -name '*.png' -o -name '*.html' ')' -exec rm '{}' ';' && echo Made htmlfiles.zip")
if also_make_compressed_XBM:
    i=0 ; dat=[]
    while True:
        try:
          dat.append(zlib.compress(open(("%08d.xbm" % i),"rb").read()))
          os.remove("%08d.xbm" % i)
        except: break
        i += 1
    o=open("images.dat","wb")
    offset=4*(len(dat)+1)
    def writeOffset(o,offset): o.write(chr(offset&255)+chr((offset>>8)&255)+chr((offset>>16)&255)+chr((offset>>24)&255))
    for d in dat:
          writeOffset(o,offset)
          offset += len(d)
    writeOffset(o,offset)
    for d in dat: o.write(d)
    print "Made images.dat (compressed XBM for XBMshow.py)"
