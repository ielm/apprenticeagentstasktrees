import pickle


@DeprecationWarning
class Ontology(object):
    ontology = {}

    def __init__(self):
        pass

    @classmethod
    def init_default(cls):
        import os
        path = os.path.relpath(__file__).replace("ontology.py", "resources/ontology_May_2017.p")
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
    def ancestors(cls, concept, include_self=False):
        c = Ontology.ontology[concept]

        results = []
        if include_self:
            results.append(concept)

        if c['IS-A']['VALUE'] is not None:

            isa = c['IS-A']['VALUE']
            if type(isa) != list:
                isa = [isa]

            for parent in isa:
                results.append(parent)
                results.extend(cls.ancestors(parent))

        return set(results)

    @classmethod
    def add_filler(cls, concept, slot, facet, filler):
        c = Ontology.ontology[concept]

        if slot not in c:
            c[slot] = {}

        s = c[slot]

        if facet not in s:
            s[facet] = []
        if type(s[facet]) != list:
            s[facet] = [s[facet]]

        f = s[facet]
        f.append(filler)