# -*- coding: utf8 -*-
import mmh3     # third-party library for murmurhash3
from functools import partial
import math


class Bitarray:
    def __init__(self, size):
        """ Create a bit array of a specific size """
        self.size = size
        self.bitarray = bytearray(size//8 + 1)

    def set(self, n):
        """ Sets the nth element of the bitarray """

        index = n // 8
        position = n % 8
        # print(self.size, self.size//8, index, position)
        self.bitarray[index] = self.bitarray[index] | 1 << (7 - position)

    def get(self, n):
        """ Gets the nth element of the bitarray """

        index = n // 8
        position = n % 8
        return (self.bitarray[index] & (1 << (7 - position))) > 0


class BloomFilter(object):

    def __hash_function_wrapper(self, hash_func, seed, mod):
        def f(s):
            return partial(hash_func, seed=seed)(s) % mod
        return f

    def __len__(self):
        return self.count

    def __init__(self, potential_num, bitarray_size=None, hash_num=None):
        self.potential_num = potential_num
        self.bitarray_size = bitarray_size or 20*potential_num
        self.hash_num = hash_num or int(math.log(2)*self.bitarray_size/self.potential_num)
        self.hash_functions = [self.__hash_function_wrapper(mmh3.hash, seed=i, mod=self.bitarray_size)
                               for i in range(self.hash_num)]
        self.bitarray = Bitarray(self.bitarray_size)
        self.count = 0

    def add(self, string):
        for hash_func in self.hash_functions:
            # print(hash_func(string))
            self.bitarray.set(hash_func(string))
        self.count += 1

    def check(self, string):
        return all(self.bitarray.get(hash_func(string))
                   for hash_func in self.hash_functions)

    def parameters(self):
        return self.potential_num, self.bitarray_size, self.hash_num


def test_bitarray():
    bitarray_obj = Bitarray(32000)
    for i in range(5):
        print("Setting index %d of bitarray .." % i)
        bitarray_obj.set(i)
        print("bitarray[%d] = %d" % (i, bitarray_obj.get(i)))


def test_bloomfilter():
    import random
    import string
    n = 10000
    my_bf = BloomFilter(n)
    input_strings = ["".join(random.choices(string.ascii_letters, k=32)) for i in range(n)]
    negative_samples = ["".join(random.choices(string.ascii_letters, k=32 - 1)) for i in range(n)]
    for s in input_strings:
        my_bf.add(s)
    FP = 0   # False Poitive
    for s in negative_samples:
        FP += int(my_bf.check(s))
    print("Bloom Filter(n = {0},m = {1},k= {2})".format(*my_bf.parameters()))
    print("False Positive:{0}\nTrue Negative:{1}\nFP Rate:{2}".format(FP, n-FP, FP/n))


if __name__ == "__main__":
    test_bitarray()
    test_bloomfilter()

'''
Bloom Filter(n = 100000,m = 2000000,k= 13)
False Positive:9
True Negative:99991
FP Rate:9e-05
'''
