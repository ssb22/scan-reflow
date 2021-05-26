/*

Split scanned images into words, scale and re-flow them
(c) Silas S. Brown, 2005-2009, 2012, 2021.  Version 1.391

Compile by typing:  gcc reflow.c -o reflow
Then run by typing: ./reflow

Run without arguments to see syntax

Uses Unix libraries; assumes shell is bash; requires netpbm
and requires pdftex unless using --html
(if your pdftex crashes, try upgrading your TeX installation,
e.g. for tetex go to www.tug.org/teTeX )

Known bugs: Should do more checks for I/O errors etc.

-------------
    
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

Where to find history:
on GitHub at https://github.com/ssb22/scan-reflow
and on GitLab at https://gitlab.com/ssb22/scan-reflow
and on BitBucket https://bitbucket.org/ssb22/scan-reflow
and at https://gitlab.developers.cam.ac.uk/ssb22/scan-reflow
and in China: https://gitee.com/ssb22/scan-reflow

*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

enum ProgramVariables {
  OriginalDPI = 600,
#define Millimetres(m) ((int)((m)*OriginalDPI/25.4+0.5))
  FuzzSize = Millimetres(0.4), /* 2 pixels doesn't always seem to be enough, neither does 0.3mm or even 0.5mm with some scans, but 0.8mm removes the dots from i's (and 0.5mm does too at smaller print sizes) */
  FuzzSizeForOutput = Millimetres(0.2), /* can set o/p to be stricter than boundary-finding (to preserve some smaller diacritics-on-italics etc) */
  Remove_Verticals_Larger_Than = Millimetres(25.4),
  LineGap = Millimetres(0.635), /* minimum space between 2 lines (increased slightly to cope with slight baseline shifts due to font changes in some interlinear material - see LinegapTolerant) */
  LinegapTolerant=1,
  WordGap = Millimetres(1), /* minimum space between words */
  MaxSatelliteSize = Millimetres(0.85), /* objects smaller than this are merged with others */
  MaxSatelliteDistance = /*Millimetres(3)*/ 0, /* if they are closer than this distance (0=no limit) - this is supposed to avoid merging thin lines etc with their nearest text; however in practice it means if a document has more fuzz than could be removed then some of it can get the interlinear out of sync, whereas thin lines isn't a big problem, so I'm setting it to 0 */
  SmallObject = Millimetres(3), /* typical "smallest object" size (used to stop columns-within-columns recursion, allow for margins, etc) */
  LargestVerticalMargin=Millimetres(2.5), /* larger vertical margins are trimmed */
  VerticalMarginTrimTo=Millimetres(1), /* this is what they are trimmed to (NB LargestVerticalMargin should be greater than this otherwise the base line could be interfered with unnecessarily) */
  Max_Images_Per_Paragraph = 500 /* to avoid exceeding TeX limits */
};

int AvailableWidth = (210-20)*720/254,
  AvailableHeight = (297-20)*720/254; /* points */

typedef struct{int width,widthBytes,height;char* data;} Pbm;

/* Remove artifacts that can get in the way of the splitting
   operations.  These functions could do with being faster
   (more than 1 bit at a time) */
const int bitPos[]={128,64,32,16,8,4,2,1};
inline int getBit(const Pbm* pbm,int x,int y) {
  if(x<0||y<0||x>=pbm->width||y>=pbm->height) return 0;
  else return pbm->data[y*pbm->widthBytes+(x/8)] & bitPos[x%8];
}
inline void clearBit(Pbm* pbm,int x,int y) {
  pbm->data[y*pbm->widthBytes+(x/8)] &= (0xFF-bitPos[x%8]);
}
void debug_horizLine(Pbm* pbm,int x1,int x2,int y) {
  /* (for debugging interlinear) (loop over a few y positions because a thin horiz line can be scaled out) */
  int yy; for(;x1<=x2 && x1<pbm->width;x1++) for(yy=y-2; yy<y+2 && yy<pbm->height; yy++) if(x1>=0 && yy>=0) pbm->data[yy*pbm->widthBytes+(x1/8)] |= bitPos[x1%8];
}
void removeFuzz(Pbm* pbm, int fuzzSize) {
  int x,y,i,fuzz;
  for(y=0; y<pbm->height; y++) for(x=0; x<pbm->width; x++) for(fuzz=fuzzSize; fuzz>=1; fuzz--) {
    /* trace around the boundary of a fuzz*fuzz square (top left at x,y) - if boundry is clear, clear the inside.  (note: 'fuzz' in a loop to cope with areas with a lot of fuzz) */
    int maybeFuzz=1;
    for(i=-1;i<=fuzz;i++)
      if(getBit(pbm,x+i,y-1) || getBit(pbm,x+i,y+fuzz) || getBit(pbm,x-1,y+i) || getBit(pbm,x+fuzz,y+i)) { maybeFuzz=0; break; }
    if(maybeFuzz) {
      int xi,yi;
      for(xi=x;xi<x+fuzz;xi++) for(yi=y;yi<y+fuzz;yi++) if(getBit(pbm,xi,yi)) clearBit(pbm,xi,yi); /* do leave the 'if' in, in case go over bounds */
      x += (fuzz-1); /* might as well */
      break; /* out of 'fuzz' loop */
    }
  }
}
extern int rotationMode;
void removeVertLines(Pbm* pbm) {
  int x,y,i;
  for(y=0; y<=pbm->height-Remove_Verticals_Larger_Than; y++) for(x=0; x<pbm->width; x++) {
    int maybeLine=1;
    for(i=y; i<y+Remove_Verticals_Larger_Than; i++)
      if(!getBit(pbm,x,i)) { maybeLine=0; break; }
    if(maybeLine)
      for(i=y; i<pbm->height && getBit(pbm,x,i); i++) {
        clearBit(pbm,x,i);
        if(rotationMode) {
          if(x) clearBit(pbm,x-1,i);
          if(x<pbm->width-1) clearBit(pbm,x+1,i);
        }
      }
  }
}

