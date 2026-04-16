'''define the hard bits of recipe'''

import dip.base
import dip.bindings.recipe


class FSM(dip.base.Orchestrator):
    def _do_delegation(self):
        xml = self._load('recipe.xml')
        rcp = dip.bindings.recipe.CreateFromDocument(xml)
        self._fill(rcp, 'recipe.xml')
        return dip.base.ProductStatus.ALL
