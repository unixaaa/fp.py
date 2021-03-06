import unittest, os, antlr3, StringIO, random
from CoreLexer import CoreLexer
from CoreParser import CoreParser
from visitors import Identification, CodeGeneration
from transforms import CaseLifter, LambdaLifter
from gmachine import State, SymbolTable, run
from decimal import *

class CoreTest(unittest.TestCase):
  def setUp(self):
    self.reset()

  def reset(self):
    'reset the compiler'
    self.asts = []
    self._loaded = {}
    self.symtab = SymbolTable()
    self.id = Identification(self.symtab)
    self.cg = CodeGeneration(self.symtab)
    self.cl = CaseLifter(self.symtab)
    self.ll = LambdaLifter(self.symtab)

  def load(self, filename):
    'load function list definitions'
    if filename in self._loaded:
      return
    ast = self.parse(filename)
    self.ll.visit(ast)
    self.cl.visit(ast)
    self.id.visit(ast)
    self.asts.append(ast)
    self._loaded[filename] = True

  def prelude(self):
    'load prelude definitions'
    self.load("core\\runtime\\prelude.core")

  def lists(self):
    'load functional-lists definitions'
    self.load("core\\tests\\lists.core")
    self.prelude()

  def compile(self, ast):
    for a in self.asts:
      self.cg.visit(a)
    self.cg.visit(ast)

  def parse(self, filename):
    'parse an file into an ast'
    if not os.path.exists(filename):
      raise Exception('file not found: %s.' % (filename))
    with open(filename) as f:
      stream = antlr3.ANTLRInputStream(f)
      lexer = CoreLexer(stream)
      tokens = antlr3.CommonTokenStream(lexer)
      parser = CoreParser(tokens)
      ast = parser.program()
      return ast.tree

  def parse_str(self, content):
    stream = antlr3.ANTLRInputStream(StringIO.StringIO(content))
    lexer = CoreLexer(stream)
    tokens = antlr3.CommonTokenStream(lexer)
    parser = CoreParser(tokens)
    ast = parser.program()
    return ast.tree

  def run_str(self, content):
    ast = self.parse_str(content)
    self.ll.visit(ast)
    self.cl.visit(ast)
    self.id.visit(ast)
    self.compile(ast)
    state = State(self.symtab)
    return run(state), state

  def test_basic1(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("main = I %s" % (p));
    self.assertEqual(ans, p)

  def test_basic2(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("id = S K K; main = id %s" % (p));
    self.assertEqual(ans, p)

  def test_basic3(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("id = S K K; main = twice twice twice id %s" % (p));
    self.assertEqual(ans, p)

  def test_basic4(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("main = twice (I I I) %s" % (p));
    self.assertEqual(ans, p)

  def test_precedence(self):
    self.reset()
    ans, state = self.run_str("""
main = 4*5+(2-5)
""")
    self.assertEqual(ans, 17)

  def test_precedence1(self):
    self.reset()
    ans, state = self.run_str("""
main = (4+2)*5+2-5
""")
    self.assertEqual(ans, 27)

  def test_precedence2(self):
    self.reset()
    ans, state = self.run_str("""
main = 4+2*5+2-5
""")
    self.assertEqual(ans, 11)

  def test_negate1(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("main = negate %s" % (p));
    self.assertEqual(ans, -p)

  def test_negate2(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("main = twice negate %s" % (p));
    self.assertEqual(ans, p)

  def test_add1(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("main = 10 + %s" % (p));

  def test_add2(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("main = %s + 10" % (p));
    self.assertEqual(ans, 10 + p)

  def test_mul1(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("main = 10 * %s" % (p));
    self.assertEqual(ans, 10 * p)

  def test_mul2(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("""
square x = x * x ;
main = square (square %s)
""" % p)
    self.assertEqual(ans, (p * p) * (p * p))

  def test_mul3(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("main = %s * 10" % (p));
    self.assertEqual(ans, 10 * p)

  def test_div1(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 10 / 2");
    self.assertEqual(ans, 5)

  def test_div2(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 20 / 10");
    self.assertEqual(ans, 2)

  def test_eq1(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 10 == 20");
    self.assertEqual(ans, False)

  def test_eq2(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 10 == 10");
    self.assertEqual(ans, True)

  def test_neq1(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 10 != 20");
    self.assertEqual(ans, True)

  def test_neq2(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 10 != 10");
    self.assertEqual(ans, False)

  def test_lt1(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 10 < 20");
    self.assertEqual(ans, True)

  def test_lt2(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 10 < 10");
    self.assertEqual(ans, False)

  def test_lte1(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 10 <= 20");
    self.assertEqual(ans, True)

  def test_lte2(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 10 <= 10");
    self.assertEqual(ans, True)

  def test_lte3(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 10 <= 1");
    self.assertEqual(ans, False)

  def test_gt1(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 10 > 20");
    self.assertEqual(ans, False)

  def test_gt2(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 10 > 1");
    self.assertEqual(ans, True)

  def test_gte1(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 10 >= 20");
    self.assertEqual(ans, False)

  def test_gte2(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 10 >= 10");
    self.assertEqual(ans, True)

  def test_gte3(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 10 >= 1");
    self.assertEqual(ans, True)

  def test_eq3(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 20 == 10");
    self.assertEqual(ans, False)

  def test_and(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = true & false");
    self.assertEqual(ans, False)

  def test_and1(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = true & true");
    self.assertEqual(ans, True)

  @unittest.expectedFailure
  def test_and2(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = true & 1");

  @unittest.expectedFailure
  def test_and3(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = 0 & false");

  def test_or1(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = true | true");
    self.assertEqual(ans, True)

  def test_or2(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = true | false");
    self.assertEqual(ans, True)

  def test_if1(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = if false 1 2");
    self.assertEqual(ans, 2)

  def test_if2(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = if true 1 2");
    self.assertEqual(ans, 1)

  def test_if3(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = if (5 == 5) 10 2");
    self.assertEqual(ans, 10)

  def test_if4(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = if (6 == 5) 10 2");
    self.assertEqual(ans, 2)

  def test_if5(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = if ((2 - 2) == 0) (K 4 5) (K1 4 5)");
    self.assertEqual(ans, 4)

  def test_let1(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("main = let id1 = I I I in id1 id1 %s" % (p));
    self.assertEqual(ans, p)

  def test_let2(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("main = let a = 1, b = 2, c = 3, d = %s in K (K d a) b" % (p));
    self.assertEqual(ans, p)

  def test_let3(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("main = let a = 1, b = 2, c = 3, d = %s in K (K a a) b" % (p));
    self.assertEqual(ans, 1)

  def test_let4(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("main = let a = 1, b = 2, c = 3, d = %s in K (K b c) b" % (p));
    self.assertEqual(ans, 2)

  def test_let5(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("main = let a = 1, b = 2, c = 3, d = %s in K (K c a) d" % (p));
    self.assertEqual(ans, 3)

  def test_let6(self):
    self.reset()
    self.prelude()
    p = random.randint(0, 99999)
    ans, state = self.run_str("main = let a = %s in (let b = 1 in K a b)" % (p));
    self.assertEqual(ans, p)

  @unittest.expectedFailure
  def test_abort1(self):
    self.reset()
    ans, state = self.run_str("main = abort");

  def test_abort2(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = K 1 abort");

  @unittest.expectedFailure
  def test_abort3(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("main = K1 1 abort");

  def test_lists(self):
    self.reset()
    self.load("core\\tests\\lists.core")
    self.assertEqual(len(self.symtab['ftl'].parameters()), 1)
    self.assertEqual(len(self.symtab['fhd'].parameters()), 1)
    self.assertEqual(len(self.symtab['fnil'].parameters()), 2)
    self.assertEqual(len(self.symtab['fcons'].parameters()), 4)

  def test_infinite(self):
    self.reset()
    self.lists()
    p = random.randint(0, 99999)
    ans, state = self.run_str("""
infinite x = fcons x (infinite x);
main = fhd (ftl (ftl (infinite %s)))
""" % (p))
    self.assertEqual(len(self.symtab['infinite'].parameters()), 1)
    self.assertEqual(ans, p)

  def test_infinite2(self):
    self.reset()
    self.lists()
    p = random.randint(0, 99999)
    ans, state = self.run_str("""
infinite x = letrec xs = fcons x xs in xs;
main = fhd (ftl (ftl (infinite %s)))
""" % (p))
    self.assertEqual(len(self.symtab['infinite'].parameters()), 1)
    self.assertEqual(ans, p)

  def test_case1(self):
    self.reset()
    ans, state = self.run_str("""
length xs = case xs of <1> -> 0, <2> y ys -> 1 + length ys;
main = length (Pack{2,2} 2 (Pack{2,2} 2 (Pack{2,2} 1 Pack{1,0})))
""")
    self.assertEqual(len(self.symtab['length'].parameters()), 1)
    self.assertEqual(ans, 3)

  def test_case2(self):
    "case in non-strict context"
    self.reset()
    ans, state = self.run_str("""
K x y = x;
f x = K (1 + (case x of <3> -> 1, <4> -> 2)) 1;
main = f Pack{3,0}
""")
    self.assertEqual(len(self.symtab['f'].parameters()), 1)
    self.assertEqual(ans, 2)

  def test_case3(self):
    "case in non-strict context"
    self.reset()
    ans, state = self.run_str("""
K x y = x;
f x = K (1 + (case x of <3> -> 1, <4> -> 2)) 1;
main = f Pack{4,0}
""")
    self.assertEqual(len(self.symtab['f'].parameters()), 1)
    self.assertEqual(ans, 3)

  def test_case4(self):
    "case with arguments in non-strict context"
    self.reset()
    ans, state = self.run_str("""
K x y = x;
f x = K (1 + (case x of <3> -> 1, <4> x -> x)) 1;
main = f Pack{4,1} 10
""")
    self.assertEqual(len(self.symtab['f'].parameters()), 1)
    self.assertEqual(ans, 11)

  def test_case5(self):
    "case with arguments in non-strict context"
    self.reset()
    ans, state = self.run_str("""
K x y = x;
f x = K (1 + (case x of <3> x -> x, <4> x -> x)) 1;
main = f Pack{3,1} 100
""")
    self.assertEqual(len(self.symtab['f'].parameters()), 1)
    self.assertEqual(ans, 101)

  def test_highlevel1(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
from n = cons n (from (n+1));
take n xs = if (n==1) nil (case xs of
  <4> -> nil,
  <3> p ps -> cons p (take (n-1) ps));
main = hd (tl (tl (tl (take 5 (from 0)))))
""")
    self.assertEqual(ans, 3)

  def test_highlevel2(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
from n = cons n (from (n+1));
take n xs = if (n==1) nil (case xs of
  <4> -> nil,
  <3> p ps -> cons p (take (n-1) ps));
main = hd (tl (tl (tl (take 5 (from 5)))))
""")
    self.assertEqual(ans, 8)

  def test_highlevel3(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
from n = cons n (from (n+1));
take n xs = if (n==1) nil (case xs of
  <4> -> nil,
  <3> p ps -> cons p (take (n-1) ps));
main = hd (tl (tl (tl (from 5))))
""")
    self.assertEqual(ans, 8)

  @unittest.expectedFailure
  def test_highlevel4(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
from n = cons n (from (n+1));
take n xs = if (n==1) nil (case xs of
  <4> -> nil,
  <3> p ps -> cons p (take (n-1) ps));
main = hd (tl (tl (tl (tl (tl (take 5 (from 5)))))))
""")


  def test_highlevel5(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
from n = cons n (from (n + 1));

sieve xs = case xs of
  <4> -> nil,
  <3> p ps -> cons p (sieve (filter (nonMultiple p) ps));

filter predicate xs = case xs of
    <4> -> nil,
    <3> p ps -> let rest = filter predicate ps in if (predicate p) (cons p rest) rest;

nonMultiple p n = ((n/p)*p) != n;

take n xs = if (n==0) nil (case xs of
  <4> -> nil,
  <3> p ps -> cons p (take (n-1) ps));

main = hd (tl (tl (tl (sieve (take 15 (from 2))))))
""")
    self.assertEqual(ans, 7)

  def test_highlevel5(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
from n = cons n (from (n + 1));

sieve xs = case xs of
  <4> -> nil,
  <3> p ps -> cons p (sieve (filter (nonMultiple p) ps));

filter predicate xs = case xs of
    <4> -> nil,
    <3> p ps -> let rest = filter predicate ps in if (predicate p) (cons p rest) rest;

nonMultiple p n = ((n/p)*p) != n;

take n xs = if (n==0) nil (case xs of
  <4> -> nil,
  <3> p ps -> cons p (take (n-1) ps));

main = (sieve (take 15 (from 2)))
""")
    self.assertEqual(ans, [2, 3, 5, 7, 11, 13, 'nil'])

  def test_lambdalifter(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
f x = let g = \y. x*x + y in (g 3 + g 4);
main = f 6
""")
    self.assertEqual(ans, 79)

  def test_lambdalifter1(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
f = (\ x.x + 1);
main = f 1
""")
    self.assertEqual(ans, 2)

  def test_lambdalifter2(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
f x = let g = (\y. y+1) in g (g x);
main = f 6
""")
    self.assertEqual(ans, 8)

  def test_lambdalifter3(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
g = \y. let z = x*x in let p = z*z in p + y;
main = g 2 3
""")
    self.assertEqual(ans, 83)

  def test_shadowing1(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
main = let x = (let y = 1 in y), y = 2 in x + y
""")
    self.assertEqual(ans, 3)

  def test_shadowing2(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
f x = case x of <5> h -> (let h = 10 in h) + h;
main = f (Pack{5, 1} 2)
""")
    self.assertEqual(ans, 12)

  def test_shadowing3(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
f x = case x of <5> x -> (let x = 10 in x);
main = f (Pack{5, 1} 2)
""")
    self.assertEqual(ans, 10)

  def test_floats(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
main = 1.31 + 1.2
""")
    self.assertEqual(str(ans), str('2.51'))

  def test_floats1(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
main = 1.31 + 1
""")
    self.assertEqual(str(ans), str('2.31'))

  def test_floats2(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
main = 1.31 + 1
""")
    self.assertEqual(str(ans), str('2.31'))

  def test_floats3(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
main = 1.31 * 2
""")
    self.assertEqual(str(ans), str('2.62'))

  def test_floats4(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
main = 2.44 / 2
""")
    self.assertEqual(str(ans), str('1.22'))

  def test_floats5(self):
    "test aribtrary precisionness of floats, google doesn't compute this sum but wolfram alpha will"
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
main = 2.123456789123456789 / 1.121212121121212121
""")
    self.assertEqual(str(ans), str('1.893893893155560965668214599'))

  def test_chars(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
main = 'a'
""")
    self.assertEqual(ans, 'a')

  @unittest.expectedFailure
  def test_chars1(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
main = 'a' + 1
""")

  @unittest.expectedFailure
  def test_chars2(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
main = 'a' < 1
""")

  def test_chars3(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
main = 'a' < 'b'
""")
    self.assertEqual(ans, True)

  def test_chars4(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
main = 'z' >= 'a'
""")
    self.assertEqual(ans, True)

  def test_chars5(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
main = 'a' <= 'a'
""")
    self.assertEqual(ans, True)

  def test_chars6(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
main = 'a' == 'a'
""")
    self.assertEqual(ans, True)

  def test_chars7(self):
    self.reset()
    self.prelude()
    ans, state = self.run_str("""
main = 'a' != 'a'
""")
    self.assertEqual(ans, False)