Pbm* pngtoPbm(const char* png_filename) {
  Pbm* newPbm=(Pbm*)malloc(sizeof(Pbm)); FILE* p; int size;
  char* data;
  setenv("File",png_filename,1);
  // (NB: use = not == in 'test', for maximum compatibility across sh versions)
  p=popen("export TmpFile=$(mktemp /tmp/tmppnmXXXXXX)\n"
"pngtopnm $File > $TmpFile; export Type=$(head -1 < $TmpFile)\n"
"if test $Type = P6; then\n"
"  ppmtopgm $TmpFile | pgmtopbm -threshold\n"
"elif test $Type = P5; then\n"
"  pgmtopbm -threshold $TmpFile\n"
"else\n"
"  cat $TmpFile\n"
"fi ; rm $TmpFile","r"); /* could also add "| pnmcrop -white" after "fi" if needs to be cropped (but can be good to leave some margins) */
  fscanf(p,"P4\n%d %d\n",&(newPbm->width),&(newPbm->height));
  newPbm->widthBytes=(newPbm->width+7)/8;
  size=newPbm->height*newPbm->widthBytes;
  data = newPbm->data = malloc(size);
  while(size) {
    size_t read=fread(data,1,size,p);
    data += read; size -= read;
  }
  pclose(p);
  return newPbm;
}

int faster=0;
void Pbmtopng(const Pbm* pbm,const char* png_filename,
              int left,int top,int width,int height) {
  char* s; FILE* p;
  int bytesPerRow=(pbm->width+7)/8;
  const char* compression=(faster?"":" -compression 9");
  asprintf(&s,"pnmcut %d 0 %d %d | pnmtopng%s > %s",left,width,height,compression,png_filename);
  printf("%s      \r",s); fflush(stdout);
  p=popen(s,"w");
  fprintf(p,"P4\n%d %d\n",pbm->width,height);
  fwrite(pbm->data+top*bytesPerRow,bytesPerRow,height,p);
  pclose(p);
  free(s);
}

void pngtopng(const char* src,const char* dest,
              int left,int top,int width,int height) {
  char* s;
  asprintf(&s,"pngtopnm '%s' | pnmcut %d %d %d %d | pnmtopng%s > %s",src,left,top,width,height,(faster?"":" -compression 9"),dest);
  puts(s); system(s); free(s);
}

inline int getByte(const Pbm* pbm,int xDiv8,int y,int slightRotateDir,int slightRotateEvBytes) {
  if(slightRotateDir) {
    y += slightRotateDir*xDiv8/slightRotateEvBytes;
    if(y<0 || y>=pbm->height) return 0; /* white */
  }
  return pbm->data[y*pbm->widthBytes+xDiv8];
}

int horizBeam(const Pbm* pbm,int y,int leftX,int rightX,
              int beamWidth,int tolerant,
              int slightRotateDir,int slightRotateEvBytes) {
  /* Returns 1 if the beam got through.
     tolerant: 0 = all rows in beamWidth must be white to
     pass, 1 = all must be black simultaneously to block.
     If tolerant, returns 2 if tolerant=0 would also have
     worked.
  */
  int minY,maxY,firstByteMask=0xFF,lastByteMask=0xFF,i,yi;
  int retVal=2;
  minY = y-(beamWidth>>1); if(minY<0) minY=0;
  maxY = minY+beamWidth-1; if(maxY>=pbm->height) maxY=pbm->height-1;
  for(i=0; i<(leftX%8); i++) firstByteMask>>=1;
  for(i=7; i>(rightX%8); i--) lastByteMask = (lastByteMask<<1)&0xFF;
  leftX/=8; rightX/=8;
  for(i=leftX; i<=rightX; i++) {
    int tolerantRow=0xFF, intolerantRow=0;
    for(yi=minY; yi<=maxY; yi++) {
      int byte=getByte(pbm,i,yi,slightRotateDir,slightRotateEvBytes);
      tolerantRow&=byte; intolerantRow|=byte;
    }
    if(i==leftX) { tolerantRow&=firstByteMask; intolerantRow&=firstByteMask; }
    /* NOT 'else'! */ if(i==rightX) { tolerantRow&=lastByteMask; intolerantRow&=lastByteMask; }
    if(tolerant?tolerantRow:intolerantRow) return 0;
    if(intolerantRow) retVal=1;
  }
  return retVal;
}

int vertBeam(const Pbm* pbm,int x,int topY,int bottomY,
              int beamWidth,int slightRotateDir,int slightRotateEvBytes) {
  int YbeamWidth=bottomY-topY+1,leftX,rightX;
  leftX=x-(beamWidth>>1); if(leftX<0) leftX=0;
  rightX = leftX+beamWidth-1; if(rightX>=pbm->width) rightX=pbm->width-1;
  return horizBeam(pbm,topY+(YbeamWidth>>1),leftX,rightX,YbeamWidth,0,slightRotateDir,slightRotateEvBytes);
}

void eliminateSatelliteObjects(int* beamAverages,const char* beamResult,int offset,int intolerantBeamWidth) {
  /* go from one av to next av: if BLOCKED beams < MaxSatelliteSize, delete either the 1st or the 2nd whichever is nearest to the obj (as long as it's within MaxSatelliteDistance - don't want false positives from isolated lines etc) */
  int i,found;
  if(intolerantBeamWidth) intolerantBeamWidth-=1;
  do {
    found=0;
    for(i=0; beamAverages[i+1]!=-1; i++) {
      int objStart=beamAverages[i], objEnd=beamAverages[i+1];
      while(objStart<objEnd && beamResult[objStart-offset]) objStart++;
      while(objEnd>objStart && beamResult[objEnd-offset]) objEnd--;
      if(objEnd-objStart < MaxSatelliteSize+intolerantBeamWidth) { /* adding intolerantBeamWidth because it will block for that many EXTRA pixels to the left or top (see also the -=1 above) */
        int edgeToDelete, gap;
        if(i && beamAverages[i+1] - objEnd > objStart - beamAverages[i]) {
          edgeToDelete = i; gap = objStart-beamAverages[i];
        } else { edgeToDelete = i+1; gap=beamAverages[i+1]-objEnd; }
        if(!MaxSatelliteDistance || gap < MaxSatelliteDistance) {
          int j=edgeToDelete;
          while(beamAverages[j]!=-1) j++;
          memmove(&(beamAverages[edgeToDelete]),&(beamAverages[edgeToDelete+1]),(j-edgeToDelete)*sizeof(int));
          found = 1; break;
        }
      }
    }
  } while(found);
}

void beamEnhance(char* beamResult,int length) {
  /* Does a kind of "edge enhance".  Thin horizontal lines
 (e.g. footnote separators) may not otherwise be detected at
 all, which can sometimes lead to nearby lines not being
 split into words.  Look for complete->partial->complete
 patterns as well as the usual
 partial-or-complete->none->partial-or-complete. */
  int i;
  for(i=1; i<length; i++) if(beamResult[i-1]==2 && beamResult[i]==1) {
    int j;
    for(j=i; j<length && beamResult[j]==1; j++);
    if(j==length || beamResult[j]==2)
      /* got one */
      while(j>=i) beamResult[--j] = 0;
  }
}

