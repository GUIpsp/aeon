from .frontend_module.AeonASTVisitor import AeonASTVisitor

from .frontend_module.generated.AeonParser import AeonParser
from .frontend_module.generated.AeonLexer import AeonLexer

from .libraries.standard import importNative

# from .frontend_module.verifiers.ContextVerifier import ContextVerifier
from .frontend_module.verifiers.AeonSyntaxErrorListener import AeonSyntaxErrorListener

import os
import sys 
import os.path

from antlr4 import *
from .ast import Var
from .ast import Import
from .ast import Program
from .ast import Definition

# Given a file, parses the file and imports the program
def parse(path):
    
    from aeon3.libraries.stdlib import initial_context
    
    input_stream = FileStream(path)
    tree = parse_input(input_stream)
    
    # Build the program
    context = initial_context
    aeonVisitor = AeonASTVisitor(context)
    program = aeonVisitor.visit(tree)
    
    # Check if the imports are proper and resolve the imports
    if runImportVerifier(tree):
        program = resolveImports(path, program)

    # Run the verifiers to search for errors
    # runVerifiers(tree)
    
    return program
    
# Given an expression of a program, parse it and imports it
def parse_strict(text):
    input_stream = InputStream(text)
    tree = parse_input(input_stream)
    
    # Build the program and return it
    program = AeonASTVisitor({}).visit(tree)
    
    return program.declarations[0]
    
def parse_input(input_stream):

    # Initialize error listener
    syntax_error_listener = AeonSyntaxErrorListener()

    # Initialize lexer, tokens and parser
    lexer = AeonLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = AeonParser(tokens)

    # Add default error listener to lexer and parser
    lexer.removeErrorListeners()
    parser.removeErrorListeners()
    lexer.addErrorListener(syntax_error_listener)
    parser.addErrorListener(syntax_error_listener)
    
    tree = parser.aeon()

    # Print the errors and exit
    if syntax_error_listener.errorsList:
        [print(error) for error in syntax_error_listener.errorsList]
        sys.exit(-1)
    
    return tree

def runImportVerifier(tree):
    return True


def runVerifiers(tree):
    errorsList = []
    ContextVerifier(errorsList).visit(tree)

    # Print the errors and exit
    if errorsList:
        [print(error) for error in errorsList]
        sys.exit(-1)

# Resolves the imports
def resolveImports(path, program):
    result = []
    from .libraries.stdlib import add_function
    for declaration in program.declarations:
        if type(declaration) is Import:
            # Get the os path for the ae file
            importPath = declaration.name + '.ae'
            joinedPath = os.path.join(os.path.dirname(path), importPath)
            realPath = os.path.normpath(joinedPath)
            importedProgram = parse(realPath)
            
            # If we only want a specific function from the program
            if declaration.function is not None:
                importedProgram.declarations = list(filter(lambda x : type(x) is Definition \
                                            and x.name == declaration.function, \
                                            importedProgram.declarations))
            for decl in importedProgram.declarations:
                # native variable
                if type(decl) is Definition and type(decl.body) is Var and decl.body.name == 'native':
                    path = realPath[:-3].replace('/', '.')
                    res = importNative(path, decl.name)
                    for key in res.keys():
                        add_function(key, (decl, res[key]))
            result = importedProgram.declarations + result
        else:
            result.append(declaration)
    return Program(result)