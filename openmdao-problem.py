from __future__ import print_function
from openmdao.components.indep_var_comp import IndepVarComp
from openmdao.components.exec_comp import ExecComp
from openmdao.core.component import Component
from openmdao.core.problem import Problem, Group
from openmdao.core.driver import Driver
from openmdao.drivers.scipy_optimizer import ScipyOptimizer
from openmdao.api import ExternalCode
from openmdao.recorders.dump_recorder import DumpRecorder
from openmdao.recorders.base_recorder import BaseRecorder
from ommodelwrapper.ommodelwrapper import OMModelWrapper
from openmdao.drivers.uniform_driver import UniformDriver
from openmdao.util.record_util import format_iteration_coordinate
from collections import Counter
import json
import sys
import os
import string
import random
import copy
import six
import csv
import numpy as np


class CsvRecorder(BaseRecorder):

    def __init__(self, out=sys.stdout):
        super(CsvRecorder, self).__init__()

        self._wrote_header = False
        self._parallel = False

        if out != sys.stdout:
            self.out = out
        self.writer = csv.writer(out)

    def startup(self, group):
        super(CsvRecorder, self).startup(group)

    def record_iteration(self, params, unknowns, resids, metadata):
        filtered_unknowns = [unknown for unknown in unknowns if unknown.startswith('tl_')]
        filtered_params = [param for param in params if param.startswith('modelica')]

        if self._wrote_header is False:
            self.writer.writerow(filtered_params + filtered_unknowns)
            self._wrote_header = True

        def munge(val):
            if isinstance(val, np.ndarray):
                return ",".join(map(str, val))
            return str(val)
        self.writer.writerow([munge(value['val']) for key, value in params.iteritems() if key in filtered_params] + [munge(value['val']) for key, value in unknowns.iteritems() if key in filtered_unknowns])

        if self.out:
            self.out.flush()

    def record_metadata(self, group):
        pass


class TakeLast(Component):
    def __init__(self):
        super(TakeLast, self).__init__()
        self.add_param('input', val=0.1)
        self.add_output('output', val=0.1, pass_by_obj=True)

    def solve_nonlinear(self, params, unknowns, resids):
        unknowns['output'] = params['input'][-1]


if __name__ == "__main__":
    top = Problem()

    root = top.root = Group()

    root.add('simprop', IndepVarComp('simtime', val="100"))
    root.add('p1', IndepVarComp('rho', val=1.0))
    root.add('p2', IndepVarComp('jturbine', val=1.0))
    root.add('p3', IndepVarComp('ratio', val=1.0))
    root.add('modelica',
             OMModelWrapper('WindPowerPlants.Examples.GenericPlantRayleigh',
                            '/Users/adam/repo/WindPowerPlants/WindPowerPlants/package.mo'))
    root.add('tl_peakPowerOutput', TakeLast())
    root.add('tl_integratedEnergy', TakeLast())

    top.driver = UniformDriver(5000)
    top.driver.add_desvar('p1.rho', low=1.0, high=1.5)
    top.driver.add_desvar('p2.jturbine', low=13000000*0.7, high=130000000*1.3)
    top.driver.add_desvar('p3.ratio', low=80.0, high=120.0)
    top.driver.add_objective('tl_peakPowerOutput.output')
    top.driver.add_objective('tl_integratedEnergy.output')

    root.connect('simprop.simtime', 'modelica.stopTime')
    root.connect('p1.rho', 'modelica.rho')
    root.connect('p2.jturbine', 'modelica.jturbine')
    root.connect('p3.ratio', 'modelica.ratio')
    root.connect('modelica.peakPowerOutput', 'tl_peakPowerOutput.input')
    root.connect('modelica.integratedEnergy', 'tl_integratedEnergy.input')

    # root.connect('thing.simtime', 'modelica.stopTime')
    # root.connect('thing2.nz', 'modelica.nz')

    recorder = CsvRecorder(open('dump.csv', 'w'))
    recorder.options['record_params'] = False
    recorder.options['record_metadata'] = False
    recorder.options['record_resids'] = False
    top.driver.add_recorder(recorder)

    top.setup()
    top.run()

    top.driver.recorders[0].close()
