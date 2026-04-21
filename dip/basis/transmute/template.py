'''Code templates for letting model.Class fill itself out'''

from . import Kind
from string import Template

CODE_BLOCKS = {
    Kind.ALGORITHM: Template('''
class ${cls_definition}:
    def __init__(self):
        dawgie.Algorithm.__init__(self)
        self._version_ = dawgie.VERSION(${version})
${svs_init}
${vrefs_init}

    def name(self) -> str:
        return "${cls_myname}"

    def previous(self) -> [dawgie.SV_REF, dawgie.V_REF]:
        return [${vrefs_list}]

    def run(self, ds:dawgie.Dataset, _ps):
        machine = ${cls_fsm_path}.${cls_fsm_class}()
        dip.basis.fsm.build(machine)
        machine.features = dip.base.features_asdict(self.previous())
        machine.inputs = dip.base.ds_asdict(self)
        machine.outputs.update(self.sv_as_dict())
        machine.do()
        if machine.panicked:
            raise dawgie.AbortAEError('we sank!')
        if machine.retargets:
            for target,svs in machine.retargets.items():
                for sv in svs:
                    self.sv_as_dict()[sv.name()].clear()
                    self.sv_as_dict()[sv.name()].update(sv)
                ds.retarget(target,[]).update()
        else:
            ds.update()

    def state_vectors(self) -> [dawgie.StateVector]:
        return [${svs_list}]
    '''),
    Kind.ANALYZER: Template('''
class ${cls_definition}:
    def __init__(self):
        dawgie.Analyzer.__init__(self)
        self._version_ = dawgie.VERSION(${version})
${svs_init}
${vrefs_init}

    def name(self) -> str:
        return "${cls_myname}"

    def run(self, aspects:dawgie.Aspect):
        machine = ${cls_fsm_path}.${cls_fsm_class}()
        dip.basis.fsm.build(machine)
        machine.features = dip.base.features_asdict(self.traits())
        machine.inputs = aspects
        machine.outputs.update(self.sv_as_dict())
        machine.do()
        if machine.panicked:
            raise dawgie.AbortAEError('we sank!')
        aspects.ds().update()

    def state_vectors(self) -> [dawgie.StateVector]:
        return [${svs_list}]

    def traits(self) -> [dawgie.SV_REF, dawgie.V_REF]:
        return [${vrefs_list}]
    '''),
    Kind.REGRESSION: Template('''
class ${cls_definition}:
    def __init__(self):
        dawgie.Regression.__init__(self)
        self._version_ = dawgie.VERSION(${version})
${svs_init}
${vrefs_init}

    def name(self) -> str:
        return "${cls_myname}"

    def run(self, _ps: int, timeline: dawgie.Timeline):
        machine = ${cls_fsm_path}.${cls_fsm_class}()
        dip.basis.fsm.build(machine)
        machine.features = dip.base.features_asdict(self.variables())
        machine.inputs = timeline
        machine.outputs.update(self.sv_as_dict())
        machine.do()
        if machine.panicked:
            raise dawgie.AbortAEError('we sank!')
        timeline.ds().update()

    def state_vectors(self) -> [dawgie.StateVector]:
        return [${svs_list}]

    def variables(self) -> [dawgie.SV_REF, dawgie.V_REF]:
        return [${vrefs_list}]
    '''),
    Kind.STATE_VECTOR: Template('''
class ${cls_definition}:
    def __init__(self):
        dawgie.StateVector.__init__(self)
        self._version_ = dawgie.VERSION(${version})
${values}

    def name(self) -> str:
        return "${cls_myname}"

    def view(self, caller, visitor):
        try:
            super().view(caller, visitor)
        except NotImplementedError:
            pass  # ignore the error and try something else
        dip.base.generic_view(self, visitor)
        return
    '''),
    Kind.VALUE: Template(''),
}