/* Takes an array of T/F "could the beam get through" and
 gives 1-dimensional split points (ending with -1).
*/
int* objectEdges(const char* beamResult,int length,int offset) {
  int lastBeamResult=1, beamStart=0, i, retPtr=0,
    *retVal=malloc(length*sizeof(int)+1);
  for(i=0; i<length; i++) {
    if(beamResult[i]) {
      if(!lastBeamResult) beamStart = i;
    } else if(lastBeamResult) {
      int o=(beamStart ? ((beamStart+i) >> 1) : (i-SmallObject));
      /* the i-smallObject is a special case to eliminate excessive top margins that sometimes have a side-effect of causing the second line in interlinear mode to be ignored because it's smaller than the combined size of first line and large top margin; it also ensures that centred single interlinear words are processed properly - see comment below about "CENTERED paragraph" */
      if(o<0) o=0;
      retVal[retPtr++] = o + offset;
    }
    lastBeamResult = beamResult[i];
  }
  /* retVal[0] = offset; */
  /* retVal[retPtr++] = offset + length-1; */ if(lastBeamResult) {
    int a=beamStart+SmallObject; /* avoid wide bottom margins */
    int b=(beamStart+length)>>1;
    retVal[retPtr++] = ((a<b)?a:b) + offset;
  } else retVal[retPtr++] = offset + length-1;
  /* (switch to the commented-out code if want to guarantee that ALL pixels are included in the output) */
  retVal[retPtr] = -1;
  return retVal;
}

int* horizObjectEdges(const Pbm* pbm,int topY,int bottomY,
                      int leftX,int rightX,
                      int beamWidth,int tolerant,
                      int slightRotateDir,int slightRotateEvBytes) {
  char* result=malloc(bottomY-topY+1); int y;
  int* ret;
  for(y=topY; y<=bottomY; y++) result[y-topY] = horizBeam(pbm,y,leftX,rightX,beamWidth,tolerant,slightRotateDir,slightRotateEvBytes);
  if(tolerant) beamEnhance(result,bottomY-topY+1);
  ret=objectEdges(result,bottomY-topY+1,topY);
  eliminateSatelliteObjects(ret,result,topY,tolerant?0:beamWidth);
  free(result); return ret;
}

int* vertObjectEdges(const Pbm* pbm,int topY,int bottomY,
                     int leftX,int rightX,int beamWidth,
                     int slightRotateDir,int slightRotateEvBytes) {
  char* result=malloc(rightX-leftX+1); int x; int* ret;
  for(x=leftX; x<=rightX; x++)
    result[x-leftX] = vertBeam(pbm,x,topY,bottomY,beamWidth,slightRotateDir,slightRotateEvBytes);
  ret=objectEdges(result,rightX-leftX+1,leftX);
  eliminateSatelliteObjects(ret,result,leftX,beamWidth); /* doing this in vertObjectEdges as well as horizObjectEdges, because lots of small dots (e.g. in a table-of-contents list at the top of the page) can confuse the find-best-rotation system and anyway there's no point enlarging them all as separate units */
  free(result); return ret;
}

typedef struct {int top,bottom,left,right;} Bounds;

int interlinearMode=0, singleCol_mode=0;

inline int similarWidth(int w1,int w2) {
  /* Used as an extra check before merging interlinear
     lines.  Needs to be tolerant of differences, but avoid
     silly things like 2 words on one line and 10 on the
     next. */
  return (w1 <= 3*w2 && w2 <= 3*w1);
}

