from lexer import Lexer
from parser import Parser
from generator import Generator
from symbolizer import Symbolizer
from runner import Runner
#from grapher import *

id = '10'
path = f'./Datoteke/Druga faza/{id}/src.pas'
with open(path, 'r') as source:
    text = source.read()
    lexer = Lexer(text)
    tokens = lexer.lex()

    parser = Parser(tokens)
    ast = parser.parse()

    # doda simbole ast-u (modifikuje ast)
    symbolizer = Symbolizer(ast)
    symbolizer.symbolize()

    runner = Runner(ast)
    runner.run()

    generator = Generator(ast)
    code = generator.generate('main.c') # ime fajla
    # print(ast)    


#grapher = Grapher(ast)
#img = grapher.graph()
# Image(img) 
# print(ast)
# for t in tokens:
#     print(t)

# Osmi test primer kada rucno istestiram ne ispisuje tacno resenje ali nigde ne puca dok kad pokrenem grader pukne i ispise gresku za operand * sto je cudno jer taj operand ne postoji u tom test primeru. I nakon toga od 9 do 15 test primera puca za svaki 


