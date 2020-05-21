import copy
import builtins
from .annotation import aefunction, aedocumentation

''' List binds in Aeon to Python '''

@aefunction("""type List[T] {
    size : Integer;
}""", None)

class List(object):
    def __init__(self):
        pass

# Empty list
@aefunction('empty_list[T]() -> {l:List[T] | l.size == 0} = native;', lambda x : empty_list(x))
def empty_list(ignore):
    return []

# Range: returns a list of Integers
@aefunction('range[T](min:Integer, max:Integer) -> {l:List[Integer] | l.size == (max - min)} = native;', lambda min: lambda max: range_list(min, max))
def range_list(minimum, maximum):
    return list(bultins.range(minimum, maximum))

# Append an element to the list
@aefunction('append[T](x:T, l:List[T]) -> {l2:List[T] | l2.size == l.size + 1} = native;', lambda x: lambda l: append(x, l))
def append(x, l):
    return l + [x]

# Extend the list with another list
@aefunction('extend[T](l1:List[T], l2:List[T]) -> {l3:List[T] | l3.size == l1.size + l2.size} = native;', lambda l1: lambda l2: extend(l1, l2))
def extend(l1, l2):
    return l1 + l2

# Insert at a specific position
@aefunction('insert[T](x:T, l:List[T], {i:Integer | i <= l.size}) -> {l2:List[T] | l2.size == l.size + 1} = native;', lambda x: lambda l: lambda i: insert(x, l, i))
def insert(x, l, i):
   return l[0:i] + [x] + l[i:]

# Removes the first occurence of the element
@aefunction('remove[T](x:T, l:List[T]) -> {l2:List[T] | l2.size <= l.size} = native;', lambda x: lambda l: remove(x, l))
def remove(x, l):
    if x not in l:
        return copy.deepcopy(l)
    return l[0:l.index(x)] + l[l.index(x) + 1:]

# Contains a certain element
@aefunction('contains[T](x:T, l:List[T]) -> Boolean = native;', lambda x: lambda l: contains(x, l))
def contains(x, l):
    return x in l

# Index of the first occurence of the element
@aefunction('index[T](x:T, l:List[T]) -> {i:Integer | -1 <= i && i < l.size} = native;', lambda x: lambda l: index(x, l))
def index(x, l):
    return l.index(x)

# Amount of times an element occurs 
@aefunction('count[T](x:T, l:List[T]) -> Integer = native;', lambda x: lambda l: count(x, l))
def count(x, l):
    return l.count(x)

# Reverses a list 
@aefunction('reverse[T](l:List[T]) -> List[T] = native;', lambda l: reverse(l))
def reverse(l):
    return list(reversed(l))

# Check if any element of the list respects a predicate 
@aefunction('exists[T](f:(x:T -> Boolean), l:List[T]) -> Boolean = native;', lambda f: lambda l: exists(f, l))
def exists(f, l):
    return any(f(x) for x in l)

# Check if all element of the list respects a predicate 
@aefunction('forall[T](f:(x:T -> Boolean), l:List[T]) -> Boolean = native;', lambda f: lambda l: forall(f, l))
def forall(f, l):
    return all(f(x) for x in l)

# Check if any element of the list respects a predicate 
@aefunction('filter[T](f:(x:T -> Boolean), l:List[T]) -> List[T] = native;', lambda f: lambda l: filter(f, l))
def filter(f, l):
    return list(builtins.filter(f, l))
    
# Map each element
@aefunction('map[T, K](f:(x:T -> K), l:List[T]) -> {l2:List[K] | l.size == l2.size} = native;', lambda f: lambda l: map(f, l))
def map(f, l):
    return list(builtins.map(f, l))

# Element at a certain position
@aefunction('elemAt[T](i:Integer, l:List[T]) -> T = native;', lambda i: lambda l: elemAt(i, l))
def elemAt(i, l):
    return l[i]

# Reduce
@aefunction('reduce[X, Y](f:(x:X -> [Y -> Y]), {l:List[X] | l.size > 0}) -> X = native;', lambda l: reduce(l))
def reduce(l):
    return l[1:]

# Size of the list 
@aefunction('length[T](l:List[T]) -> {i:Integer | i == l.size} = native;', lambda l: length(l))
def length(l):
    return len(l)

# Head of the list
@aefunction('head[T]({l:List[T] | l.size > 0}) -> T = native;', lambda l: head(i, l))
def head(l):
    return l[0]

# Tail of the list 
@aefunction('tail[T]({l:List[T] | l.size > 0}) -> {l2:List[T] | l2.size == l.size - 1} = native;', lambda l: tail(l))
def tail(l):
    return l[1:]