#ifdef DEBUG_INTERLINEAR
int debug_interlinear = 0;
#endif
void generalObjectEdges(const Pbm* pbm,int isVert,
                        int topY,int bottomY,
                        int leftX,int rightX,
                        int beamWidthHoriz,int beamWidthVert,int horizTolerant,
                        int slightRotateDir,int slightRotateEvBytes,
                        Bounds* *boundsList,int* listPtr,int* listSize,int* score,int stopIfNoSplit) {
  int *edges, i, splittingAllowed, haveSplitHoriz=0, beginListPtr=*listPtr, beginScore=*score, prevOldListPtr,widthForInterlinear=0;
  if(isVert) edges=vertObjectEdges(pbm,topY,bottomY,leftX,rightX,beamWidthVert,slightRotateDir,slightRotateEvBytes);
  else edges=horizObjectEdges(pbm,topY,bottomY,leftX,rightX,beamWidthHoriz,horizTolerant,slightRotateDir,slightRotateEvBytes);

  for(splittingAllowed=(stopIfNoSplit==2?0:1);splittingAllowed>=0;splittingAllowed--) for(i=0; edges[i+1]!=-1; i++) {
    int breakAndTryWithNoSplitting=0;
    if(splittingAllowed && (edges[i+1]-edges[i] >= SmallObject || (isVert?topY-bottomY:rightX-leftX) >= SmallObject) && (!stopIfNoSplit || (stopIfNoSplit==1 && edges[2]!=-1))) {
      int oldListPtr = *listPtr, lastWidthForInterlinear = widthForInterlinear, oldScore = *score;
      generalObjectEdges(pbm,!isVert,isVert?topY:edges[i],isVert?bottomY:edges[i+1],isVert?edges[i]:leftX,isVert?edges[i+1]:rightX,beamWidthHoriz,beamWidthVert,horizTolerant,slightRotateDir,slightRotateEvBytes,boundsList,listPtr,listSize,score,
                         /* stopIfNoSplit: if we're in singleCol_mode then don't split any further than the next vertical anyway, otherwise if there's only 2 edges */
                         (singleCol_mode && !isVert)?2:(edges[2]==-1)
                         );
      if(interlinearMode && !isVert &&
         /* make sure we don't treat full-page horizontal lines as part of the interlinear */
         (*listPtr-oldListPtr > (singleCol_mode?1:3) /* enough words */
          || (*boundsList)[(*listPtr)-1].right-(*boundsList)[oldListPtr].left < ((leftX+rightX)>>1)) /* line ends early (as in last word of paragraph) (subtracting the left bound because some interlinear material can have 1 word left over on the last line of a CENTRED paragraph) */
         ) widthForInterlinear=((*boundsList)[(*listPtr)-1].right-(*boundsList)[oldListPtr].left);
      else widthForInterlinear=0;
      if(isVert && *listPtr > oldListPtr+1 && *listPtr < oldListPtr+5) { /* The recursive call split horizontally.  To avoid chopping accents off letters, check that ALL columns are being split horizontally, otherwise back off. (the clause after && was added to stop false alarms when splitting columns etc) */
        if(i && !haveSplitHoriz) breakAndTryWithNoSplitting=1;
        haveSplitHoriz=1;
      } else if(isVert && *listPtr <= oldListPtr+1 && haveSplitHoriz) breakAndTryWithNoSplitting=1;
      else if(/* [isVert will always be false if] */ widthForInterlinear && lastWidthForInterlinear && i && similarWidth(widthForInterlinear,lastWidthForInterlinear)) {
        /* splitting horizontally at this level, and the vertical split at level below seems to have found 2 successive interlinear lines - re-do them as a single line */
#ifdef DEBUG_INTERLINEAR
        printf("Interlinear merge (%d,%d,%d) from ptr %d\n",edges[i-1],edges[i],edges[i+1],prevOldListPtr);
#endif
        *listPtr = oldListPtr = prevOldListPtr;
        int tempScore=0;
        interlinearMode=0;
        if (((edges[i]-edges[i-1]) > 2*(edges[i+1]-edges[i]) || (edges[i]-edges[i-1])*2 < (edges[i+1]-edges[i])) && edges[i+2]!=-1) {
          /* Hack: If the two lines are significantly different heights then it's probably a mistaken split (taking the tops off disconnected hanzi, or picking up on left-over fuzz instead of pinyin top line), so merge with NEXT line as well. */
          /* vertical-split this and next 2 lines together */
          generalObjectEdges(pbm,1,edges[i-1],edges[i+2],leftX,rightX,beamWidthHoriz,beamWidthVert,horizTolerant,slightRotateDir,slightRotateEvBytes,boundsList,listPtr,listSize,&tempScore,2/*don't split ANY further*/);
#ifdef DEBUG_INTERLINEAR
          if(debug_interlinear) { debug_horizLine((Pbm*)pbm,leftX,rightX,edges[i]); debug_horizLine((Pbm*)pbm,leftX,rightX,edges[i+1]); }
#endif
          i++;
        } else {
          /* vertical-split this and next line together */
          generalObjectEdges(pbm,1,edges[i-1],edges[i+1],leftX,rightX,beamWidthHoriz,beamWidthVert,horizTolerant,slightRotateDir,slightRotateEvBytes,boundsList,listPtr,listSize,&tempScore,2/*don't split ANY further*/);
#ifdef DEBUG_INTERLINEAR
          if(debug_interlinear) debug_horizLine((Pbm*)pbm,leftX,rightX,edges[i]);
#endif
        }
        interlinearMode=1;
        lastWidthForInterlinear = widthForInterlinear = 0;
        *score = oldScore + 2*tempScore + 10; /* if interlinear boxes count as 2, scoring is not biased in favour of disrupting the interlinear.  Add something to bias in favour of finding more interlinear lines. */
      }
      prevOldListPtr = oldListPtr;
    } else {
      if(*listPtr==*listSize) {
        *listSize <<= 1;
        *boundsList=realloc(*boundsList,*listSize*sizeof(Bounds));
      }
      (*boundsList)[*listPtr].top=(isVert?topY:edges[i]);
      (*boundsList)[*listPtr].bottom=(isVert?bottomY:edges[i+1]);
      (*boundsList)[*listPtr].left=(isVert?edges[i]:leftX);
      (*boundsList)[*listPtr].right=(isVert?edges[i+1]:rightX);
      (*listPtr)++;
      (*score)++;
    }
    if(breakAndTryWithNoSplitting) {
      *listPtr = beginListPtr;
      *score = beginScore;
      break; /* do again with splittingAllowed=0 */
    } else if(edges[i+2]==-1) splittingAllowed=-1; /* we finished, so no need to run with splittingAllowed=0. (+2 because just about to do i++) */
  }
  free(edges);
}

Bounds* generalObjectEdges_wrapper(int* length,int* score,const Pbm* pbm,int beamWidthHoriz,int beamWidthVert,int horizTolerant,int slightRotateDir,int slightRotateEvBytes) {
  int listSize = 512;
  Bounds* boundsList = malloc(listSize*sizeof(Bounds));
  printf("Calculating bounds at rotation 1/%d    \r",slightRotateEvBytes*slightRotateDir); fflush(stdout);
#ifdef DEBUG_INTERLINEAR
  puts("");
#endif
  *length=0; *score=0;
  generalObjectEdges(pbm,!singleCol_mode,0,pbm->height-1,0,pbm->width-1,beamWidthHoriz,beamWidthVert,horizTolerant,slightRotateDir,slightRotateEvBytes,&boundsList,length,&listSize,score,0);
  return boundsList;
}

int rotationMode = 1;
int rotationsToTry[] = {143, 80, 55, 42, 34, 29, 25, 22, 19, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 0}; /* From map(lambda x:round(1/math.tan(math.pi*x/18000.0)/8),range(1,200,4)). The approximation starts getting inaccurate if rotated as much as this; would need several levels of fine-tuning to compensate */
Bounds* findBestRotation(int* length,const Pbm* pbm,int beamWidthHoriz,int beamWidthVert,int horizTolerant) {
  int slightRotateDir,i,bestRotation=0;
  Bounds* bestBounds; int bestLength,bestScore;
  bestBounds = generalObjectEdges_wrapper(&bestLength,&bestScore,pbm,beamWidthHoriz,beamWidthVert,horizTolerant,0,0);
  if(rotationMode) for(slightRotateDir=-1; slightRotateDir<=1; slightRotateDir+=2)
    for(i=0; rotationsToTry[i]; i++) {
      Bounds* tryBounds; int tryLength,tryScore;
      tryBounds = generalObjectEdges_wrapper(&tryLength,&tryScore,pbm,beamWidthHoriz,beamWidthVert,horizTolerant,slightRotateDir,rotationsToTry[i]);
      if(tryScore > bestScore) {
        free(bestBounds);
        bestLength = tryLength; bestBounds = tryBounds;
        bestScore = tryScore;
        bestRotation = rotationsToTry[i] * slightRotateDir;
      } else {
        free(tryBounds);
        if(tryLength < bestLength*2/3) break;
      }
    }
  static int counter=0;
  printf("Image %d: using rotation 1/%d                 \n",++counter,bestRotation);
#ifdef DEBUG_INTERLINEAR
  /* re-do the rotation we found and draw the lines in. (Don't draw lines above because there's still other rotations to try.) */
  debug_interlinear=1; free(generalObjectEdges_wrapper(&bestLength,&bestScore,pbm,beamWidthHoriz,beamWidthVert,horizTolerant,(bestRotation<0)?-1:(bestRotation?1:0),(bestRotation<0)?-bestRotation:bestRotation)); debug_interlinear=0;
#endif
  if(bestRotation) for(i=0; i<bestLength; i++) {
    bestBounds[i].top += (bestBounds[i].left>>3)/bestRotation;
    bestBounds[i].bottom += (bestBounds[i].right>>3)/bestRotation;
    if(bestBounds[i].top<0) bestBounds[i].top=0;
    if(bestBounds[i].bottom>=pbm->height) bestBounds[i].bottom=pbm->height-1;
  }
  *length = bestLength; return bestBounds;
}

