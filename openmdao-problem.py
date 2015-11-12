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

    root.add('thing', IndepVarComp('simtime', val="15.0"))
    root.add('p1', IndepVarComp('nz', val=1.0))
    root.add('p2', IndepVarComp('nn', val=1.0))
    root.add('modelica',
             OMModelWrapper('WindPowerPlants.Examples.GenericPlantRayleigh',
                            '/Users/adam/repo/WindPowerPlants/WindPowerPlants/package.mo'))
    root.add('tl', TakeLast())

    top.driver = UniformDriver(1)
    top.driver.add_desvar('p2.nn', low=1.0, high=10.0)
    top.driver.add_desvar('p1.nz', low=5.0, high=25.0)
    top.driver.add_objective('modelica.y_testvariable')

    root.connect('thing.simtime', 'modelica.stopTime')
    root.connect('p1.nz', 'modelica.nz')
    root.connect('p2.nn', 'modelica.nn')
    root.connect('modelica.y_testvariable', 'tl.input')

    # root.connect('thing.simtime', 'modelica.stopTime')
    # root.connect('thing2.nz', 'modelica.nz')

    recorder = CsvRecorder('dump.csv')
    recorder.options['record_params'] = True
    recorder.options['record_metadata'] = True
    recorder.options['record_resids'] = True
    top.driver.add_recorder(recorder)

    top.setup()
    top.run()

    print ('modelica.y_testvariable', top['modelica.y_testvariable'])
    print ('tl.output', top['tl.output'])

    top.driver.recorders[0].close()
