import pickle

#ontology = {}  # pickle.load(open("../backend/resources/ontology_May_2017.p", "rb"))


class Ontology(object):
    ontology = {}

    def __init__(self):
        pass

    @classmethod
    def init_default(cls):
        import os
        path = os.path.relpath(__file__).replace("mini_ontology.py", "resources/ontology_May_2017.p")
        cls.init_from_file(path)

    @classmethod
    def init_from_file(cls, path):
        with open(path, mode="rb") as f:
            global ontology
            Ontology.ontology = pickle.load(f)

    @classmethod
    def init_from_ontology(cls, ont):
        global ontology
        Ontology.ontology = ont

    @classmethod
    def contains(cls, concept, property, facet, value):
        c = Ontology.ontology[concept]

        if property not in c:
            return False
        if facet not in c[property]:
            return False

        values = c[property][facet]
        if type(values) != list:
            values = [values]

        candidates = [value]
        candidates.extend(cls.ancestors(value))

        return len(set(values).intersection(set(candidates))) > 0

    @classmethod
    def ancestors(cls, concept):
        c = Ontology.ontology[concept]

        results = []
        if c['IS-A']['VALUE'] is not None:

            isa = c['IS-A']['VALUE']
            if type(isa) != list:
                isa = [isa]

            for parent in isa:
                results.append(parent)
                results.extend(cls.ancestors(parent))

        return set(results)