void crop(const Pbm* pbm,Bounds* bounds) {
  /* "pnmcrop -white" may spoil baselines etc, but could do L/R.  Doing here so program knows about new co-ords (avoid false oversized-images alarms) */
  int y,found,realYBorder;
#ifdef DEBUG_INTERLINEAR
  return;
#endif
  for(found=0; bounds->left<bounds->right; bounds->left++) {
    for(y=bounds->top; y<=bounds->bottom; y++)
      if(getBit(pbm,bounds->left,y)) { found=1; break; }
    if(found) break;
  }
  for(found=0; bounds->right>bounds->left; bounds->right--) {
    for(y=bounds->top; y<=bounds->bottom; y++)
      if(getBit(pbm,bounds->right,y)) { found=1; break; }
    if(found) break;
  }
  /* Trim vertical margins only if they're too big.  This stops silly things happening when the last line of a paragraph is followed by a huge amount of whitespace, but it still allows some whitespace between the lines. */
  realYBorder=bounds->top; for(found=0; realYBorder<bounds->bottom; realYBorder++) {
    for(y=bounds->left; y<=bounds->right; y++)
      if(getBit(pbm,y,realYBorder)) { found=1; break; }
    if(found) break;
  }
  if(realYBorder-LargestVerticalMargin > bounds->top) bounds->top = realYBorder-VerticalMarginTrimTo;
  realYBorder=bounds->bottom; for(found=0; realYBorder>bounds->top; realYBorder--) {
    for(y=bounds->left; y<=bounds->right; y++)
      if(getBit(pbm,y,realYBorder)) { found=1; break; }
    if(found) break;
  }
  if(realYBorder+LargestVerticalMargin < bounds->bottom) bounds->bottom = realYBorder+VerticalMarginTrimTo;
}

int screenMode = 0, use_original = 0, hadPaperColour = 0;

inline int max(int a,int b) { return (a>b)?a:b; }
inline int min(int a,int b) { return (a<b)?a:b; }

int wordCounter=0, /* in sync with filenames */
  htmlWordCounter=0, /* ditto */
  realWordCounter=0, /* not necessarily in sync after edits */
  lastParagraphBreak=0;
char* papercol=NULL;
char* bodyTag="<BODY BGCOLOR=#FFFFFF";
int showNumbers=0;
void writeTeX(FILE* texFile,Bounds* bounds,int length,float scale) {
  int i;
  for(i=0;i<length;i++) {
    char* s; struct stat test;
    if(realWordCounter-lastParagraphBreak>=Max_Images_Per_Paragraph) { lastParagraphBreak=realWordCounter; fputs("\n\n",texFile); }
    asprintf(&s,"%09d.png",wordCounter);
    if(papercol && !hadPaperColour) { fputs(papercol,texFile); hadPaperColour = 1; }
    stat(s,&test); if(!test.st_size) {
      printf("WARNING: File %s is empty (probably due to a bug); skipping it\n",s);
    } else if(scale<0) {
      /* Negative scales are 1/x of available height to scale line-height to */
      int dpi, availablePoints;
      availablePoints = AvailableHeight/-scale;
      if(showNumbers) availablePoints -= 12;
      dpi=(bounds[i].bottom-bounds[i].top)*72/availablePoints; /* because <height> dots in availablePoints/72 inches */
      if((bounds[i].right-bounds[i].left)*72/dpi>AvailableWidth) dpi=1+(bounds[i].right-bounds[i].left)*72/AvailableWidth; /* emergency shrink overly-wide images */
      fprintf(texFile,"\\pdfimageresolution=%d\\wordnumber{%d}{%s}\\scalebox{%g}[1]{ } %%\n",dpi+1,wordCounter,s,AvailableHeight/-scale/12/2); /* dpi+1 for rounding errors (otherwise might break the fit or the num lines on the screen).  That scale because scaling 12pt to AvailableHeight/-scale pt, but halve it to match scaling 12pt by factor 'scale' which is likely only half of a 2-line stack (NB there's a normal space afterwards also) */
    } else if((bounds[i].right-bounds[i].left)*72/(OriginalDPI/scale) > AvailableWidth || (bounds[i].bottom-bounds[i].top)*72/(OriginalDPI/scale) > AvailableHeight) {
      const char *rotStart="",*rotEnd="";
      int ratio=1000*(bounds[i].right-bounds[i].left) / (bounds[i].bottom-bounds[i].top);
      int willRotate=(ratio<10000 && bounds[i].right-bounds[i].left > bounds[i].bottom-bounds[i].top && !screenMode); /* (if width >= 10 times height, is probably a missed line so don't put it on a page by itself) */
      int squashByHeight=((ratio>1414 && willRotate) || ratio<707 || (screenMode && (bounds[i].bottom-bounds[i].top)*72/AvailableHeight > (bounds[i].right-bounds[i].left)*72/AvailableWidth));
      char *resizeParams = (squashByHeight ? "{!}{1\\textheight}" : "{1\\columnwidth}{!}");
      printf("WARNING: Image %s too big; trying to fit\n",s);
      if(willRotate) { rotStart="\\rotatebox{90}{"; rotEnd="}"; }
      fprintf(texFile,"\n\n\\resizebox*%s{%s\\includegraphics{%s}%s}\n\n",resizeParams,rotStart,s,rotEnd);
      lastParagraphBreak=realWordCounter;
    } else {
      fprintf(texFile,"\\wordnumber{%d}{%s}\\scalebox{%g}[1]{ } %%\n",wordCounter,s,scale);
    }
    free(s); wordCounter++; realWordCounter++;
  }
}

