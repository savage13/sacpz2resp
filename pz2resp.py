#!/usr/bin/env python

import sys
import argparse
from datetime import datetime

class polezero(object):
    def __init__(self, args):
        self.args = dict(vars(args))
        for k,v in self.args.items():
            if not v:
                del self.args[k]
            else:
                self.args[k] = self.args[k][0]
        self.read(args.sac_pz_file[0])
    def empty(self):
        return { 'zeros': [], 'poles': [], 'constant': 1.0, 'nzeros': 0, 'npoles': 0 }
    def check_single(self,pz):
        n = len(pz['zeros'])
        for i in range(pz['nzeros'],len(pz['zeros'])):
            pz['zeros'].append(0+0j)
        trans = [('STATION    (KSTNM)','stat'),
                 ('NETWORK   (KNETWK)','net'),
                 ('LOCATION   (KHOLE)','loc'),
                 ('CHANNEL   (KCMPNM)','chan'),
                 ('START','start'),
                 ('END','end')]
        for t in trans:
            if t[0] in pz:
                pz[t[1]] = pz[t[0]]
                del pz[t[0]]
        # SAC_PZ are by default to displacement
        # Removing a zero changes them to velocity
        pz['nzeros'] -= 1
        pz['zeros'].pop()

        pz.update(self.args)

        if 'start' in pz and 'end' in pz:
            pz['_start_'] = datetime.strptime(pz['start'],'%Y-%m-%dT%H:%M:%S')
            pz['_end_'] = datetime.strptime(pz['end'],'%Y-%m-%dT%H:%M:%S')
            pz['start_mdy'] = pz['_start_'].strftime('%m/%d/%Y')
            pz['end_mdy'] = pz['_end_'].strftime('%m/%d/%Y')
            pz['start_yohms'] = pz['_start_'].strftime('%Y,%j,%H:%M:%S')
            pz['end_yohms'] = pz['_end_'].strftime('%Y,%j,%H:%M:%S')
        else :
            raise ValueError('Missing start and end time for polezero')
        if not 'chan' in pz:
            raise ValueError('Missing channel name in polezero')
        if not 'net' in pz:
            raise ValueError('Missing network name in polezero')
        if not 'stat' in pz:
            raise ValueError('Missing station name in polezero')
        if not 'loc' in pz:
            raise ValueError('Missing location name in polezero')
    def read(self, filename):
        f = open(filename, 'r')
        state = None
        pzs = []
        pz = None
        for line in f.readlines():
            # Comment
            line = line.strip()
            if len(line) <= 0:
                continue
            if line.startswith('*') :
                if pz and state != 'meta':
                    self.check_single(pz)
                    pzs.append(pz)
                    pz = None
                state = 'meta'
                if pz == None:
                    pz = self.empty()

                if ':' in line:
                    k,v = str.split(line[2:],':',1)
                    pz[k.strip()] = v.strip()
                continue
            if pz == None:
                pz = self.empty()
            if line.startswith('ZEROS'):
                state = 'zeros'
                pz['nzeros'] = int(line.split()[1])
            elif line.startswith('POLES'):
                state = 'poles'
                pz['npoles'] = int(line.split()[1])
            elif line.startswith('CONSTANT'):
                state = 'constant'
                pz['constant'] = float(line.split()[1])
            elif state == 'zeros':
                v = line.split()
                pz['zeros'].append(float(v[0]) + float(v[1]) * 1j)
            elif state == 'poles':
                v = line.split()
                pz['poles'].append(float(v[0]) + float(v[1]) * 1j)
        if pz :
            self.check_single(pz)
            pzs.append(pz)
        self.pzs = pzs
    def __repr__(self):
        s = ""
        meta = ['NETWORK   (KNETWK)',
                'STATION    (KSTNM)',
                'LOCATION   (KHOLE)',
                'CHANNEL   (KCMPNM)',
                'CREATED',
                'START',
                'END',
                'DESCRIPTION',
                'LATITUDE',
                'LONGITUDE',
                'ELEVATION',
                'DEPTH',
                'DIP',
                'AZIMUTH',
                'SAMPLE RATE',
                'INPUT UNIT',
                'OUTPUT UNIT',
                'INSTTYPE',
                'INSTGAIN',
                'COMMENT',
                'SENSITIVITY',
                'A0']
        for pz in self.pzs:
            s += '* '+ '*'*34 + '\n'
            for k in meta:
                if k in pz:
                    s += '* %-18s: %s\n' %(k,pz[k])
            s += '* '+ '*'*34 + '\n'
            s += 'ZEROS\t%d\n' % pz['nzeros']
            for z in pz['zeros']:
                s += "\t%+13.6e\t%+13.6e\t\n" %( z.real, z.imag )
            s += 'POLES\t%d\n' % pz['npoles']
            for z in pz['poles']:
                s += "\t%+13.6e\t%+13.6e\t\n" %( z.real, z.imag )
            s += 'CONSTANT\t%-12.6e\n' % (pz['constant'])
            s += '\n\n'
        return s
    def resp(self):
        r = ""
        for pz in self.pzs:
            r += '''#
##################################################
B050F03     Station:     %(stat)s
B050F16     Network:     %(net)s
B052F03     Location:    %(loc)s
B052F04     Channel:     %(chan)s
B052F22     Start date:  %(start_yohms)s
B052F23     End date:    %(end_yohms)s
#
#                  +-----------------------------------+
#                  |    Response (Poles and Zeros)     |
#                  |        %(net)s  %(stat)s  %(loc)s   %(chan)s         |
#                  |     %(start_mdy)s to %(end_mdy)s      |
#                  +-----------------------------------+
#
B053F03     Transfer function type:                A
B053F04     Stage sequence number:                 1
B053F05     Response in units lookup:              M/S - Velocity in Meters Per Second
B053F06     Response out units lookup:             V - Volts
B053F07     A0 normalization factor:               1.0
B053F08     Normalization frequency:               1.0
B053F09     Number of zeroes:                      %(nzeros)d
B053F14     Number of poles:                       %(npoles)d
''' % pz
            r += '''#              Complex zeroes:
#              i  real          imag          real_error    imag_error
'''
            for i,z in enumerate(pz['zeros']):
                r += 'B053F10-13    %2d  %+12.5e  %+12.5e  %+12.5e  %+12.5e\n' % (i,z.real,z.imag,0,0)
            r += '''#              Complex poles:
#              i  real          imag          real_error    imag_error
'''
            for i,z in enumerate(pz['poles']):
                r += 'B053F15-18    %2d  %+12.5e  %+12.5e  %+12.5e  %+12.5e\n' % (i,z.real,z.imag,0,0)

            r += '''#
#                  +-----------------------------------+
#                  |      Channel Sensitivity/Gain     |
#                  |        %(net)s  %(stat)s  %(loc)s   %(chan)s         |
#                  |     %(start)s to %(end)s          |
#                  +-----------------------------------+
#
B058F03     Stage sequence number:                 1
B058F04     Sensitivity:                           %(constant)s
B058F05     Frequency of sensitivity:              1.0
B058F06     Number of calibrations:                0
''' % pz

        return r


extra = {}
parser = argparse.ArgumentParser(description='Convert SAC Polezero files to Resp files')
parser.add_argument('--start', type=str, nargs=1, action='store',   help='start date of form YYYY-MM-DDTHH:MM:SS',required=False)
parser.add_argument('--end', type=str, nargs=1, action='store',   help='end date of form YYYY-MM-DDTHH:MM:SS',required=False)
parser.add_argument('--chan', type=str, nargs=1, action='store',   help='channel name',required=False)
parser.add_argument('--stat', type=str, nargs=1, action='store',   help='station name',required=False)
parser.add_argument('--net', type=str, nargs=1, action='store',   help='network name',required=False)
parser.add_argument('--loc', type=str, nargs=1, action='store',   help='location name',required=False)
parser.add_argument('--output', type=str, nargs=1, action='store',   help='output filename, stdout if not specified ',required=False)
parser.add_argument('--no-zero-removal', action='store_true', help='do not remove a zero during conversion',required=False)
parser.add_argument('sac_pz_file', type=str, nargs=1, action='store',   help='sac pole zero file with or without metadata')


args = parser.parse_args()

pz = polezero(args)

if args.output:
    f = open(args.output[0],'w')
    f.write(pz.resp())
else:
    print pz.resp()
