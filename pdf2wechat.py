#!/usr/bin/env python3
"""
PDF to JPEG converter + compressor
Combines multi-page PDF into single horizontal JPEG
and optimises for a maximum size e.g. WeChat 300KiB
Requirements: poppler-utils (pdftoppm), Pillow

Silas S. Brown 2026, public domain, no warranty
"""

import subprocess,os,tempfile,argparse
from pathlib import Path
from PIL import Image

def pdf_to_images(pdf_path, dpi=150):
    pdf_path = Path(pdf_path)
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(['pdftoppm','-jpeg','-r', str(dpi),'-jpegopt','quality=95',str(pdf_path),str(Path(tmpdir) / 'page')], check=True, capture_output=True)
        return [img.convert('RGB') if img.mode != 'RGB' else img for img in [Image.open(p) for p in sorted(Path(tmpdir).glob('page-*.jpg'))]]

def combine_horizontal(images):
    height = max(img.height for img in images)
    combined = Image.new('RGB', (sum(img.width for img in images),height), (255,255,255))
    x = 0
    for img in images:
        combined.paste(img, (x,(height-img.height)//2))
        x += img.width
    return combined

def find_quality_setting(img, target_path, max_size=300*1024):
    "Binary search for highest quality JPEG under max_size, returns (quality,size)"
    low, high = 10, 95
    quality = low
    best_size = None
    while low <= high:
        mid = (low + high) // 2
        size = save(img, target_path, mid)
        print(f"  Quality {mid:2d}: {size/1024:6.1f} KiB", end="")
        if size <= max_size:
            print(", OK")
            quality,best_size,low = mid,size,mid+1
        else:
            print(", too big")
            high = mid-1
    assert best_size, "Couldn't get the size low enough within quality range (try lower -d DPI)"
    return quality, save(img, target_path, quality)

def save(img, path, quality):
    img.save(path,'JPEG',quality=quality,optimize=True)
    return os.path.getsize(path)

parser = argparse.ArgumentParser(
    description='Convert multi-page PDF to single horizontal JPEG and optimise size for WeChat etc')
parser.add_argument('pdf_file', help='Input PDF file')
parser.add_argument('-o','--output',default=None,help='Output JPEG file (default: inputname_wechat.jpg)')
parser.add_argument('-d','--dpi',type=int,default=150,help='Resolution for PDF conversion (default 150)')
parser.add_argument('-m','--max-size',type=int,default=300,help='Max file size in KiB (default 300 for WeChat)')

def main():
    args = parser.parse_args()
    pdf_path = Path(args.pdf_file)
    output_path = Path(args.output if args.output else pdf_path.with_suffix('').name + '_wechat.jpg')
    images = pdf_to_images(pdf_path, dpi=args.dpi)
    print(f"Found {len(images)} page{'' if len(images)==1 else 's'}")
    combined = combine_horizontal(images)
    quality,size = find_quality_setting(combined,output_path,args.max_size*1024)
    print(f"Done {output_path}, quality {quality}, {size/1024:.1f} KiB ({size} bytes), {combined.width}x{combined.height}")
if __name__ == '__main__': main()
# ruff:noqa: E401,E701
