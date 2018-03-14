type T => java.util.ArrayList<T> as T => A.Array<T> where [ self.size >= 0 ]

native A.array : T => (size : Integer, o:T) -> res:A.Array<T> where [ size >= 0 and res.size == size ] 

native A.range : (mi : Integer, ma : Integer) -> res:A.Array<Integer> where [ mi <= ma and res.size == (ma - mi)]

native A.get : T => (arr: A.Array<T>, index: Integer) -> p:T  where [ index >= 0 and index < arr.size ]

native A.set : T => (arr: A.Array<T>, index: Integer, value:T) -> p:T  where [ index >= 0 and index < arr.size ]

native A.size : T => (arr: A.Array<T>) -> r:Integer where [ r == arr.size ]

native A.forEach : T => (arr: A.Array<T>, f: (T) -> Void) -> _:A.Array<T>

native A.map : T,R => (arr: A.Array<T>, f: (T) -> R) -> out:A.Array<R> where [ out.size == arr.size ]

native A.reduce : T => (arr: A.Array<T>, f: (T,T) -> T) -> _:T where [ arr.size > 0 ]