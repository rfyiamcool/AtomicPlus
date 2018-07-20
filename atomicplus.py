# coding:utf-8
from multiprocessing import Value, Lock

from cffi import FFI


class AtomicCounter(object):
    def __init__(self, initial_value=0):
        self._storage = ffi.new('long *', initial_value)

    @property
    def value(self):
        return self._storage[0]

    def __iadd__(self, inc):
        lib.long_add_and_fetch(self._storage, inc)
        return self

    def __isub__(self, dec):
        lib.long_sub_and_fetch(self._storage, dec)
        return self

    def check(self, old):
        if lib.long_bool_compare_and_swap(self._storage, old, old) == 1:
            return True
        return False

    def cas(self, old, new):
        return lib.long_val_compare_and_swap(self._storage, old, new)


class MultiCounter():
    """support multiprocessing"""
    def __init__(self):
        self._counter = Value('i', 0)
        self._lock = Lock()

    def __iadd__(self, inc):
        with self._lock:
            self._counter = self._counter + inc

    def __isub__(self, dec):
        with self._lock:
            self._counter = self._counter - dec

    def check(self, old):
        if self.cas(old, old) == old:
            return True
        return False

    def cas(self, old, new):
        with self._lock:
            if self._counter == old:
                self._counter = new
                return new
            else:
                return self._counter


ffi = FFI()


ffi.cdef("""
long long_add_and_fetch(long *, long);
long long_sub_and_fetch(long *, long);
long long_bool_compare_and_swap(long *, long, long);
long long_val_compare_and_swap(long *, long, long);
""")

lib = ffi.verify("""
long long_add_and_fetch(long *v, long l) {
    return __sync_add_and_fetch(v, l);
};

long long_sub_and_fetch(long *v, long l) {
    return __sync_sub_and_fetch(v, l);
};

long long_bool_compare_and_swap(long *v, long o, long n) {
    return __sync_bool_compare_and_swap(v, o, n);
};

long long_val_compare_and_swap(long *v, long o, long n) {
    return __sync_val_compare_and_swap(v, o, n);
};
""")
