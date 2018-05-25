# FR Instances deviate a bit from regular instances in that each property (triple) they contain is subject to
# both a confidence value (0.0 - 1.0) and a list of ambiguities (in the case of imperfect resolution).  Further,
# properties are "learned" at distinct times - while many properties may be learned at once, it is possible to
# then learn new properties at a notable point in the future, so each property also maintains an abstract
# timestamp (incrementing integer).

# It is perfectly reasonable for an instance to be a THEME-OF A-1, THEME-OF B-1, and also be a THEME-OF (A-1 or B-1).
# That is to say:
#  1) at time 0 (or later, but not later than time n), it is known that the instance is a THEME-OF A-1;
#  2) at time 0 (or later, but not later than time n), it is also known that the instance is a THEME-OF B-1;
#  3) at time n (or later), it is ambiguously reported that the instance is a THEME-OF either A-1 or B-1
# We make this distinction because we have unambiguous evidence prior that A-1 and B-1 are both unique fillers
# of the property; finding that they are later ambiguous only relates to *that timestamp*, which is a new and
# unique triple, and therefore the ambiguity must be tied to only that triple, and should not impact the other data.

# To handle these requirements, the FRInstance behaves like a dictionary (similar to Instances); it will return
# a list of fillers for a given key, or an empty list; and will return False if the fillers list is empty when
# using contains().  However, rather than returning just IDs (or attribute values) as fillers, it returns
# FRFiller objects, which contain the filler, along with the other meta-data, including links to ambiguities.
# In the above example, four fillers would be returned, A-1 (t=0), B-1 (t=0), A-1 (t=0, amb=#4), B-1 (t=0, amb=#3),
# where #3 and #4 are IDs referring to specific FRFillers.

# Finally, we must maintain the current abstract time reference (self._time, default to 0).  There is an explicit
# call that must be made to advance time - this should be called after all data from one TMR has been populated
# into the FRInstance, to maintain proper ambiguity tracking.

from backend.models.instance import Instance


class FRInstance(Instance):

    def __init__(self, name, concept, index, uuid=None, properties=None, subtree=None):
        super().__init__(name, concept, uuid=uuid, properties=properties, subtree=subtree)

        self.index = index
        self._time = 0
        self._ambiguities = []

        self._from = {}  # Used to track TMR instances that derived this instance
        self._context = {}  # Used to track context-sensitive learning properties

    def __setitem__(self, key, value):
        if not type(value) == FRInstance.FRFiller:
            raise Exception("Values must be FRFiller objects.")

        value = [value] if not type(value) == list else value

        if key in self._storage:
            self._storage[key].extend(value)
        else:
            self._storage[key] = value

    def __getitem__(self, key):
        if key in self._storage:
            return self._storage[key]
        return []

    def __iter__(self):
        return iter(self._storage)

    def __len__(self):
        return len(self._storage)

    def __contains__(self, key):
        return key in self._storage

    def attribute_to(self, tmrinstance):
        self._from[tmrinstance.uuid] = tmrinstance

    def is_attributed_to(self, tmrinstance):
        return tmrinstance.uuid in self._from

    def context(self):
        return self._context

    def does_match_context(self, context):
        if type(context) is not dict:
            raise Exception("Context must be a dictionary.")

        for c in context:
            if c not in self._context:
                return False
            if self._context[c] != context[c]:
                return False

        return True

    # Use this method to remove a FRFiller.  All fillers of the property with exactly the one value (no ambiguity)
    # will be deleted.
    def forget(self, property, value):
        self._storage[property] = list(filter(lambda filler: not (filler.value == value and len(filler.ambiguities) == 0), self._storage[property]))

    # Use this method to add values to the instance.  Provide the property, and a set of ambiguous values
    # to record.  Note, if the values are not ambiguous (but rather, just multiple values), pass a set
    # and call this method once for each unique value.  Any list of size greater than one will be assumed to be
    # ambiguous.
    def remember(self, property, values, filter_redundant=True):
        if not type(values) == set:
            values = {values}

        # Here we find all of the current values of the property, and filter out any redundancy (just being sure
        # not to add the exact same value twice).
        if filter_redundant and len(self[property]) > 0:
            current_fillers = filter(lambda filler: filler.time == self._time, self[property])
            current_values = map(lambda filler: filler.value, current_fillers)
            values = filter(lambda value: value not in current_values, values)

        fillers = list(map(lambda value: FRInstance.FRFiller(self._time, value), values))
        ids = list(map(lambda filler: filler.id, fillers))
        for filler in fillers:
            for id in ids:
                filler.add_ambiguity(id)

        for filler in fillers:
            self[property] = filler

    def advance(self):
        self._time += 1

    def has_fillers(self, query, expand_sets={}):
        for key in query:
            if key not in self:
                return False

            value = query[key]
            fillers = self[key]

            filler_values = list(map(lambda filler: filler.value, fillers))
            sets_to_expand = list(filter(lambda set: set in filler_values, expand_sets.keys()))
            expanded_values = list(map(lambda set: expand_sets[set]["MEMBER-TYPE"], sets_to_expand))
            for ev in expanded_values:
                filler_values.extend(map(lambda filler: filler.value, ev))

            if value not in filler_values:
                return False

        return True

    def __str__(self):
        lines = [self.name]
        for property in self:
            line = "  " + property + " = " + ", ".join(list(map(lambda filler: str(filler), self[property])))
            lines.append(line)
        for c in self._context:
            line = "  " + c + " = " + str(self._context[c])
            lines.append(line)

        return "\n".join(lines)

    def __repr__(self):
        return self.name

    class FRFiller(object):

        id_index = 0

        def __init__(self, time, value, ambiguities=None):
            self.id = FRInstance.FRFiller.id_index
            FRInstance.FRFiller.id_index += 1

            self.time = time
            self.value = value

            if ambiguities is not None and type(ambiguities) == set:
                self.ambiguities = ambiguities
            else:
                self.ambiguities = set()

        def add_ambiguity(self, id):
            if id == self.id:
                return

            self.ambiguities.add(id)

        def remove_ambiguity(self, id):
            self.ambiguities.remove(id)

        def is_ambiguous(self):
            return len(self.ambiguities) > 0

        def __eq__(self, other):
            if not type(other) == FRInstance.FRFiller:
                return False

            if self.time != other.time:
                return False

            if self.value != other.value:
                return False

            if self.ambiguities != other.ambiguities:
                return False

            return True

        def __str__(self):
            ambiguity = ""
            if len(self.ambiguities) > 0:
                ambiguity = " ambiguous with " + ", ".join(list(map(lambda id: str(id), self.ambiguities)))

            return "[" + str(self.id) + "]" + self.value + ambiguity