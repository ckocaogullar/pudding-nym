'''
oprf.py
A module that includes all operations needed for OPRF (Oblivious Pseudorandom Function) operations.
Specifically, I use 2HashDH OPRF scheme by Jarecki et al. (2016)
'''

import json
from decimal import *
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives import hashes, hmac
from sympy.combinatorics.named_groups import CyclicGroup
import math
import os
import logging
import random
import numpy as np
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


# Based on Cambridge Cryptography lectures, slide 182.
# p should be a strong prime, I am setting it to value 11 to create a PoC implementation
# In the prime order subgroup that will be used in this algorithm, p is the prime modulus; g is the generator; and q is the prime order
def generate_group():
    p = 11
    q = int((p-1)/2)
    while True:
        x = random.randint(2, p-1)
        print(x)
        g = (x*x) % p
        if g != 1:
            break
    return p, q, g


def generate_private_key(q):
    return random.randint(1, q - 1)

# To map a hash function output to a group element, I take the generator of the group to the power of the hash
# (interpreting the hash as an integer)


def hash(val, g, p):
    return (g ** val) % p


def generate_inverse_private_key(key, q):
    return pow(key, -1, q)


p, q, g = generate_group()
user_key = generate_private_key(q)
inverse_user_key = generate_inverse_private_key(user_key, q)
server_key = generate_private_key(q)
val = 13
blinded_hash = pow(hash(val, g, p), user_key) % p
server_comp = pow(blinded_hash, server_key) % p
unblinded_hash = pow(server_comp, inverse_user_key) % p
print('blinded_hash', blinded_hash)
print('server_comp', server_comp)
print('unblinded_hash', unblinded_hash)

server_alone_comp = pow(hash(val, g, p), server_key) % p
print('server_alone_comp', server_alone_comp)

assert server_alone_comp == unblinded_hash
