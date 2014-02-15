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
                layer[item].updateValue()

class Cell(object):
    cells = 0

    def __init__(self, formula, deps = []):
        self.formula = formula
        #self.value = value  # can be a lambda
        self.deps = deps
        self.dirty = False
        self.weight = 0
        self.value = None

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



graph = Graph()



cell = Cell(5)
cell2 = Cell(lambda : cell + 7, [cell])
cell3 = Cell(lambda : cell + cell2.value, [cell, cell2])
cell4 = Cell(lambda : cell + cell2.value + 9, [cell, cell2])

graph.updateCells()

print cell.value
print cell2.value
print cell3
print cell4

cell = Cell(lambda : 7)
graph.updateCells()

print cell.value
print cell2.value
print cell3
print cell4