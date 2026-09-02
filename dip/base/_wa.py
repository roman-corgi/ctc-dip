'''work arounds for dawgie inconsistencies'''

import dawgie
import dawgie.context
import importlib

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
            visitor.add_declaration_inline(f'{k} ({len(v)}):', tag='b')
            visitor.add_declaration_inline('', list=[str(p) for p in v])
        else:
            visitor.add_declaration_inline(
                f'{k}: {type(v)} does not have a standard display'
            )
    visitor.add_declaration_inline('', div='</div>')


def sv_lookup(name: str) -> _types.Manifest:
    '''use a full name from dawgie.db.search().find() to resolve the object

    Given a full name - rid.target.task.algorithm.state_vector.value - break
    it is apart into its constutients, build its underlying dawgie object,
    then load it.
    '''
    rid, target, task, algn, svn = name.split('.')[:5]
    runid = int(rid)
    mod = importlib.import_module(
        '.'.join([dawgie.context.ae_base_package, task]).replace('..', '.')
    )
    bot = (
        mod.regress(task, 1, target)
        if runid == 0
        else (
            mod.analysis(task, 1, runid)
            if target == '__all__'
            else mod.task(task, 1, runid, target)
        )
    )
    alg = list(filter(lambda x, a=algn: x.name() == a, bot.routines()))[0]
    sv = list(filter(lambda x, s=svn: x.name() == s, alg.state_vectors()))[0]
    dawgie.db.reset(runid, target, task, alg)
    ds = dawgie.db.connect(alg, bot, target)
    ds.load()
    return sv
