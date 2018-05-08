

class Syntax(object):

    def __init__(self, syntax_results):
        self._raw_results = syntax_results
        self.dependencies = syntax_results["basicDeps"]

        def is_integer(s):
            try:
                int(s)
                return True
            except ValueError:
                return False

        self.index = dict((key, syntax_results[key]) for key in filter(lambda key: is_integer(key), syntax_results.keys()))

    def find_dependencies(self, types=None, governors=None, dependents=None):
        results = self.dependencies

        if types is not None:
            if type(types) is not list:
                types = [types]
            results = filter(lambda dependency: dependency[0] in types, results)

        if governors is not None:
            if type(governors) is not list:
                governors = [governors]
            results = filter(lambda dependency: dependency[1] in governors, results)

        if dependents is not None:
            if type(dependents) is not list:
                dependents = [dependents]
            results = filter(lambda dependency: dependency[2] in dependents, results)

        return list(results)