float em_size = 0; /* will be filled in with number of points in an em, also the font size.  We write in em's rather than points so as many browsers as possible will zoom. */
void writeHtml(FILE* htmlFile,Bounds* bounds,int length,float scale) {
  int i;
  for(i=0;i<length;i++) {
    char* s; float pt;
    asprintf(&s,"%09d.png",htmlWordCounter);
    if(bodyTag) {
      fputs(bodyTag,htmlFile); bodyTag=NULL; /* (note: not free() because may not have been alloc'd.  This is a small memory leak but only once per run and the RAM will be reclaimed on exit.) */
      if(showNumbers) fputs(" onLoad=\"if(window.location.hash && document.getElementById) document.getElementById(window.location.hash.slice(1)).style.border='thick solid blue';\"",htmlFile); /* so you can refer people to the html file with #number at the end of the URL, and it will jump to and highlight that word (TODO should this be documented somewhere?) */
      fputs(">",htmlFile);
      /* Following scripts must be after the body tag (could re-write for placing in HEAD so won't get deleted by editor, using "onload" in our bodyTag and using the DOM, instead of document.write, but then the button wouldn't appear until the page is fully loaded which may take some time) */
      if(showNumbers) fprintf(htmlFile,"<SCRIPT><!--\nvar w=document.body.clientWidth; if(window.innerWidth) w=window.innerWidth; if(w) document.write('<STYLE>img{max-width:'+w+'px;}</STYLE>'); // as img{max-width:100%%} won't work if inside ruby (note IE doesn't support max-width anyway, see end of document)\n--></SCRIPT>\n<STYLE ID=styleHack></STYLE><SCRIPT><!--\nfunction hideNumbers() { var hide='.hideMe { display:none !important; } rt { display: none !important;} '; if(document.styleSheets && document.styleSheets[0].cssText) document.styleSheets[0].cssText=document.styleSheets[0].cssText+hide; else document.getElementById('styleHack').innerHTML=hide; }\nif(document.getElementById) document.write('<BUTTON STYLE=\"font-size: 1em; display: block\" CLASS=hideMe onClick=\"hideNumbers();\">Hide numbers (press this when you\\'ve finished editing)</BUTTON>');\n--></SCRIPT>\n");
    }
    if(scale<0) pt=(bounds[i].right-bounds[i].left)*AvailableHeight/-scale/(bounds[i].bottom-bounds[i].top); /* because height in points = (bottom-top)*72/dpi, and we want that to scale to AvailableHeight/-scale.  Put this scale into width*72*scale/dpi (as below), factor out ()s and cancel the 72's and dpi's.  Note: we assume the screen's DPI setting is true, which it might not be if it's been adjusted for magnification - in this case you should multiply the "number of lines on screen" value (the negative scale) by the enlargement factor of the DPI (or divide the available height by the same factor). */
    else pt=(bounds[i].right-bounds[i].left)*72.0*scale/OriginalDPI;
    if(showNumbers) fprintf(htmlFile,"<RUBY ID=%d><RB><IMG SRC=%s STYLE=\"width: %gem\"></RB><RT>%d</RT></RUBY>\n",htmlWordCounter,s,pt/em_size,htmlWordCounter); /* Could also put htmlWordCounter as ALT text, but don't do both as it makes copy/paste more awkward.  Displaying the number separately is probably better for collaboration with people who don't know about ALT text. */
    else fprintf(htmlFile,"<IMG SRC=%s STYLE=\"width: %gem\" ALT=%d>\n",s,pt/em_size,htmlWordCounter); /* so if run without --edit, still get the ALT */
    free(s); htmlWordCounter++;
  }
  fflush(htmlFile); /* so can incrementally test in browser */
}

void processOnePage(FILE* texFile,FILE* htmlFile,const char* pngFilename,float scale,FILE* boundsFile) {
  Pbm* pbm=pngtoPbm(pngFilename); Bounds* bounds; int length,i;
  Pbm* outPbm; outPbm=pbm;
  if(rotationMode) {
    printf("Removing fuzz\r"); fflush(stdout);
    if(FuzzSizeForOutput<FuzzSize) {
      outPbm=(Pbm*)malloc(sizeof(Pbm));
      memcpy(outPbm,pbm,sizeof(Pbm));
      outPbm->data=malloc(pbm->widthBytes*pbm->height);
      memcpy(outPbm->data,pbm->data,pbm->widthBytes*pbm->height);
      removeFuzz(outPbm,FuzzSizeForOutput);
    }
    removeFuzz(pbm,FuzzSize);
  }
  printf("Removing vertical lines\r"); fflush(stdout);
  removeVertLines(pbm);
  /* if(!pbm==outPbm) removeVertLines(outPbm); */ /* (might not actually want this, although reasons will likely be different from the reasons for having a different fuzz size) */
  bounds=findBestRotation(&length,pbm,LineGap,WordGap,LinegapTolerant);
  for(i=0;i<length;i++) {
    char* s;
    crop(pbm,&(bounds[i]));
    asprintf(&s,"%09d.png",wordCounter+i);
    if(use_original) pngtopng(pngFilename,s,bounds[i].left,bounds[i].top,bounds[i].right-bounds[i].left+1,bounds[i].bottom-bounds[i].top+1);
    else Pbmtopng(outPbm,s,bounds[i].left,bounds[i].top,bounds[i].right-bounds[i].left+1,bounds[i].bottom-bounds[i].top+1);
    if(use_original) {
      /* try to choose a paper colour */
      int theTop,theBottom;
      if(i && !papercol && bounds[i-1].right+WordGap <= bounds[i].left && (theTop=max(bounds[i-1].top,bounds[i].top)) < (theBottom=min(bounds[i-1].bottom,bounds[i].bottom))) {
        char* cmd; FILE*p; int status;
        int paperR,paperG,paperB;
        asprintf(&cmd,"pngtopnm '%s' | pnmcut %d %d %d %d | pnmcolormap 2 | pnmcut 1 0 1 1|tail -1",pngFilename,bounds[i-1].right+1,theTop,bounds[i].left-bounds[i-1].right-2,theBottom-theTop);
        p=popen(cmd,"r");
        paperR=fgetc(p); paperG=fgetc(p); paperB=fgetc(p);
        if(paperG==EOF) paperG=paperB=paperR; /* TODO this works only with 8-bit greyscale and 24-bit colour */
        pclose(p); free(cmd);
        if(paperR!=EOF) {
          asprintf(&papercol,"\\definecolor{papercol}{rgb}{%.2f,%.2f,%.2f}\\pagecolor{papercol}%%\n",(float)paperR/255.0,(float)paperG/255.0,(float)paperB/255.0);
          asprintf(&bodyTag,"<BODY BGCOLOR=#%02x%02x%02x",paperR,paperG,paperB);
          if(boundsFile) {
            FILE* pcfil=fopen("papercol.tex","w");
            fputs(papercol,pcfil);
            fclose(pcfil); pcfil=fopen("papercol.htm","w");
            fputs(bodyTag,pcfil); fclose(pcfil);
          }
        }
      }
    }
  }
  if(boundsFile) {
    fwrite(bounds,sizeof(Bounds),length,boundsFile);
    /* also output the original-image filename for reference, in case the image needs more pre-editing (so it shouldn't matter that this isn't saved if run --edit a second time) */
    if(showNumbers) {
      fprintf(texFile,"\n%s:\n",pngFilename);
      if(htmlFile && !bodyTag) fprintf(htmlFile,"\n<SPAN CLASS=hideMe>%s:</SPAN>\n",pngFilename); /* !bodyTag added so doesn't print one of these before the <body> tag and scripts */
    }
  }
  writeTeX(texFile,bounds,length,scale);
  if(htmlFile) writeHtml(htmlFile,bounds,length,scale);
  if(outPbm!=pbm) { free(outPbm->data); free(outPbm); }
  free(bounds); free(pbm->data); free(pbm);
  printf("                                                               \r");
}

