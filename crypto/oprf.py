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
import numpy as np
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


'''
Uses the cryptography library to create group parameters for Diffie-Hellman key exchange if there are no pre-saved parameters
Returns the saved parameters otherwise

In a real setting, all discovery nodes and users should know and agree on the same prime order.
For demonstrative purposes, here the value is stored locally and read from a pickle file.
This module does not deal with making sure that all parties agree on the prime order value.
'''

parameters = None


def get_dh_parameters(generator=2, key_size=2048):
    global parameters
    if parameters:
        pass
    elif not os.path.exists('store/dh_parameters.json'):
        logging.info(
            "There are no saved DH parameters. Creating a new set of group parameters...")
        parameters = dh.generate_parameters(
            generator=generator, key_size=key_size)
        p = parameters.parameter_numbers().p
        g = parameters.parameter_numbers().g
        logging.info("Generated new parameters")
        with open("store/dh_parameters.json", "w") as file:
            json.dump({'p': p, 'g': g}, file)
    else:
        logging.info("Retrieving existing parameters")
        with open("store/dh_parameters.json", "r") as file:
            data = json.load(file)
            pn = dh.DHParameterNumbers(
                data['p'], data['g'])
            parameters = pn.parameters()
    logging.info('Prime order: {}'.format(parameters.parameter_numbers().p))
    return parameters


def get_prime_order():
    return get_dh_parameters().parameter_numbers().p


def get_generator():
    return get_dh_parameters().parameter_numbers().g


def generate_public_key(private_key):
    public_key = private_key.public_key()
    public_number = public_key.public_numbers().y
    print("public numbers: {}".format(public_number))
    return public_number


def generate_private_key():
    private_key = get_dh_parameters().generate_private_key()
    private_number = private_key.private_numbers().x
    return private_key, private_number


def _fast_exp(base, exp, order):
    print('base: {}'.format(base))
    print('exp: {}'.format(exp))
    print('order: {}'.format(order))
    x = base
    y = base if exp % 2 else 1
    exp = exp // 2
    while exp > 0:
        assert x != 0
        x = (x * x) % order
        if exp % 2:
            y = x if y == 1 else (x * y) % order
        exp = exp // 2
    return y


def lcm(a, b):
    return abs(a*b) // math.gcd(a, b)


def multiplicative_cyclic_group_pow(base, exp, order):
    # if type(base) is bytes:
    #     base = int.from_bytes(base, byteorder='big')
    # return _fast_exp(base, exp, order)
    return pow(base, exp, order)


def additive_cyclic_group_pow(base, exp, order):
    return (base * exp) % order


def get_inverse_user_priv_key(msg, key, order):
    # Additive inverse
    # return order - key

    # Multiplicative inverse
    return pow(key, -1, order - 1)


def cyclic_group_root(num, root, order):
    with localcontext() as ctx:
        # return ctx.power(num, 1 / Decimal(root))
        a = Decimal(num).ln() / Decimal(root)
        res_up = a.exp().quantize(Decimal('1.'), rounding=ROUND_UP)
        res_down = a.exp().quantize(Decimal('1.'), rounding=ROUND_DOWN)
        if ctx.power(res_up, root) == num:
            return res_up
        elif ctx.power(res_down, root) == num:
            return res_down
        logging.error("Could not find the {}th root of {}".format(root, num))


def log(log_base, input, mod):
    n = 1
    while log_base ** n % mod != input:
        n += 1
    return n


def hash(data, order, algorithm=hashes.SHA256()):
    if type(data) is str:
        data = bytes(data, 'UTF-8')
    digest = hashes.Hash(algorithm)
    digest.update(data)
    return int.from_bytes(digest.finalize(), byteorder='big') % order


def keyed_hash(key, data, algorithm=hashes.SHA256()):
    h = hmac.HMAC(key, algorithm)
    h.update(data)
    signature = h.finalize()
    signature


user_priv_dh_key, user_priv_key = generate_private_key()
if user_priv_key % 2 == 0:
    user_priv_key += 1
print('user_priv_key {}'.format(user_priv_key))
discovery_server_priv_dh_key, discovery_server_priv_key = generate_private_key()
print('discovery_server_priv_key {}'.format(discovery_server_priv_key))
prime_order = get_prime_order()
assert user_priv_key < prime_order
assert discovery_server_priv_key < prime_order
print('prime_order: {}'.format(prime_order))

# user_priv_key = 11
# discovery_server_priv_key = 9
# prime_order = 37
# msg = 2

msg = hash('hey', prime_order)
inverse_user_priv_key = get_inverse_user_priv_key(
    msg, user_priv_key, prime_order)
#assert inverse_user_priv_key + user_priv_key == prime_order

print('inverse user private key {}'.format(inverse_user_priv_key))

# Simulate a real OPRF evaluation
blinded_exp = multiplicative_cyclic_group_pow(msg, user_priv_key, prime_order)
print('blinded exp {}'.format(blinded_exp))
server_response = multiplicative_cyclic_group_pow(
    blinded_exp, discovery_server_priv_key, prime_order)
print('server resp {}'.format(server_response))
unblinded_exp = multiplicative_cyclic_group_pow(
    server_response, inverse_user_priv_key, prime_order)

# If the discovery server computed the value by itself
discovery_server_comp = multiplicative_cyclic_group_pow(
    msg, discovery_server_priv_key, prime_order)

print('Unblinded exp {}'.format(unblinded_exp))
print('Discovery server computation {}'.format(discovery_server_comp))

assert unblinded_exp == discovery_server_comp
