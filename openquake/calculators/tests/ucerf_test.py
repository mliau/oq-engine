# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2019 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import unittest
from openquake.baselib.general import gettemp
from openquake.calculators.export import export
from openquake.calculators.views import view
from openquake.calculators import ucerf_base
from openquake.qa_tests_data import ucerf
from openquake.calculators.tests import CalculatorTestCase


class UcerfTestCase(CalculatorTestCase):

    def test_event_based(self):
        self.run_calc(ucerf.__file__, 'job.ini')
        gmv_uc = view('global_gmfs', self.calc.datastore)
        # check the distribution of the events
        self.assertEventsByRlz([2, 2, 2, 2, 6, 6, 2, 2, 2, 2, 6, 6, 2, 2, 3,
                                3, 6, 6, 1, 1, 1, 1, 6, 6, 2, 2, 3, 3, 2, 2,
                                2, 2, 3, 3, 2, 2, 3, 3, 3, 3, 2, 2, 3, 3,
                                3, 3, 3, 3])

        [fname] = export(('ruptures', 'csv'), self.calc.datastore)
        # check that we get the expected number of ruptures
        with open(fname) as f:
            self.assertEqual(len(f.readlines()), 72)
        self.assertEqualFiles('expected/ruptures.csv', fname, lastline=20,
                              delta=1E-5)

        # run a regular event based on top of the UCERF ruptures and
        # check the generated hazard maps
        self.run_calc(ucerf.__file__, 'job.ini',
                      calculation_mode='event_based',
                      hazard_calculation_id=str(self.calc.datastore.calc_id))

        # check ucerf_hazard and event_based produces the same GMFs
        gmv_eb = view('global_gmfs', self.calc.datastore)
        self.assertEqual(gmv_uc, gmv_eb)

        # check the mean hazard map
        [fname] = [f for f in export(('hmaps', 'csv'), self.calc.datastore)
                   if 'mean' in f]
        self.assertEqualFiles('expected/hazard_map-mean.csv', fname,
                              delta=1E-5)

    def test_event_based_sampling(self):
        self.run_calc(ucerf.__file__, 'job_ebh.ini')

        # check the distribution of the events
        self.assertEventsByRlz([29, 25])

        # check the mean hazard map
        got = gettemp(view('hmap', self.calc.datastore))
        self.assertEqualFiles('expected/hmap.rst', got)

    def test_classical(self):
        ucerf_base.RUPTURES_PER_BLOCK = 50  # check splitting
        self.run_calc(ucerf.__file__, 'job_classical_redux.ini', exports='csv')
        ucerf_base.RUPTURES_PER_BLOCK = 1000  # resume default
        fnames = export(('hcurves/', 'csv'), self.calc.datastore)
        expected = ['hazard_curve-0-PGA.csv', 'hazard_curve-0-SA(0.1).csv',
                    'hazard_curve-1-PGA.csv', 'hazard_curve-1-SA(0.1).csv']
        for fname, exp in zip(fnames, expected):
            self.assertEqualFiles('expected/' + exp, fname)

        # make sure this runs
        view('fullreport', self.calc.datastore)

    def test_classical_time_dep(self):
        ucerf_base.RUPTURES_PER_BLOCK = 10  # check splitting
        out = self.run_calc(ucerf.__file__, 'job_classical_time_dep_redux.ini',
                            exports='csv')
        ucerf_base.RUPTURES_PER_BLOCK = 1000  # resume default
        fname = out['hcurves', 'csv'][0]
        self.assertEqualFiles('expected/hazard_curve-td-mean.csv', fname,
                              delta=1E-6)

        # make sure this runs
        view('fullreport', self.calc.datastore)

    def test_classical_time_dep_sampling(self):
        ucerf_base.RUPTURES_PER_BLOCK = 10  # check splitting
        out = self.run_calc(ucerf.__file__, 'job_classical_time_dep_redux.ini',
                            number_of_logic_tree_samples='2',
                            exports='csv')
        ucerf_base.RUPTURES_PER_BLOCK = 1000  # resume default
        fname = out['hcurves', 'csv'][0]
        self.assertEqualFiles('expected/hazard_curve-sampling.csv', fname,
                              delta=1E-6)

    def test_event_based_risk(self):
        # the fast calculator ucerf_risk
        raise unittest.SkipTest('ucerf_risk has been removed')
        self.run_calc(ucerf.__file__, 'job_ebr.ini')

        fname = gettemp(view('portfolio_loss', self.calc.datastore))
        self.assertEqualFiles('expected/portfolio_loss.txt', fname, delta=1E-5)

        # check the mean losses_by_period
        [fname] = export(('agg_curves-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/losses_by_period-mean.csv', fname)

    def test_event_based_risk_sampling(self):
        # the fast calculator ucerf_risk
        raise unittest.SkipTest('ucerf_risk has been removed')
        self.run_calc(ucerf.__file__, 'job_ebr.ini',
                      number_of_logic_tree_samples='2')

        # check the right number of events was stored
        self.assertEqual(len(self.calc.datastore['events']), 79)

        fname = gettemp(view('portfolio_loss', self.calc.datastore))
        self.assertEqualFiles(
            'expected/portfolio_loss2.txt', fname, delta=1E-5)

        # check the mean losses_by_period
        [fname] = export(('agg_curves-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/losses_by_period2-mean.csv', fname)

        # make sure this runs
        view('fullreport', self.calc.datastore)
