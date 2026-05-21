#!/usr/bin/env python3

"""Source code to PDF (works in larger print sizes)
with pygments and reportlab

v0.2 - Silas S. Brown 2026 - public domain - no warranty"""

import reportlab # sudo apt install python3-reportlab or pip install reportlab
import pygments, pygments.lexers

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

import sys,os,re

from optparse import OptionParser
parser = OptionParser("src2pdf [options] (input files)")
parser.add_option("--margin",type="int",default=15,help="Margin in mm")
parser.add_option("--size",type="int",default=18,help="Font size in pt")
parser.add_option("--tabs",type="int",default=4,help="Tab spacing")
parser.add_option('--style',default='default',help="pygments style name")

def make_space_non_collapseable(s):
    s = re.sub('(?<=[^ ]) (?=[^ ])',chr(0),s)
    s = s.replace(' ', '&nbsp;<wbr>')
    return s.replace(chr(0),' ')

def convert_pygments_html_to_reportlab(html):
    def replace_span(m):
        style,content = m.groups()
        c = re.search(r'color:\s*#([0-9A-Fa-f]{6})', style)
        if 'bold' in style: content='<b>'+content+'</b>'
        if 'italic' in style: content='<i>'+content+'</i>'
        return f'<font*color="#{c.group(1) if c else "000000"}">{content}</font>'
    html = re.sub(r'<span style="([^"]*)">(.*?)</span>', replace_span, html, flags=re.DOTALL)
    return make_space_non_collapseable(re.sub('</*(div|pre|span)[^>]*>','',html)).replace('font*color','font color')

def src2pdf(input_file,output_file=None):
    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + '.pdf'
    SimpleDocTemplate(
        output_file,
        pagesize=reportlab.lib.pagesizes.A4,
        leftMargin=options.margin,rightMargin=options.margin,
        topMargin=options.margin,bottomMargin=options.margin
    ).build([
        Paragraph(f'<font color="#999999">{make_space_non_collapseable(f"{lineNo+1:4d}  ")}</font>{line}', ParagraphStyle(
            'Code',
            parent=getSampleStyleSheet()['Normal'],
            fontName='Courier',fontSize=options.size,
            leading=options.size*1.4,
            spaceAfter=0,spaceBefore=0,
            leftIndent=options.size*3.5,
            firstLineIndent=-options.size*3.5,
            rightIndent=0,
            textColor=reportlab.lib.colors.black))
        for lineNo,line in enumerate(convert_pygments_html_to_reportlab(
                pygments.highlight(
                    open(input_file,'r',encoding='utf-8').read().replace('\t'," "*options.tabs),
                    pygments.lexers.get_lexer_for_filename(input_file),
                    pygments.formatters.HtmlFormatter(
                        noclasses=True,linenos=False,
                        style=options.style,wrapcode=False)
                )).split('\n'))])
    print(f"Created: {output_file}")

def main():
    global options
    options,args = parser.parse_args()
    for f in args: src2pdf(f)
if __name__ == '__main__': main()
# ruff:noqa:E401,E701
