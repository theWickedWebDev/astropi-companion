# import functools
# from collections.abc import Hashable
from functools import cache as Memoize

# class Memoize(object):
#    def __init__(self, func):
#       self.func = func
#       self.cache = {}
#    def __call__(self, *args):
#       if not isinstance(args, Hashable):
#          return self.func(*args)
#       if args in self.cache:
#          return self.cache[args]
#       else:
#          value = self.func(*args)
#          self.cache[args] = value
#          return value
#    def __repr__(self):
#       return self.func.__doc__
#    def __get__(self, obj, objtype):
#       return functools.partial(self.__call__, obj)