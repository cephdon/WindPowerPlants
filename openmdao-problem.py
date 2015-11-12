from __future__ import print_function
from openmdao.components.indep_var_comp import IndepVarComp
from openmdao.components.exec_comp import ExecComp
from openmdao.core.component import Component
from openmdao.core.problem import Problem, Group
from openmdao.core.driver import Driver
from openmdao.drivers.scipy_optimizer import ScipyOptimizer
from openmdao.api import ExternalCode
from openmdao.recorders.dump_recorder import DumpRecorder
from ommodelwrapper.ommodelwrapper import OMModelWrapper
from openmdao.drivers.uniform_driver import UniformDriver
from openmdao.recorders.csv_recorder import CsvRecorder
from collections import Counter
import json
import sys
import os
import string
import random
import copy
import six
import numpy as np


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

    root.add('simprop', IndepVarComp('simtime', val="15.0"))
    root.add('p1', IndepVarComp('rho', val=1.0))
    root.add('p2', IndepVarComp('jturbine', val=1.0))
    root.add('p3', IndepVarComp('ratio', val=1.0))
    root.add('modelica',
             OMModelWrapper('WindPowerPlants.Examples.GenericPlantRayleigh',
                            '/Users/adam/repos/WindPowerPlants/WindPowerPlants/package.mo'))
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

    recorder = CsvRecorder('dump.csv')
    recorder.options['record_params'] = False
    recorder.options['record_metadata'] = False
    recorder.options['record_resids'] = False
    top.driver.add_recorder(recorder)

    top.setup()
    top.run()

    top.driver.recorders[0].close()
