import pickle

ontology = {}  # pickle.load(open("../backend/resources/ontology_May_2017.p", "rb"))


def init_from_file(path):
    with open(path, mode="rb") as f:
        global ontology
        ontology = pickle.load(f)


def init_from_ontology(ont):
    global ontology
    ontology = ont


def contains(concept, property, facet, value):
    c = ontology[concept]

    if property not in c:
        return False
    if facet not in c[property]:
        return False

    values = c[property][facet]
    if type(values) != list:
        values = [values]

    candidates = [value]
    candidates.extend(ancestors(value))

    return len(set(values).intersection(set(candidates))) > 0


def ancestors(concept):
    c = ontology[concept]

    results = []
    if c['IS-A']['VALUE'] is not None:

        isa = c['IS-A']['VALUE']
        if type(isa) != list:
            isa = [isa]

        for parent in isa:
            results.append(parent)
            results.extend(ancestors(parent))

    return set(results)

# ontology={
#   'ARTIFACT-LEG': {
#     'HAS-OBJECT-AS-PART': {
#       'SEM': 'ARTIFACT-PART'
#     }
#   },
#   'ARTIFACT-PART': {
#     'HAS-OBJECT-AS-PART': {
#       'SEM': 'ARTIFACT-PART'
#     }
#   },
#   'CHAIR': {
#     'HAS-OBJECT-AS-PART': {
#       'SEM': ['ARTIFACT-LEG',
#       'CHAIR-ARM',
#       'SEAT',
#       'CHAIR-BACK']
#     }
#   },
#   'CHAIR-ARM': {
#     'HAS-OBJECT-AS-PART': {
#       'SEM': 'ARTIFACT-PART'
#     }
#   },
#   'SEAT': {
#     'HAS-OBJECT-AS-PART': {
#       'SEM': ['ARTIFACT-PART', 'ARTIFACT-LEG']
#     }
#   },
#   'CHAIR-BACK': {
#     'HAS-OBJECT-AS-PART': {
#       'SEM': 'ARTIFACT-PART'
#     }
#   },
#   'SCREWDRIVER': {
#     'HAS-OBJECT-AS-PART': {
#       'SEM': 'ARTIFACT-PART'
#     }
#   },
#   'SCREW': {
#     'HAS-OBJECT-AS-PART': {
#       'SEM': 'ARTIFACT-PART'
#     }
#   },
#   'CAT': {
#     'HAS-OBJECT-AS-PART': {
#       'DEFAULT': ['HEAD',
#       'VERTEBRAL-COLUMN'],
#       'NOT': 'PLANT-PART',
#       'SEM': ['SKELETON',
#       'EYE',
#       'MOUTH',
#       'NOSE',
#       'EAR',
#       'TRUNK-OF-BODY',
#       'ABDOMEN',
#       'ANIMAL-TISSUE',
#       'BLOOD',
#       'ANIMAL-ORGAN',
#       'SALIVA',
#       'TONGUE',
#       'TOOTH',
#       'HAIR',
#       'TAIL',
#       'LEG',
#       'PAW',
#       'FUR']
#     }
#   },
#   'TAIL': {
#     'HAS-OBJECT-AS-PART': {
#       'SEM': 'INANIMATE'
#     }
#   },
#   'LEG': {
#     'HAS-OBJECT-AS-PART': {
#       'SEM': ['FOOT',
#       'ANKLE',
#       'HOOF',
#       'CLAW',
#       'PAW']
#     }
#   },
#   'FOOT': {
#     'HAS-OBJECT-AS-PART': {
#       'SEM': 'ANATOMICAL-STRUCTURE'
#     }
#   },
#   'ANKLE': {
#     'HAS-OBJECT-AS-PART': {
#       'SEM': 'ANATOMICAL-STRUCTURE'
#     }
#   },
#   'MOUTH': {
#     'HAS-OBJECT-AS-PART': {
#       'SEM': ['TONGUE',
#       'LIP',
#       'TOOTH']
#     }
#   },
#   'TONGUE': {
#     'HAS-OBJECT-AS-PART': {
#       'SEM': 'ANATOMICAL-STRUCTURE'
#     }
#   },
#   'LIP': {
#     'HAS-OBJECT-AS-PART': {
#       'SEM': 'ANATOMICAL-STRUCTURE'
#     }
#   },
#   'TOOTH': {
#     'HAS-OBJECT-AS-PART': {
#       'SEM': 'ANATOMICAL-STRUCTURE'
#     }
#   }
# }