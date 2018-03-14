import prelude.J
import prelude.A

type Integer as Nat where [ self >= 0 ]
type Integer as Neg where [ self < 0 ]

plus : (n:Nat) -> npo:Nat where [ npo == (n + 1) ] {
   n + 1
}

fun : (i:Integer, j:Integer) -> _:Integer where [ (i + j) < 10 and j > 0 ] {
   i + j
}

main : (args:Array<String>) -> _:Void { 
   a = plus(10)
   # b = plus(-10)
   
   fun(1,2)
   # fun(1, -2)
   fun(5,4)
   #fun(5,5)
  
   ar = A.array(10, 0)
   A.get(ar, 0)
   #A.get(ar, a)
   
   
   ar2 = A.range(10,20)
   A.get(ar2, 0)
   #A.get(ar2, a)
   A.get(ar2, A.size(ar2)-1)
   

}