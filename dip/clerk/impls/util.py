'''utility functions for the clerks'''

import re


def l1mfn2tn(l1mfn: str) -> str:
    '''convert the l1 manifest filename to target name'''
    c, dt = l1mfn.split('_')[1:3]
    d = f'{dt[:4]}-{dt[4:6]}-{dt[6:8]}'
    t = f'{dt[9:11]}:{dt[11:13]}:{dt[13:15]}'
    s = dt[-1]
    return f'{c} ({d})({t})({s})'


def tn2l1mfn(tn: str) -> str:
    c = tn.split(' ')[0]
    dt = ''
    for i, segment in enumerate(re.findall(r'\((.*?)\)', tn)):
        dt += segment.replace('-', '').replace(':', '')
        if i == 0:
            dt += 'T'
    return f'cgi_{c}_{dt}_l1_.yaml'
