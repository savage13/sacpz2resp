#!/usr/bin/env python

import sys
import getopt
from math import *

file  = ""
gamma = 0
opts, args = getopt.getopt(sys.argv[1:], 'f:u:')
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


maxf=12
minf=0
nfft  = 8192
delta = 1.0
delta_freq = (maxf - minf) / ( nfft * delta )
X    = list()
freq = list()
amp  = list()
pha  = list()
for i in range(nfft) :
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
