#!/usr/bin/env python3
"""
src2epub.py - Convert source files to EPUB suitable for large-font configurations on Zenithal Bistable Display (eInk) devices
(Tested on a secondhand 2011 Nook Simple Touch)
v0.3 - Silas S. Brown 2026 - public domain - no warranty

Usage: python src2epub.py code-files [output.epub]
"""

import sys,os,html
from datetime import datetime
from ebooklib import epub  # sudo apt install python3-ebooklib, or pip install ebooklib
import pygments.lexers
from pygments.token import Token as T
from pygments.util import ClassNotFound

css = """body {
  line-height: 1.6;
  margin: 1.25em;
  background: #ffffff;
  color: #333;
  max-width: 100% }
h1 { color: #2c3e50;
  border-bottom: 0.2em solid #3498db;
  padding-bottom: 0.6em;
  font-size: 1.3em;
  word-wrap: break-word }
.metadata {
  color: #7f8c8d;
  font-size: 0.9em;
  margin-bottom: 1.5em;
  word-wrap: break-word }
.line { margin-bottom: 0.3em; width: 100% }
.ln { color: #999; user-select: none }
.code /* don't use code element itself (especially if we're reading TeX source from arXiv or whatever i.e. mostly words) as the Nook Simple Touch ingores non-monospaced font family in code except on spans inside (could put a span around the inside of the whole code block though) */ {
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-all }"""
colours = { # (likely greyscale on eInk)
    T.Keyword: '#008000', # (covers all types)
    T.Name.Class: '#0000FF',T.Name.Function: '#0000FF',T.Name.Builtin: '#008000',T.Name.Exception: '#008000',
    T.String: '#BA2121',
    T.Comment: '#408080',
    T.Comment.Preproc: '#BC7A00',
    T.Operator: '#AA22FF',
    T.Number: '#008000',
    T.Generic.Heading: '#000080',T.Generic.Subheading: '#800080'}

def src2epub(input_files, output_file=None):
    book = epub.EpubBook()
    book.set_identifier(f"src2epub-{datetime.now().timestamp()}")
    book.set_title(', '.join(os.path.basename(i) for i in input_files))
    book.add_author('src2epub converted') # keep together if a filer sorts by author
    book.toc,book.spine,totLines = [],[],0
    book.add_item(epub.EpubItem(uid="style",file_name="styles.css",media_type="text/css",content=css))
    for n,i in enumerate(input_files):
        chapter = epub.EpubHtml(title=os.path.basename(i),file_name=f'content{n}.xhtml',lang='en')
        html,lines = src2html(i)
        totLines += lines
        chapter.set_content(html.encode('utf-8'))
        chapter.add_link(href='styles.css',rel='stylesheet',type='text/css')
        book.add_item(chapter)
        book.spine.append(chapter)
        book.toc.append(epub.Link(f'content{n}.xhtml', os.path.basename(i)+(f' ({os.path.dirname(i)})' if os.path.dirname(i) else ''), f'id{n}'))
    book.add_item(epub.EpubNcx())
    output_file = output_file or f'{os.path.splitext(os.path.basename(input_files[0]))[0]}{os.extsep}epub'
    epub.write_epub(output_file, book)
    print(f"Created {output_file} ({os.path.getsize(output_file) / 1024:.1f} KB), {totLines} paragraph-lines")

def src2html(input_file):
    try: lexer = pygments.lexers.get_lexer_for_filename(input_file)
    except ClassNotFound: lexer = pygments.lexers.TextLexer(stripnl=False)
    code = open(input_file).read()
    lines = code.splitlines()
    highlighted,lineNo,lineToks = [],1,[]
    for token_type,value in lexer.get_tokens(code):
        for i,part in enumerate(value.split('\n')):
            if i:
                highlighted.append((lineNo, tok2html(lineToks)))
                lineNo += 1 ; lineToks = []
            if part: lineToks.append((token_type, part))
    if lineToks: highlighted.append((lineNo, tok2html(lineToks)))
    while len(highlighted) < len(lines): highlighted.append((len(highlighted) + 1, '')) # trailing newlines

    highlighted = '\n'.join(f'<div class="line"><span class="ln">{"&#8199;"*(len(str(len(lines)))-len(str(lineNo)))}{lineNo}</span> <span class="code">{line if line else " "}</span></div>' for lineNo, line in highlighted[:len(lines)])
    # Return value does not need full head etc: it's parsed by ebooklib
    return f"""<html><body><h1>{html.escape(os.path.basename(input_file))}</h1>
    <div class="metadata">Converted: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Lines: {len(lines)}</div>
{highlighted}</body></html>""", len(lines)
    
def tok2html(tokens):
    result = []
    for token_type, value in tokens:
        colour, escaped = [colours[ttype] for ttype in token_type.split() if ttype in colours], html.escape(value).replace('  ',' &nbsp;')
        result.append(f'<span style="color: {colour[0]}">{escaped}</span>' if colour and value.strip() else escaped)
    return ''.join(result)

def main():
    if len(sys.argv) < 2:
        print("Usage: python src2epub.py input_files [output.epub]")
        sys.exit(1)
    hasOut = len(sys.argv)>2 and sys.argv[-1].lower().endswith('epub')
    src2epub(sys.argv[1:len(sys.argv)+(not hasOut)],sys.argv[-1] if hasOut else None)
if __name__ == '__main__': main()
# ruff:noqa: E401,E701,E702
