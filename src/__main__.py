import sys
import os

from .frontend import program
from .typechecker import typecheck
from .codegen import generate

if __name__ == '__main__':
    if len(sys.argv) > 1:
        i = open(sys.argv[1]).read()
    else:
        i = input()
    ast = program.parse_strict(i)
    ast, table = typecheck(ast)
    print("Typed ast:")
    for decl in ast:
        print("\t", decl)
    print("Table:")
    for top in table:
        print("\t", top)
    output = generate(ast, table)

    try:
        os.mkdir('bin')
    except:
        pass
    open('bin/E.java', 'w').write(output)
