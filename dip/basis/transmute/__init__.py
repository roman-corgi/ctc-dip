'''transmute the basis into the specific (or concrete)

While not quite alchemy (air to gold), it can appear that way when transforming the loosely defiined DSL contained with the GraphViz files.

All of the GraphViz file (`.dot` files) in the dip.basis package are processed.
They are first read and converted to a more effecient form of Python objects.
They are then written back out into the package `dip` for DAWGIE to use. All
Python modules it writes to will be created if they do not exist. Within the
module, it will place generated code between two comments that clearly define
a region the user should not edit or change. It will be completely overwritten
every transmutation. Code outside of these blocks will be undisturbed.

In order for elements in GraphViz file to be processed, certain keywords must
be present. These keywords are the DSL definition. To be detected as:


runnables (dawgie.Algorithm | dawgie.Analyzer | dawgie.Regression)
  - runname : The name that will appear in the DAWGIE DAG. Note, this also
              defines the parent dawgie.Task. For instance, `l1.cat` defnines
              the task `l1` that contains an algorithmic element `cat`.

  - runtype : The class it should inherit from DAWGIE and can be:
              dawgie.Algorithm | dawgie.Analyzer | dawgie.Regression

  - fsmtype : The full class name to connect a dawgie runnable to the dip FSM
              like `dip.base.Drp` or `dip.base.Internal`.


dawgie.StateVector
  - svname  : The name that will appear in the DAWGIE DAG. Note, this also
              defines the parent algorithmic element and dawgie.Task. For
              example `l1.cat.channel` defines the task `l1`, the algorithmic
              element `cat`, and the state vector `channel`.
  - svtype  : The class name that extends dawgie.StateVector and given svname.

dawgie.Value
  - valname : The name that will appear in the DAWGIE DAG. Note, this also
              defines the parent task, algorithmic element, and state vector.
              For example, `l1.cat.channel.eng_a` defines the task `l1`,
              algorithmic element `cat`, state vector `channel`, and value
              `eng_a`.
  - valtype : The name of the user created dawgie.Value. For example,
              `dip.Manifest`

For nodes of dawgie.StateVector and dawgie.Value, if they have no source, then
they are considered inputs. If they have no destination, then they are
considered outputs. Inputs and outputs are in reference to the algorithmic
element in their respective names.
'''

import enum


@enum.unique
class Kind(enum.Enum):
    ALGORITHM = 'dawgie.Algorithm'
    ANALYZER = 'dawgie.Analyzer'
    REGRESSION = 'dawgie.Regression'
    STATE_VECTOR = 'dawgie.StateVector'
    VALUE = 'dawgie.Value'
    V_REF = 'dawgie.V_REF'


RUNNABLE = (Kind.ALGORITHM, Kind.ANALYZER, Kind.REGRESSION)


KEYWORDS = {
    Kind.ALGORITHM: ('runname', 'runtype', 'fsmtype'),
    Kind.ANALYZER: ('runname', 'runtype', 'fsmtype'),
    Kind.REGRESSION: ('runname', 'runtype', 'fsmtype'),
    Kind.STATE_VECTOR: ('svname', 'clsname'),
    Kind.VALUE: ('valname', 'valtype'),
}

ALL_KEYWORDS = {kw for keywords in KEYWORDS.values() for kw in keywords}

BEGIN = '# <-------------  BELOW: auto generated code below do not edit  ------------->'  # fmt: skip
END = '# <-------------  ABOVE: auto generated code above do not edit  ------------->'  # fmt: skip
