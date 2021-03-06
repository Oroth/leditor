__author__ = 'chephren'
import operator

class Graph(object):
    def __init__(self):
        self.graph = [{}]

    def addCell(self, cell):
        if not cell.deps:
            self.graph[0][cell._id] = cell    # add it to the list of non-dependents
        else:
            unresolved = cell.deps
            depth = 0
            for i, g in enumerate(self.graph):
                depth = i
                unresolved = [x for x in unresolved if x._id not in g]
                if not unresolved:
                    break

            if unresolved:
                raise LookupError, unresolved
            else:
                if len(self.graph) == depth + 1:
                    self.graph.append({cell._id: cell})
                else:
                    self.graph[depth+1][cell._id] = cell    # assume it has one depedent

        print self.graph


    def updateCells(self):
        for layer in self.graph:
            for item in layer:
                for dep in layer[item].deps:
                    if dep.dirty:
                        layer[item].updateValue()
                        break

        # clean all cells
        for layer in self.graph:
            for item in layer:
                layer[item].dirty = False

class Cell(object):
    cells = 0

    def __init__(self, formula, deps = []):
        self.formula = formula
        #self.value = value  # can be a lambda
        self.deps = deps
        self.dirty = True
        self.weight = 0
        self.value = None
        self.updateValue()
        # should make it so it is automatically updated.

        self._id = Cell.cells
        Cell.cells += 1
        graph.addCell(self)

        print "cell", locals()

    def updateValue(self):
        oldValue = self.value
        if hasattr(self.formula, '__call__'):
            self.value = self.formula()
        else:
            self.value = self.formula
        if self.value != oldValue:
            self.dirty = True

    #more of a test method
    def modifySelf(self, newFormula):
        self.formula = newFormula
        self.updateValue()

    def __repr__(self):
        return str(self.value)

    def __getattr__(self, name):
        return self.value.__getattr__(name)

    def __add__(self, val):
        return self.value + val
    def __sub__(self, val):
        return self.value - val
    def __mul__(self, val):
        return self.value * val
    def __div__(self, val):
        return self.value / val

    def __radd__(self, val):
        return self.value + val
    def __rsub__(self, val):
        return val - self.value
    def __rmul__(self, val):
        return self.value * val
    def __rdiv__(self, val):
        return val / self.value

graph = Graph()

if __name__ == '__main__':
    x = Cell([1, 2, 3])

    def f():
        ret = 0
        for i in x.value:
            ret += i

        return ret

    z = Cell(f, [x])

    print z.value
    x.value.append(4)
    x.updateValue()
    graph.updateCells()
    print z.value

    # cell stream:
    # modify ops: append (change next), modify (change from modification), deleteLast(backtrack)
    # dependent operations: map, foldr, filter...

    # output stream = map-accumulate-stream input-stream, function(ins)

    # more complex map:
    # cmap(input, selector, function)
    # selector receives a zip
    # or.. map(input1, input2, func(x y))


