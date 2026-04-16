'''work arounds for dawgie inconsistencies'''

import dawgie


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