#define LoadFunction(Funcname,Filename,Type) \
  Type* Funcname(int *length) { \
    FILE* f; struct stat test; Type* ret; \
    if(stat(Filename,&test)) { *length=0; return NULL; } \
    *length=test.st_size/sizeof(Type); \
    ret=(Type*)malloc(*length * sizeof(Type)); \
    f=fopen(Filename,"rb"); \
    fread(ret,sizeof(Type),*length,f); \
    fclose(f); return ret; }
LoadFunction(loadPreviousBounds,"bounding.dat",Bounds);
LoadFunction(loadEditSequence,"sequence.dat",int);
LoadFunction(loadPaperCol,"papercol.tex",char);
LoadFunction(loadBodyTag,"papercol.htm",char);

void loadInterlinearMode() {
  FILE* f; struct stat test;
  if(stat("interlinear.dat",&test)) { interlinearMode=1; return; }
  f=fopen("interlinear.dat","rb");
  fread(&interlinearMode,sizeof(int),1,f);
  fclose(f);
}

void saveInterlinearMode() {
  FILE* f=fopen("interlinear.dat","wb");
  fwrite(&interlinearMode,sizeof(int),1,f);
  fclose(f);
}

void processEditSequence(FILE* texFile,FILE* htmlFile,float scale) {
  int length; Bounds* bounds; int* sequence;
  int i;
  papercol=loadPaperCol(&length);
  if(papercol) { papercol=(char*)realloc(papercol,length+1); papercol[length]=0; }
  bodyTag=loadBodyTag(&length);
  if(bodyTag) { bodyTag=(char*)realloc(bodyTag,length+1); bodyTag[length]=0; }
  else bodyTag="<BODY BGCOLOR=#FFFFFF";
  bounds=loadPreviousBounds(&length);
  sequence=loadEditSequence(&i);
  loadInterlinearMode();
  if(sequence) {
    length=i; /* don't need to keep old length because we're not checking the validity of the sequence */
    i=0; while(i<length) {
      if(sequence[i]==-1) { /* pause */
        float pauseScale = (interlinearMode?2:1)*scale;
        if(scale<0) pauseScale=AvailableHeight/-scale/12; /* but '/' is more than 12pt */
        fprintf(texFile,"\\textcolor{blue}{\\scalebox{%g}[%g]{\\raisebox{3pt}[12pt][0pt]{//}}}\n",pauseScale,pauseScale);
        if(htmlFile) fprintf(htmlFile,"<SPAN STYLE=\"color: blue; font-size: %gem\">//</SPAN>\n",12*pauseScale/em_size);
        i++;
      } else {
        /* try to do as large a segment at a time as possible (for the use_original code) */
        int segmentLength;
        for(segmentLength=1; segmentLength+i<length; segmentLength++) if(sequence[segmentLength+i]!=sequence[segmentLength+i-1]+1) break;
        wordCounter=sequence[i]; writeTeX(texFile,bounds+wordCounter,segmentLength,scale);
        if(htmlFile) { htmlWordCounter=sequence[i]; writeHtml(htmlFile,bounds+htmlWordCounter,segmentLength,scale); }
        i+=segmentLength;
      }
    }
    free(sequence);
  } else { /* no resequencing */
    writeTeX(texFile,bounds,length,scale);
    if(htmlFile) writeHtml(htmlFile,bounds,length,scale);
  }
  free(bounds);
}

