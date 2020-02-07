#!/usr/bin/env python
# (should work in either Python 2 or Python 3)

# bitmap.py v1.3 (c) 2009, 2020 Silas S. Brown.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

try: raw_input
except: # Python 3
    raw_input = input

def getVal(prompt,default):
    r=raw_input(prompt+"? (default "+str(default)+") : ")
    if not r: return default
    return float(r)

xpixels = getVal("Screen pixel width",640)
ypixels = getVal("Screen pixel height",480)
heightmm = getVal("Screen physical height mm",93) # 6.1"
scale = getVal("Extra magnification factor",2)
heightmm = heightmm*1.0/scale # use the small-paper trick (do not use SeaMonkey's "scale"; it doesn't always work)
widthmm = xpixels*heightmm/ypixels ; dpi = ypixels*25.4/heightmm # this assumes square pixels

# Try to use the smallest paper size possible (saves CPU processing whitespace below), but don't go below A5 because A6 isn't always available
paperH, paperW, paperNumber = 210,148,5
while paperH<heightmm or paperW<widthmm:
    # Paper not big enough - try next size up
    paperNumber -= 1
    paperW, paperH = paperH, int(paperH * 1.414 + .5)

import os
print("")
raw_input("In Seamonkey (or whatever), set papersize A%d (portrait), margins: left 0mm bottom 0mm top %dmm right %dmm, no titles in margins, scale 100%%, print to PDF.  Save it as %s, then press Enter: " % (paperNumber,paperH-heightmm,paperW-widthmm,os.getcwd()+os.sep+"enlarged.pdf"))

print ("\nProcessing...")
os.system((r"mkdir tmp0 && cd tmp0 && gs -sDEVICE=png16m -sOutputFile=slide%%03d.png -r%(dpi)d -q -dNOPAUSE - < ../enlarged.pdf && (echo '\documentclass{article}\usepackage[pdftex]{graphicx} \pdfimageresolution=%(dpi)d \textwidth %(widthmm)dmm \pdfpagewidth=%(widthmm)d true mm \textheight %(heightmm)dmm \pdfpageheight=%(heightmm)d true mm \topmargin 0mm \marginparwidth 0mm \oddsidemargin 0mm \evensidemargin 0mm \pdfhorigin=0 mm \pdfvorigin=-12.95 mm \begin{document}\pagestyle{empty}'; for N in slide*.png ; do pngtopnm $N | pnmcut -width %(xpixels)d -height %(ypixels)d -left 0 -bottom -1 | pnmtopng -compression 9 > n.png && mv n.png $N && echo "+'"'+r"\\noindent \\includegraphics{$N}\\newpage"+'"'+r"; done; echo '\end{document}') > enlarged.tex && pdflatex enlarged.tex && mv enlarged.pdf .. && cd .. && rm -rf tmp0 && xpdf enlarged.pdf").replace("\t","\\t").replace("\n","\\n").replace("\b","\\b") % globals())
