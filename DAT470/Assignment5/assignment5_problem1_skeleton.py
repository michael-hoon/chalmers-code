#!/usr/bin/env python3

import argparse

def rol32(x,k):
    """Auxiliary function (left rotation for 32-bit words)"""
    return ((x << k) | (x >> (32-k))) & 0xffffffff

def murmur3_32(key, seed):
    """Computes the 32-bit murmur3 hash"""

    # encode all strings to UTF-8
    if isinstance(key, str):
        key = key.encode('utf-8')
    elif not isinstance(key, bytes):
        raise TypeError("key must be a string or bytes")
    if len(key) == 0:
        raise ValueError("key must not be empty")

    # Constants
    c1 = 0xcc9e2d51
    c2 = 0x1b873593
    r1 = 15
    r2 = 13
    m = 5
    n = 0xe6546b64

    hash = seed

    for i in range(0, len(key), 4):
        k = 0
        for j in range(4):
            if i + j < len(key):
                k |= (ord(key[i + j]) & 0xff) << (j * 8)
            else:
                break

        k = (k * c1) & 0xffffffff
        k = rol32(k, r1)
        k = (k * c2) & 0xffffffff

        hash ^= k
        hash = rol32(hash, r2)
        hash = (hash * m + n) & 0xffffffff
    
    # Finalization

    hash ^= len(key)
    hash ^= (hash >> 16)
    hash = (hash * 0x85ebca6b) & 0xffffffff
    hash ^= (hash >> 13)
    hash = (hash * 0xc2b2ae35) & 0xffffffff
    hash ^= (hash >> 16)
    return hash


def auto_int(x):
    """Auxiliary function to help convert e.g. hex integers"""
    return int(x,0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Computes MurMurHash3 for the keys.'
    )
    parser.add_argument('key',nargs='*',help='key(s) to be hashed',type=str)
    parser.add_argument('-s','--seed',type=auto_int,default=0,help='seed value')
    args = parser.parse_args()

    seed = args.seed
    for key in args.key:
        h = murmur3_32(key,seed)
        print(f'{h:#010x}\t{key}')
        