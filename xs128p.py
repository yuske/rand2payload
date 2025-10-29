import struct
import random
from z3 import *

MASK = 0xFFFFFFFFFFFFFFFF

# xor_shift_128_plus algorithm
def xs128p(state0, state1, browser):
    s1 = state0 & MASK
    s0 = state1 & MASK
    s1 ^= (s1 << 23) & MASK
    s1 ^= (s1 >> 17) & MASK
    s1 ^= s0 & MASK
    s1 ^= (s0 >> 26) & MASK 
    state0 = state1 & MASK
    state1 = s1 & MASK
    if browser == 'chrome':
        generated = state0 & MASK
    else:
        generated = (state0 + state1) & MASK

    return state0, state1, generated

# Symbolic execution of xs128p
def sym_xs128p(slvr, sym_state0, sym_state1, generated, browser):
    s1 = sym_state0 
    s0 = sym_state1 
    s1 ^= (s1 << 23)
    s1 ^= LShR(s1, 17)
    s1 ^= s0
    s1 ^= LShR(s0, 26) 
    sym_state0 = sym_state1
    sym_state1 = s1
    if browser == 'chrome':
        calc = sym_state0
    else:
        calc = (sym_state0 + sym_state1)
    
    condition = Bool('c%d' % int(generated * random.random()))
    if browser == 'chrome':
        impl = Implies(condition, LShR(calc, 12) == int(generated))
    elif browser == 'firefox' or browser == 'safari':
        # Firefox and Safari save an extra bit
        impl = Implies(condition, (calc & 0x1FFFFFFFFFFFFF) == int(generated))

    slvr.add(impl)
    return sym_state0, sym_state1, [condition]

def reverse17(val):
    return val ^ (val >> 17) ^ (val >> 34) ^ (val >> 51)

def reverse23(val):
    return (val ^ (val << 23) ^ (val << 46)) & MASK

def xs128p_backward(state0, state1, browser):
    prev_state1 = state0
    prev_state0 = state1 ^ (state0 >> 26)
    prev_state0 = prev_state0 ^ state0
    prev_state0 = reverse17(prev_state0)
    prev_state0 = reverse23(prev_state0)
    # this is only called from an if chrome
    # but let's be safe in case someone copies it out
    if browser == 'chrome':
        generated = prev_state0
    else:
        generated = (prev_state0 + prev_state1) & MASK
    return prev_state0, prev_state1, generated

# Firefox nextDouble():
    # (rand_uint64 & ((1 << 53) - 1)) / (1 << 53)
# Chrome nextDouble():
    # (state0 | 0x3FF0000000000000) - 1.0
# Safari weakRandom.get():
    # (rand_uint64 & ((1 << 53) - 1) * (1.0 / (1 << 53)))
def to_double(browser, out):
    if browser == 'chrome':
        double_bits = (out >> 12) | 0x3FF0000000000000
        double = struct.unpack('d', struct.pack('<Q', double_bits))[0] - 1
    elif browser == 'firefox':
        double = float(out & 0x1FFFFFFFFFFFFF) / (0x1 << 53) 
    elif browser == 'safari':
        double = float(out & 0x1FFFFFFFFFFFFF) * (1.0 / (0x1 << 53))
    return double


def predict_sequence(observed_doubles, count, browser='chrome'):
    if browser not in ('chrome', 'firefox', 'safari'):
        raise ValueError('Unsupported browser: %s' % browser)

    if count <= 0:
        return []

    if not observed_doubles:
        raise ValueError('observed_doubles must contain at least one value')

    doubles = list(observed_doubles)
    if browser == 'chrome':
        doubles = list(reversed(doubles))

    # from the doubles, generate known piece of the original uint64
    generated = []
    for value in doubles:
        if browser == 'chrome':
            recovered = struct.unpack('<Q', struct.pack('d', value + 1))[0] & (MASK >> 12)
        elif browser == 'firefox':
            recovered = int(value * (0x1 << 53))
        else:  # safari
            recovered = int(value / (1.0 / (1 << 53)))
        generated.append(recovered)

    # setup symbolic state for xorshift128+
    ostate0, ostate1 = BitVecs('ostate0 ostate1', 64)
    sym_state0 = ostate0
    sym_state1 = ostate1
    slvr = Solver()
    conditions = []

    # run symbolic xorshift128+ algorithm for the provided observations
    for known in generated:
        sym_state0, sym_state1, ret_conditions = sym_xs128p(slvr, sym_state0, sym_state1, known, browser)
        conditions.extend(ret_conditions)

    if slvr.check(conditions) != sat:
        raise ValueError('Unable to recover internal state from observations')

    model = slvr.model()
    state0 = model[ostate0].as_long()
    state1 = model[ostate1].as_long()

    # check that the solver produced a unique solution for the provided data
    slvr.add(Or(ostate0 != model[ostate0], ostate1 != model[ostate1]))
    if slvr.check(conditions) == sat:
        raise ValueError('Multiple solutions found; provide more observations')

    predictions = []
    current_state0 = state0
    current_state1 = state1

    predictions.append(to_double(browser, current_state0))

    for _ in range(count - 1):
        if browser == 'chrome':
            current_state0, current_state1, out = xs128p_backward(current_state0, current_state1, browser)
            out = current_state0 & MASK
        else:
            current_state0, current_state1, out = xs128p(current_state0, current_state1, browser)
        predictions.append(to_double(browser, out))

    return predictions
