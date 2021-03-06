##
# Copyright 2009-2020 Ghent University
#
# This file is part of EasyBuild,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://www.vscentrum.be),
# Flemish Research Foundation (FWO) (http://www.fwo.be/en)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# https://github.com/easybuilders/easybuild
#
# EasyBuild is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation v2.
#
# EasyBuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EasyBuild.  If not, see <http://www.gnu.org/licenses/>.
##
"""
EasyBuild support for pybind11, implemented as an easyblock

@author: Alexander Grund (TU Dresden)
"""
import os
from easybuild.easyblocks.generic.cmakemake import CMakeMake
from easybuild.easyblocks.generic.pythonpackage import PythonPackage
from easybuild.easyblocks.generic.cmakepythonpackage import CMakePythonPackage
import easybuild.tools.environment as env
from easybuild.tools.build_log import EasyBuildError
from easybuild.tools.filetools import change_dir
from easybuild.tools.run import run_cmd


class EB_pybind11(CMakePythonPackage):
    """Build PyBind11 for consumption with python packages and CMake

    PyBind11 can be consumed by CMake projects using `find_package` and by
    Python packages using `import pybind11`
    Hence we need to install PyBind11 twice: Once with CMake and once with pip
    """
    @staticmethod
    def extra_options(extra_vars=None):
        """Easyconfig parameters specific to PyBind11: Set defaults"""
        extra_vars = PythonPackage.extra_options(extra_vars=extra_vars)
        extra_vars = CMakeMake.extra_options(extra_vars=extra_vars)
        extra_vars['use_pip'][0] = True
        extra_vars['sanity_pip_check'][0] = True
        extra_vars['download_dep_fail'][0] = True
        return extra_vars

    def test_step(self):
        """Run pybind11 tests"""
        # always run tests
        self.cfg['runtest'] = 'check'
        super(EB_pybind11, self).test_step()

    def install_step(self):
        """Install with cmake install and pip install"""
        build_dir = change_dir(self.cfg['start_dir'])
        PythonPackage.install_step(self)

        # Reset installopts (set by PythonPackage)
        self.cfg['installopts'] = ''
        change_dir(build_dir)
        CMakeMake.install_step(self)

    def sanity_check_step(self):
        """
        Custom sanity check for Python packages
        """
        # don't add user site directory to sys.path (equivalent to python -s)
        env.setvar('PYTHONNOUSERSITE', '1', verbose=False)
        # Get python includes
        fake_mod_data = self.load_fake_module(purge=True)
        cmd = "%s -c 'import pybind11; print(pybind11.get_include())'" % self.python_cmd
        out, ec = run_cmd(cmd, simple=False)
        if ec:
            raise EasyBuildError("Failed to get pybind11 includes!")
        python_include = out.strip()
        self.clean_up_fake_module(fake_mod_data)

        # Check for CMake config and includes
        custom_paths = {
            'files': ['share/cmake/pybind11/pybind11Config.cmake'],
            'dirs': ['include/pybind11', os.path.join(python_include, 'pybind11')],
        }
        # Check for Python module
        return PythonPackage.sanity_check_step(self, custom_paths=custom_paths)
