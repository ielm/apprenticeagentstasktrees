ontology={
  'ARTIFACT-LEG': {
    'HAS-OBJECT-AS-PART': {
      'SEM': 'ARTIFACT-PART'
    }
  },
  'ARTIFACT-PART': {
    'HAS-OBJECT-AS-PART': {
      'SEM': 'ARTIFACT-PART'
    }
  },
  'CHAIR': {
    'HAS-OBJECT-AS-PART': {
      'SEM': ['ARTIFACT-LEG',
      'CHAIR-ARM',
      'SEAT',
      'CHAIR-BACK']
    }
  },
  'CHAIR-ARM': {
    'HAS-OBJECT-AS-PART': {
      'SEM': 'ARTIFACT-PART'
    }
  },
  'SEAT': {
    'HAS-OBJECT-AS-PART': {
      'SEM': 'ARTIFACT-PART'
    }
  },
  'CHAIR-BACK': {
    'HAS-OBJECT-AS-PART': {
      'SEM': 'ARTIFACT-PART'
    }
  },
  'SCREWDRIVER': {
    'HAS-OBJECT-AS-PART': {
      'SEM': 'ARTIFACT-PART'
    }
  },
  'SCREW': {
    'HAS-OBJECT-AS-PART': {
      'SEM': 'ARTIFACT-PART'
    }
  },
  'CAT': {
    'HAS-OBJECT-AS-PART': {
      'DEFAULT': ['HEAD',
      'VERTEBRAL-COLUMN'],
      'NOT': 'PLANT-PART',
      'SEM': ['SKELETON',
      'EYE',
      'MOUTH',
      'NOSE',
      'EAR',
      'TRUNK-OF-BODY',
      'ABDOMEN',
      'ANIMAL-TISSUE',
      'BLOOD',
      'ANIMAL-ORGAN',
      'SALIVA',
      'TONGUE',
      'TOOTH',
      'HAIR',
      'TAIL',
      'LEG',
      'PAW',
      'FUR']
    }
  },
  'TAIL': {
    'HAS-OBJECT-AS-PART': {
      'SEM': 'INANIMATE'
    }
  },
  'LEG': {
    'HAS-OBJECT-AS-PART': {
      'SEM': ['FOOT',
      'ANKLE',
      'HOOF',
      'CLAW',
      'PAW']
    }
  },
  'FOOT': {
    'HAS-OBJECT-AS-PART': {
      'SEM': 'ANATOMICAL-STRUCTURE'
    }
  },
  'ANKLE': {
    'HAS-OBJECT-AS-PART': {
      'SEM': 'ANATOMICAL-STRUCTURE'
    }
  },
  'MOUTH': {
    'HAS-OBJECT-AS-PART': {
      'SEM': ['TONGUE',
      'LIP',
      'TOOTH']
    }
  },
  'TONGUE': {
    'HAS-OBJECT-AS-PART': {
      'SEM': 'ANATOMICAL-STRUCTURE'
    }
  },
  'LIP': {
    'HAS-OBJECT-AS-PART': {
      'SEM': 'ANATOMICAL-STRUCTURE'
    }
  },
  'TOOTH': {
    'HAS-OBJECT-AS-PART': {
      'SEM': 'ANATOMICAL-STRUCTURE'
    }
  }
}