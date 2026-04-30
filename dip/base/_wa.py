'''work arounds for dawgie inconsistencies'''

import dawgie

from . import _types


def ds_asdict(alg: dawgie.Algorithm) -> {str: dawgie.StateVector}:
    '''dawgie.Dataset should act as a dictionary

    dawgie.Aspect and dawgie.Timeline are more modern and emulate dictionary
    behavior with keys and values. dawgie.Dataset predates them and does not.
    This function is a workaround to make it look line one where the keys are
    `task.algname.svname' and values are the corresponding dawgie.StateVector.
    '''
    return {
        '.'.join(
            [dawgie.util.task_name(p.factory), p.impl.name(), p.item.name()]
        ): p.item
        for p in alg.previous()
    }


def features_asdict(vrefs: [dawgie.V_REF]) -> {str: str}:
    '''know which features of a dawgie.StateVector were actually loaded

    The names will match the state vectors names naturally found in aspects,
    datasets, and timelines. Note that datasets have to be run through ds_asdict
    in this module.
    '''
    result = {}
    for vref in vrefs:
        svn = '.'.join(
            [
                dawgie.util.task_name(vref.factory),
                vref.impl.name(),
                vref.item.name(),
            ]
        )
        if svn not in result:
            result[svn] = []
        result[svn].append(vref.feat)
    return result


def generic_view(sv: dawgie.StateVector, visitor: dawgie.Visitor):
    '''for the auto-generated implementations of dawgie.StateVector

    Does its best to turn the contents of the state vector in a reasonable
    view. Since most/all of the auto-generated state vectors are lists of
    files and/or manifests, should be straight forward.
    '''
    visitor.add_declaration_inline('', div='<div><hr>')
    for k, v in sorted(sv.items(), key=lambda t: t[0]):
        if isinstance(v, _types.AuxillaryFile):
            visitor.add_declaration_inline(f'{k}:', tag='b')
            visitor.add_declaration_inline(str(v.name))
        elif isinstance(v, _types.Manifest):
            visitor.add_declaration_inline(f'{k}:', tag='b')
            visitor.add_declaration_inline('', list=[str(p) for p in v])
        else:
            visitor.add_declaration_inline(
                f'{k}: {type(v)} does not have a standard display'
            )
    visitor.add_declaration_inline('', div='</div>')
