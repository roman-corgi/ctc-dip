'''Manage the FSM in a uniform way for all algorithms

The class FiniteStateModel is meant to help form a strong typing bond between
the GraphViz file trans_fsm.dot and the python transitions module. It need not
be here so keeping the GraphViz and this synchronized is not required but highly
recommended. In the end, GraphViz always wins.

The function build() is a factory function to produce a complete FSM.
'''

import abc
import dawgie
import enum
import logging
import os
import pydot
import transitions
import typing

LOG = logging.getLogger(__name__)


@enum.unique
class AlertStatus(enum.Enum):
    FOUNDERED = enum.auto()
    RECOVERED = enum.auto()
    RETRY = enum.auto()
    SECURED = enum.auto()


@enum.unique
class ProductStatus(enum.Enum):
    ALL = enum.auto()
    NONE = enum.auto()
    SOME = enum.auto()


class AbstractModel(abc.ABC):  # pylint: disable=too-many-instance-attributes
    '''This class is to strongly type the binding from GraphViz to transitions'''

    @abc.abstractmethod
    def _do_construction(self) -> bool:
        '''do the construnction state

        Return true if all went well. Other false or throw an exception, which
        will be logged.
        '''
        pass

    @abc.abstractmethod
    def _do_delegation(self) -> ProductStatus:
        pass

    @abc.abstractmethod
    def _do_general_quarters(self) -> AlertStatus:
        '''Called by do_general_quarters()

        do_general_quarters() has already secured all of the logs and prepared
        them for the next step. This function determines what to do with
        information that has been prepared.
        '''
        pass

    def _do_panic(self):
        pass

    @abc.abstractmethod
    def _do_sanitization(self):
        pass

    @abc.abstractmethod
    def _do_warehouse(self) -> bool:
        pass

    def __init__(self):
        abc.ABC.__init__(self)
        self.__dawgie_exc = None
        self.__features = {}
        self.__finale = None
        self.__log = LOG.getChild(self.__class__.__name__)
        self.__inputs: [dawgie.Aspect, dawgie.Dataset, dawgie.Timeline] = None
        self.__outputs: dict[str, dawgie.StateVector] = {}
        self.__panicked = False
        self.__retargets: dict[str, list[dawgie.StateVector]] = {}
        self.__target: str = ''
        self.state: str = None  # transitons will manage but make pylint happy

    @property
    def dawgie_exc(
        self,
    ) -> [None, dawgie.NoValidInputDataError, dawgie.NoValidOutputDataError]:
        return self.__dawgie_exc

    @property
    def features(self) -> {str: str}:
        return self.__features

    @features.setter
    def features(self, value: {str: str}):
        self.__features = value

    @property
    def final_state(self) -> str:
        return self.__finale

    @property
    def inputs(self) -> [dawgie.Aspect, dawgie.Dataset, dawgie.Timeline]:
        return self.__inputs

    @inputs.setter
    def inputs(self, value: [dawgie.Aspect, dawgie.Dataset, dawgie.Timeline]):
        self.__inputs = value

    @property
    def outputs(self) -> {str: dawgie.StateVector}:
        return self.__outputs

    @property
    def panicked(self) -> bool:
        return self.__panicked

    @property
    def retargets(self) -> dict[str, list[dawgie.StateVector]]:
        return self.__retargets

    @property
    def target(self) -> str:
        return self.__target

    @target.setter
    def target(self, s: str):
        self.__target = s

    @final_state.setter
    def final_state(self, finale: str):
        self.__finale = finale

    @typing.final
    def do(self):
        trigger = type(None)  # translates to No-Op but is not None for the test
        while trigger is not None:
            trigger()
            trigger = getattr(self, f'do_{self.state}')()
        if self.final_state != self.state:
            self.__log.error(
                'The model is broken because there was not transition '
                'trigger after calling do_%s()',
                self.state,
            )

    @typing.final
    def do_construction(self):
        try:
            if self._do_construction():
                return self.workspace  # pylint: disable=no-member
            return self.no_workspace  # pylint: disable=no-member
        except:  # noqa; E722 # pylint: disable=bare-except
            self.__log.exception(
                'unhandled exception caught and broadly handled here'
            )
            return self.no_workspace  # pylint: disable=no-member

    @typing.final
    def do_delegation(self):
        try:
            match self._do_delegation():
                case ProductStatus.ALL:
                    return self.all_products  # pylint: disable=no-member
                case ProductStatus.NONE:
                    return self.no_products  # pylint: disable=no-member
                case ProductStatus.SOME:
                    return self.incomplete_products  # pylint: disable=no-member
                case _:
                    return self.incomplete_products  # pylint: disable=no-member
        except (
            dawgie.NoValidInputDataError,
            dawgie.NoValidOutputDataError,
        ) as e:
            self._dawgie_exc = e
            return self.incomplete_products  # pylint: disable=no-member
        except:  # noqa; E722 # pylint: disable=bare-except
            self.__log.exception(
                'unhandled exception caught and broadly handled here'
            )
            return self.incomplete_products  # pylint: disable=no-member

    @typing.final
    def do_general_quarters(self):
        try:
            match self._do_general_quarters():
                case AlertStatus.FOUNDERED:
                    return self.foundering  # pylint: disable=no-member
                case AlertStatus.RECOVERED:
                    return self.recovered  # pylint: disable=no-member
                case AlertStatus.RETRY:
                    return self.retry  # pylint: disable=no-member
                case AlertStatus.SECURED:
                    return self.secured  # pylint: disable=no-member
                case _:
                    return self.foundering  # pylint: disable=no-member
        except:  # noqa; E722 # pylint: disable=bare-except
            self.__log.exception(
                'unhandled exception caught and broadly handled here'
            )
            return self.foundering  # pylint: disable=no-member

    @typing.final
    def do_panic(self):
        try:
            self.__panicked = True
            self._do_panic()  # pylint: disable=no-member
        except:  # noqa; E722 # pylint: disable=bare-except
            LOG.exception('unhandled user exception caught and handled here.')
        return self.sent_up_flare  # pylint: disable=no-member

    @typing.final
    def do_sanitization(self):
        try:
            self._do_sanitization()
        except:  # noqa; E722 # pylint: disable=bare-except
            LOG.exception('worst place for unhandled exception')

    @typing.final
    def do_warehouse(self):
        try:
            if self._do_warehouse():
                return self.archived  # pylint: disable=no-member
            return self.not_archived  # pylint: disable=no-member
        except:  # noqa; E722 # pylint: disable=bare-except
            LOG.exception('unhandled exception caught and broadly handled here')
            return self.not_archived  # pylint: disable=no-member


