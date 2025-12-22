
from https://ssb22.user.srcf.net/notes/psion.html (also [mirrored on GitLab Pages](https://ssb22.gitlab.io/notes/psion.html) just in case)

# Large-print notes on EPOC or Symbian

The EPOC operating system is found on the “Psion” range of PDAs (Revo, Series 5, Series 7 etc); Symbian smartphones are a derivative of it. This page describes some methods of getting large-print lesson notes onto such devices, with some reference to other devices such as Windows Mobile PDAs, iPod Touch, etc.

Contents:
* ASCII text
* Graphical slides
* Converting LaTeX output to MBM fonts
* MBM-like approach on other devices

See also [Connecting to a Psion PDA](pconnect.md).

## ASCII text

A large font can be set in EPOC’s Word application (and saved as the normal style under “Paragraph”/“Style gallery”), and then the zoom control can step through 3 sizes around this base size (4 on the Series 7).  My “notesorg” program can assist with sorting out large quantities of notes that are displayed only a small part at a time. There are two versions:
1. a Lua script [notesorg.lua](notesoorg_lua.txt) - save it as notesorg.lua in C:\System and download [the Macro5 macro that uses it](notesorg_macro.txt) (see comments at the start of this for setup instructions). You will need Macro5 and the Lua 5 OPL kit (C:\Lua5 is not necessary).
2. the older, Python 2 version [notesorg.py](notesorg.py) (see comments at the start of the script for usage)—you need [epocpython 2.1](https://ssb22.user.srcf.net/notes/epocpython02.zip) (mirrored here due to increasing accessibility issues on SourceForge download pages) and Macro5.

That version of epocpython has a console that can be enlarged up to about 35-point, which may be useful if you also need to run Python reference-lookup programs etc (if it gets too slow, clear the screen). However, you’ll need to set aside at least 2M of memory for files and runtime, and more if you keep the Python libraries, and it’s not as fast as OPL or Lua. You might be better off writing your programs in OPL or Lua and using Macro5’s copy and paste functions to interface to the wordprocessor, which can then act as your large-print console.

### Reading (and non-ASCII)

Simon Quinn developed a Shareware program called “Ebook” from 2000 through 2002, then published a universal registration code in 2002 making it “freeware” (although I paid to register before that so I haven’t tested the universal code). Ebook can be useful for reading English text, and some compression is available via its `tcr` program that can run on GNU/Linux.

Smaller amounts of text can simply be placed in the built-in “Word” app for reading, especially on the larger machines.

Besides ASCII, the Psion also supports characters from the “Code Page 1252” set, which includes curved quotes, em-dash, bullet, section and paragraph symbols, and accented letters for Western European languages—use `iconv -c -f UTF8 -t CP1252//TRANSLIT` to convert in from UTF-8, and `iconv -f CP1252 -t UTF8` to convert back (you might then like to run `diff -u` to check which characters were lost, unless you want to do without the `-c` and get error messages).

Another “ex-Shareware” program that now has a universal registration code is Neuon nConvert. A full installation is quite large (~1M), but it can be installed to a CF card if you have one. nConvert can import RTF with basic formatting (bold, italic, underline and size), but if the RTF contains Unicode markup then it’s reported as “corrupt” and not converted at all. LibreOffice includes Unicode in RTF export, but if you can make a CP1252-encoded LaTeX file and put `\usepackage[raw]{inputenc}` in its preamble, you can then use `latex2rtf` to create an RTF file that nConvert should be able to open. When using this method, LaTeX-style quotes are correctly converted to CP1252 quotes, but em-dashes are dropped, so it’s better to use UTF-8 em-dashes and convert to CP1252 code 151 instead of using the standard LaTeX representation. To work around a bug in `latex2rtf` that ends paragraphs at the first outermost right-brace, simply add a pair of braces around each paragraph (this can be after the initial `\raggedright`, which is recommended for large-print use).

### Large clock

You can type this into OPL:
```
PROC m:
  gAt gWidth/2-120,gHeight/2-20
  gClock on,11,0,"%H%:1%T%:2%S",268436072,9
  get
ENDP
```
or (larger still) install Clock5, but that takes more RAM.

## Graphical slides

Sometimes it can be useful to have notes that are not just ASCII text or CP1252. You can give yourself a graphical slideshow of notes if you generate the slides to the right screen dimensions, e.g. Series 7’s 640x480 resolution gives approx. 163x122mm at 100dpi; Revo’s 480x160 resolution gives approx. 115x38mm at 106dpi (but if you’re using TeX then Metafont doesn’t get on well with 106dpi so try 4.8x1.6in at 100dpi and multiply your magnification factor by 1.06); Series 5’s 640x240 gives approx. 134x50mm at 122dpi.
* The scripts described in [this repository's main README](README.md) can help generate the unusual page sizes, and if using TeX you can optimise for the display’s DPI by adding `-D 100` or whatever to the `dvips` command, and in teTeX 2 use
```
\usepackage[T1]{fontenc}
```
to ensure it uses bitmaps not outlines.
* You can also use a desktop application to print to PDF with a custom paper size that corresponds with the device’s screen size. If your application crashes when setting a custom paper size, try using normal A4 paper and set left and bottom margins to 0 and top and right margins to 297mm-H and 210mm-W respectively (where H and W are the height and width of the device); the converter to MBM (below) will then crop the page automatically. If your application cannot print with large fonts, divide the paper size by the zoom factor you want, and pass this zoom factor as an extra parameter to tex2mbm.py (below). For example:

Zoom factor - A4 top,right margins (mm) for - Command

Series 7 - Revo

1.5 - 215.67, 101.33 - 271.67, 133.33 - `tex2mbm.py 1.5 file.pdf`

1.7 - 225.24, 114.12 - 274.65, 142.35 - `tex2mbm.py 1.7 file.pdf`

2 - 236, 128.5 - 278, 152.5 - `tex2mbm.py 2 file.pdf`

3 - 256.33, 155.67 - 284.33, 171.67 - `tex2mbm.py 3 file.pdf`

Remember that the above measurements are for A4 size, **not Letter size**.

If you just want to print to A4 landscape but want maximum compatibility with old PDF readers (e.g. Acrobat Reader 3 on a Toshiba Libretto), you can post-process the PDF file like this:
```

pdftops myfile.pdf
ps2ps myfile.ps myfile-2.ps
ps2pdf12 myfile-2.ps
```
This might significantly increase the file size though.

### Using the MBM format

EPOC PDF viewers are slow, but you can convert to EPOC’s own MBM format using bmconv.exe (on Wine or Cygwin). My Python 2 script [tex2mbm.py](tex2mbm.py) automates the conversion (handling quirks etc); you may need to change the variables at the top before running. The simplest use is to run it with a single .ps or .pdf file of the device’s page size; this will generate one or more MBM files (multiple files are used if it can’t fit all the bitmaps into one) and then [MbmShow](MbmShow.txt) is an OPL program that will display them with double-buffering (see comments at the start for setup; press any key to page forwards, or press Escape to page backwards). You can have multiple instances of MbmShow running simultaneously by making multiple copies of the .opo file.

## Converting LaTeX Output to MBM Fonts

If you have a lot of graphical or non-ASCII documents to keep on the EPOC machine (too many for the above MBM-slideshow method) then this approach might be useful. The idea is to typeset the documents in LaTeX, but only one word per page. Each page is then trimmed to make an image, and duplicate images are removed to leave a “font” of unique images that can then be used to print the document on the device. If there are too many glyphs for one MBM file then the script can split it across several; colour glyphs are also supported. Any TeX can be used, as long as you can arrange for `\newpage` to be added after each word.

The script to run on the Unix box is [tex2mbm.py](tex2mbm.py) (as above). It requires [latex-papersize.py](latex-papersize.py) (version 1.4 or later), and it requires Symbian’s Bmconv.exe (and Wine, unless you’re on Cygwin in which case you may have difficulty with some of the more specialist TeX packages). It also requires netpbm, GhostScript, and of course TeX (although if your most powerful system doesn’t have a full TeX installation then it’s possible to run TeX on one system and the rest on another by setting a variable, and it’s also possible to separate the Mbmconv part from the rest of the processing).

The OPL program to view the results is [MbmShow](MbmShow.txt) as above (see comments at the start for setup). It will prompt for a document number (unless you passed only one document to tex2mbm.py) and will then show it; press any key to go forwards or Escape to go backwards. If you press Escape in the document-number dialogue, MbmShow will prompt for an MBM file to view instead.

### Faster version of tex2mbm.py

[tex2mbm-fast.py](tex2mbm-fast.py) is faster, but it is more restrictive about its input: it can be used **only** for .tex input (no .ps or .pdf input), and expects all TeX source files to have `%StartWord` and `%EndWord` (on lines by themselves) around each word, in addition to putting each word on its own page. (The `\newpage` or `\clearpage` commands must be included within the `%StartWord`..`%EndWord` pair.) Your script *must* know in advance where all the pagebreaks will be. It will be using a very small paper size, so you might want to use `\hbox` and similar commands to stop TeX breaking a long word onto a second page without your knowing (because if that happens, tex2mbm’s idea of which word is which will be wrong from that point onward). Duplicate pages are detected only if their TeX source is identical (not just if the output is identical). The LaTeX preamble and other setup should be the same in all files. Additionally, any page that uses colour must contain “`%Colour`” in the TeX source, and any that uses greyscale must contain “`%Grey`”, otherwise it will be set in black and white (again to save time testing the bitmaps).

## MBM-like approach on other devices

The above script tex2mbm-fast.py can also write simple HTML+images for phones etc, as well as being able to write an indexed binary file of compressed XBM images, which can be displayed on Windows Mobile and other devices with this script [XBMshow.py](XBMshow.py) (Python and Tkinter required).

Copyright and Trademarks:
All material © Silas S. Brown unless otherwise stated.
Acrobat is an Adobe trademark.
HTC and Touch are trademarks of HTC Corporation.
Linux is the registered trademark of Linus Torvalds in the U.S. and other countries.
Python is a trademark of the Python Software Foundation.
SourceForge is a trademark of VA Software Corporation.
Symbian was a trademark of the Symbian Foundation until its insolvency in 2022 and I was unable to find what happened to the trademark after that.
TeX is a trademark of the American Mathematical Society.
Toshiba is a trademark of Tokyo Shibaura Denki Kabushiki Kaisha, also called Kabushiki Kaisha Toshiba.
Unicode is a registered trademark of Unicode, Inc. in the United States and other countries.
Unix is a trademark of The Open Group.
Windows is a registered trademark of Microsoft Corp.
Zoom is a trademark of Zoom Video Communications, Inc.
Any other [trademarks](https://ssb22.user.srcf.net/trademarks.html) I mentioned without realising are trademarks of their respective holders.