main(int argc,const char* argv[]) {
  int argvLp=0; float scale;
  FILE *texFile, *boundsFile, *htmlFile=NULL;
  if(argc==1) {
    printf("Syntax:\n"
"%s [options] scale-factor PNG-filenames\n"
"Produces enlarged.pdf (and lots of temporary files)\n"
"Best run in a temporary directory\n\n"
"Options:\nUse --onecol if text has only one column (this is more reliable)\n"
"Use --norotate if text is not from a scan (also more reliable)\n"
"Use --slides if result is likely to be viewed on screen\n"
"(--slides=X,Y if unusual screen size, X and Y in millimetres,\n"
"  e.g. old Libretto: --slides=124,93\n"
"         Eee PC 900: --slides=197,115 )\n"
"Use --interlinear if text has annotation above each line\n"
"Use --nobw to cut directly from the original scan rather than the B&W version\n  (slow and makes large files; use only if necessary)\n"
"Use --edit to show a number above each word for use with edit-reflow.py\n (might not work with --nobw)\n (--html puts numbers as ALTs; --html --edit makes them visible)\n"
"Use a negative scale factor if you need to specify a\n  number of lines to fit on the page, e.g. -3 means\n  3 lines fit on the page (words of different\n  sizes are scaled differently to fit this)\n"
"Use --html to make a .html instead of .pdf\n  (.tex is still output for reference by edit-reflow.py)\n"
"Use --faster to skip maximum compression of PNGs\n  (e.g. if you're going to convert the output to something else anyway)\n"
           ,argv[0]);
    return 1;
  }
  while(argv[++argvLp][0]=='-' && argv[argvLp][1]=='-') {
    if(!strcmp(argv[argvLp],"--onecol")) singleCol_mode = 1;
    else if(!strcmp(argv[argvLp],"--interlinear")) interlinearMode = 1;
    else if(!strcmp(argv[argvLp],"--html")) htmlFile=fopen("enlarged.html","w");
    else if(!strcmp(argv[argvLp],"--faster")) faster=1;
    else if(!strcmp(argv[argvLp],"--norotate")) rotationMode = 0;
    else if(!strcmp(argv[argvLp],"--slides")) { int t=AvailableWidth; AvailableWidth=AvailableHeight; AvailableHeight=t; screenMode=1; }
    else if(!strncmp(argv[argvLp],"--slides=",9)) {
      if (sscanf(argv[argvLp],"--slides=%d,%d",&AvailableWidth,&AvailableHeight)!=2) { printf("Malformed screen size %s\n",argv[argvLp]+9); return 1; }
      screenMode=2; /* to indicate a custom size (this is used below) */
    } else if(!strcmp(argv[argvLp],"--nobw")) use_original = 1;
    else if(!strcmp(argv[argvLp],"--edit")) showNumbers = 1;
    else {
      printf("Unknown option: %s\n",argv[argvLp]);
      return 1;
    }
  }
  if(sscanf(argv[argvLp++],"%f",&scale)!=1) {
    puts("Error reading scale, check syntax");
    return 1;
  }
  texFile=fopen("enlarged.tex","w");
  if(/*showNumbers &&*/ argvLp<argc) boundsFile=fopen("bounding.dat","wb"); /* argvLp<argc added because don't want to overwrite it if we're using it again (no filenames means processing edit-reflow.py's output).  showNumbers deleted because if 0 then user can still get numbers from HTML ALTs */
  else boundsFile=NULL;
  fprintf(texFile,"\\documentclass[12pt]{article}\\usepackage[pdftex]{graphicx}\\usepackage{color}\\def\\wordnumber#1#2{\\includegraphics{#2}}\n");
  if(showNumbers) fprintf(texFile,"\\def\\wordnumber#1#2{\\shortstack{\\textcolor{red}{#1}\\\\\\includegraphics{#2}}}\n"); /* important to be on a line of its own for edit-reflow.py */
  if(screenMode==2) {
    /* custom paper size, no margins */
    fprintf(texFile,"\\textwidth %dmm \\textheight %dmm \\topmargin 0mm \\marginparwidth 0mm \\oddsidemargin 0mm \\evensidemargin 0mm \\pdfpagewidth=%d true mm \\pdfpageheight=%d true mm \\pdfhorigin=0 mm \\pdfvorigin=-12.95 mm",AvailableWidth,AvailableHeight,AvailableWidth,AvailableHeight);
    /* convert to points (no margin if unusual screen size) */
    AvailableWidth=AvailableWidth*720/254;
    AvailableHeight=AvailableHeight*720/254;
  } else fprintf(texFile,"\\usepackage{geometry}\\geometry{verbose,a4paper%s,tmargin=10mm,bmargin=10mm,lmargin=10mm,rmargin=10mm,headheight=0mm,headsep=0mm,footskip=0mm}\n",(screenMode?",landscape":""));
  fprintf(texFile,"\\pagestyle{empty}\n");
  if(scale>=0) fprintf(texFile,"\\pdfimageresolution=%d\n",(int)(OriginalDPI/scale));
  else scale *= 1.015; /* make 1/x slightly smaller for interline space to fit.  (1.01 not enough) */
  fprintf(texFile,"\\begin{document}\\raggedright\\noindent%%\n");
  if(htmlFile) {
    if(scale<0) em_size=AvailableHeight/-scale/(interlinearMode?2:1);
    else em_size = 12*scale;
    fprintf(htmlFile,"<HTML><HEAD><STYLE ID=theStyle>\nbody{font-size: %gpt}\n",em_size);
    if(showNumbers) fprintf(htmlFile,"ruby { display: inline-table; } ruby * { display: inline; line-height: 1.0; text-indent: 0; text-align: center; white-space: nowrap; } rb { display: table-row-group; font-size: %gpt; } rt { display: table-header-group; font-size: %dpt; color: red; background: white; } ",em_size,(scale==1 ? 9 : 12));
    else fprintf(htmlFile,"img{max-width:100%%}\n");
    fprintf(htmlFile,"</STYLE><SCRIPT><!-- \nif(document.all && document.getElementById && screen.logicalXDPI && document.styleSheets && document.styleSheets[0].cssText) {\n // make sure IE6+ can change size\n var pointsPerEM=12; // When rendering points, IE6+7+Firefox2 assume 12pt=(16*screen.deviceXDPI/screen.logicalXDPI)px, which is OK if at 96dpi or if correct scaling is applied. Do not try to better this by paying more attention to DPI, as it could be incorrect and would make this script's scaling drastically inconsistent from normal. \n for(var i=0; i<document.styleSheets.length; i++) document.styleSheets[i].cssText=document.styleSheets[i].cssText.replace(/%gpt/g,%g*1.0/pointsPerEM +'em');\n // also emulate max-width in IE6+\n document.styleSheets[0].cssText += 'body{overflow-x:hidden;}'; window.onload=function() { var w=document.body.clientWidth; if(window.innerWidth) w=window.innerWidth; var images=document.getElementsByTagName('img'); for(var i in images) if(w && images[i].scrollWidth>w) images[i].style.width=w+'px';}; }\n--></SCRIPT></HEAD>",em_size,em_size);
  }
  if(argvLp==argc) processEditSequence(texFile,htmlFile,scale);
  else for(;argvLp<argc;argvLp++) processOnePage(texFile,htmlFile,argv[argvLp],scale,boundsFile);
  fputs("\\end{document}",texFile);
  fclose(texFile);
  if(boundsFile) fclose(boundsFile);
  if(htmlFile) {
    fputs("<!-- blank space ensures PageDown from well-fitted end-of-text doesn't confuse: --><p>&nbsp;<p>&nbsp;<p>&nbsp;<p>&nbsp;<p>&nbsp;",htmlFile);
    fputs("</BODY></HTML>",htmlFile);
    fclose(htmlFile);
    puts("\n\nCreated HTML file.\nNote: If you're using Opera on an OLPC XO or low-spec system\nthen you may want to reduce the resolution of the images\nto speed up browser display. (Size is not affected.)\nCommand to do this:\nfor N in 0*.png;do pngtopnm $N|pnmscale 0.5|pnmtopng -compression 9 >$N-new && mv $N-new $N;done\nReminder: If sharing with others, you might want to\n mention that the browser's text size controls should work."); // (e.g. someone I know had trouble on a high-DPI screen in IE)
  } else system("ulimit -n 1024 ; pdflatex enlarged.tex");
  /* (the generous "ulimit" is to help some versions of MacTeX; Mac defaults to max 256 open files, and affected TeX versions need 1 open file for each image there is in the paragraph - need Max_Images_Per_Paragraph and then some) */
  saveInterlinearMode();
}