def _check(i, t):
    if not i:
        raise ValueError('no initial state was set with terminal="initial"')
    if not t:
        raise ValueError('no final state was set with terminal="final"')
    if len(i) > 1:
        raise ValueError(
            'too many initial state are set with terminal="initial"'
        )
    if len(t) > 1:
        raise ValueError('too many final state are set with terminal="final"')


def build(model: AbstractModel) -> transitions.Machine:
    '''Build a complete FSM

    To build a complete FSM, we need an instance of a FiniteStateModel and the
    GraphViz file fsm.dot.

    Each GraphViz node that is a state:

    - Must have the attribute "state" allowing for visible items that are
      superfluous to the FSM but have meaning to a viewer of the image.
    - One node must contain the attribute "terminal" that is equal to "initial".
      One node must contain the attribute "terminal" that is equal to "final".
      If more than one node contains either of these pairs, an error will occur.

    Each GraphViz edge that is a trigger:

    - Must have the attribute "trigger" allowing for visible items that are
      superfluous to teh FSM but have meaning to a viewer of the image.
    '''
    fn = os.path.join(os.path.dirname(__file__), 'fsm.dot')
    if not os.path.isfile(fn):
        raise ValueError(f'the file "{fn}" does not exist')
    graph = pydot.graph_from_dot_file(fn)[0]
    i = []
    t = []
    states = []
    for node in graph.get_nodes():
        na = node.get_attributes()
        if 'state' in na:
            states.append(na['state'].replace('"', ''))
            if 'terminal' in na:
                tv = na['terminal'].replace('"', '')
                if tv == 'initial':
                    i.append(states[-1])
                if tv == 'final':
                    t.append(states[-1])
    _check(i, t)
    model.final_state = t[0]
    initial = i[0]
    trns = []
    for edge in graph.get_edges():
        ea = edge.get_attributes()
        if 'trigger' in ea:
            dst = graph.get_node(edge.get_destination())[0]
            src = graph.get_node(edge.get_source())[0]
            if 'state' not in dst.get_attributes():
                raise ValueError(
                    f'the trigger {ea["trigger"]} destination '
                    f'state "{edge.get_destination()[0]}" does not have '
                    'the attribute "state"'
                )
            if 'state' not in src.get_attributes():
                raise ValueError(
                    f'the trigger {ea["trigger"]} source '
                    f'state "{edge.get_source()[0]}" does not have the '
                    'attribute "state"'
                )
            trns.append(
                {
                    'dest': dst.get_attributes()['state'].replace('"', ''),
                    'source': src.get_attributes()['state'].replace('"', ''),
                    'trigger': ea['trigger'].replace('"', ''),
                }
            )
    return transitions.Machine(
        model=model, states=states, transitions=trns, initial=initial
    )
