#!/usr/bin/python
# Author: BP
# Date: Sun Dec  8 16:18:09 SGT 2013
# Note: python v2.8
"""
     postit digitizing prototype
 usage: digitize.py [image] [outdir]
    
"""

import os,sys,re,subprocess,math,struct

DEBUG=True
VERBOSE=True

IMAGEMAGICK_CONVERT='/usr/bin/convert'
IMAGEMAGICK_IDENTIFY='/usr/bin/identify'
POSTIT_SIZE=512

_re_dimensions = re.compile('([0-9]+)x([0-9]+)')
def convert_image(img):
    "figures out image size and type, converts it to raw returning the new image filename"
    outimg=img+'.rgb'
    cmd='%s %s -depth 8 %s' % (IMAGEMAGICK_CONVERT,img,outimg)
    os.system(cmd)

    cmd='%s %s' % (IMAGEMAGICK_IDENTIFY,img)
    p = subprocess.Popen(cmd.split(),stdout=subprocess.PIPE)
    lines = ' '.join(p.stdout.readlines())
    m=_re_dimensions.search(lines)
    p.stdout.close() 

    (x,y)=map(lambda(x): int(x),m.groups())
    return (x,y,outimg)

def img_scale(imgdata,xlen,ylen,xstep,ystep):
    "decimates an image, calculating pixel value by averaging"
    nimgdata = []
    for y in range(0,ylen,ystep):
        nimgline = []
        my = ystep
        if my+y>=ylen: my = ylen-y-1
        for x in range(0,xlen,xstep):
            mx = xstep
            if mx+x>=xlen: mx = xlen-x-1
            C=0; R=0; G=0; B=0
            for cy in range(0,my):
                for cx in range(0,mx):
                    R=R+(imgdata[y+cy][x+cx] % 256);
                    G=G+((imgdata[y+cy][x+cx]/256) % 256);
                    B=B+((imgdata[y+cy][x+cx]/256/256) %256);
                    C=C+1
            R=R/C; G=G/C; B=B/C
            pixval = (R*256+G)*256+B;
            nimgline.append(pixval)
        nimgdata.append(nimgline)
    if DEBUG: print "scaled bitmap to (%i,%i)" % (len(nimgdata[0]),len(nimgdata))
    return nimgdata

def scan_for_candidates(raw_img,xlen,ylen):
    # center x, center y, rotation angle (0 degrees is east), diagonal length
    candidate_list = []
    fin = open(raw_img,'rb')
    
    # read in the pixmap
    if DEBUG: print "reading pixmap %i %i " % (xlen,ylen)
    img_data = []
    for j in range(0,ylen):
        dataline = struct.unpack("%iB" % (3*xlen),fin.read(3*xlen))
        img_line= []
        for i in range(0,len(dataline),3):
            pixval = (dataline[i]*256+ dataline[i+1])*256 + dataline[i+2]
            img_line.append(pixval)
        img_data.append(img_line)

    if DEBUG: print "analyzing pixmap %i %i " % (len(img_data),len(img_data[0]))

    # scale down the image, quantize post-it colors
    ds_img_data = img_scale(img_data,xlen,ylen,50,50)

"""
    # TODO --- scan for candidates
    for x in range(0,xlen):
        for y in range(0,xlen):
            if (ds_img_data == 0)
"""

    # now scan for candidates
    print  len(ds_img_data[0]),len(ds_img_data)
    print "%x" % ds_img_data[36][22]

    #candidate_list.append((1172,1676,90-34.12,585))
    return candidate_list

def extract_image(img,candidate,nimg):
    # first crop a subset
    cx,cy,angle,diag_length = candidate;

    while (angle>90): angle=angle-90
    mx = max(diag_length*math.cos(2*math.pi*angle/360.0),diag_length*math.sin(2*math.pi*angle/360.0))

    lx=cx-mx
    rx=cx+mx
    ty=cy-mx
    by=cy+mx

    sx=rx-lx
    sy=by-ty

    reangle = angle-45.0
#
#    cmd = '%s %s -crop %ix%i+%i+%i +repage tmp1.png' %\
#        (IMAGEMAGICK_CONVERT,img,sx,sy,lx,ty)
#    os.system(cmd)
#
#    # next rotate rotate
#
#    cmd='%s tmp1.png -rotate %.3f tmp2.png' %\
#        (IMAGEMAGICK_CONVERT,float(reangle))
#    os.system(cmd)

    mx = 2*int(diag_length/math.sqrt(2))
    cmd = '%s %s -crop %ix%i+%i+%i +repage -rotate %.3f -gravity center -crop %ix%i+0+0 +repage %s' %\
        (IMAGEMAGICK_CONVERT,img,sx,sy,lx,ty,float(reangle),mx,mx,nimg)

    # crop again and rescale
    #cmd='%s tmp2.png -gravity center -crop %ix%i+0+0 +repage %s' %\
         #(IMAGEMAGICK_CONVERT,mx,mx,nimg)
    print cmd
    os.system(cmd)
    
    
##
# main program
##

if len(sys.argv)<2:
    print __doc__
    sys.exit(1)

#
src=sys.argv[1]
outdir=sys.argv[2]

if VERBOSE: print "extracting raw image"
x,y,raw_img = convert_image(src)

if VERBOSE: print "converted %s with %i by %i pixels" % (raw_img,x,y)

if VERBOSE: print "scanning for candidate post-its"
candidates=scan_for_candidates(raw_img,x,y);
if VERBOSE: print "%i candidates found." % len(candidates)

cnt = 1
for candidate in candidates:
    nimg=os.path.join(outdir,"img.%i.png" % cnt)
    if VERBOSE: print "extracting %i to %s" % (cnt,nimg)
    extract_image(src,candidate,nimg)
    cnt=cnt+1

if VERBOSE: print "finished!"


