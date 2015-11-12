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
from collections import Counter
import json
import sys
import os
import string
import random
import copy
import six

if __name__ == "__main__":
    top = Problem()

    root = top.root = Group()

    root.add('thing', IndepVarComp('simtime', val="15.0"))
    root.add('modelica', OMModelWrapper( 'WindPowerPlants.Examples.GenericPlantRayleigh', '/Users/adam/repo/WindPowerPlants/WindPowerPlants/package.mo'))
    # root.add('modelica', OMModelWrapper( 'WindPowerPlants/Examples/GenericPlantRayleigh', '/Users/adam/repo/WindPowerPlants/WindPowerPlants/'))

    # top.driver = ScipyOptimizer()
    # top.driver.options['optimizer'] = 'SLSQP'
    # top.driver.add_desvar('p1.Voltage', low=1.0, high=10.0)
    # top.driver.add_desvar('p2.Resistance', low=5.0, high=25.0)
    # top.driver.add_objective('tb.Current')

    root.connect('thing.simtime', 'modelica.stopTime')

    recorder = DumpRecorder()
    recorder.options['record_params'] = True
    recorder.options['record_metadata'] = True
    recorder.options['record_resids'] = True
    top.driver.add_recorder(recorder)

    top.setup()
    top.run()

    top.driver.recorders[0].close()
