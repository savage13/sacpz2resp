#!/usr/bin/env python

'''
Copyright (c) 2009, Brian Savage
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, 
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import os
import sys
import getopt
from math import *

file  = ""
gamma = 0
progname = os.path.basename(sys.argv[0])


def usage () :
    print '''Usage ''', progname,'''-u units -f Pole-Zero file
        -u Units dis | vel | acc [ dis ]
        -f Pole-Zero file to read'''
    sys.exit(2)

if len(sys.argv) == 1:
    usage()

try:
    opts, args = getopt.getopt(sys.argv[1:], 'f:u:')
except getopt.GetoptError, err:
    print progname, "error:", str(err) 
    usage()

for opt, arg in opts:
    if opt == "-f" :
        file = arg
    elif opt == "-u" :
        if arg == "dis" :
            gamma = 0
        elif arg == "vel" :
            gamma = -1
        elif arg == "acc" :
            gamma = -2
        else :
            assert False, "unknown units"
            gamma = 0
    else :
        assert False, "unhadled option"

fp = open(file)

read_zeros = 0
read_poles = 0
poles = list()
zeros = list()

for line in fp:
    line = line.replace("\n", "")
    v = line.split()
    if line.startswith("CONSTANT") :
        constant = float(v[1])
    elif line.startswith("ZEROS") :
        nzeros = int(v[1])
        read_zeros = 1
        read_poles = 0
    elif line.startswith("POLES") :
        npoles = int(v[1])
        read_poles = 1
        read_zeros = 0
    else :
        if read_poles == 1:
            poles.append( complex( float(v[0]), float(v[1])) )
        if read_zeros == 1:
            zeros.append( complex(float(v[0]), float(v[1])) )

fp.close()
nzeros = nzeros + gamma # Displacement to Velocity
for i in range(len(zeros),nzeros) :
    zeros.append( complex(0.0, 0.0) )
while len(zeros) > nzeros :
    zeros.pop()


maxf  = 12.0
minf  = 0.0
npts  = 8192
delta = 1.0
delta_freq = (maxf - minf) / ( npts * delta )

X    = list()
freq = list()
amp  = list()
pha  = list()

for i in range(npts) :
    freq.append(delta_freq * i)
    omega = complex(0, 2 * pi * i * delta_freq)

    # Numerator => Zeros
    numer = complex(1.0, 0.0)
    for z in zeros:
        numer = numer * (omega - z)
    # Denomerator => Poles
    denom = complex(1.0, 0.0)
    for p in poles:
        denom = denom * (omega - p)
    
    X.append( constant * ( numer / denom ) )
    amp.append( abs( X[-1] ))
    pha.append( atan2(X[-1].imag, X[-1].real) )

for i in range(len(amp)) :
    print "%.6E %.6E %.6f" % ( freq[i], amp[i], pha[i] )


