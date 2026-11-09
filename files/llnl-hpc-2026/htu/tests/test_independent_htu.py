"""Checks for the independent source comparison and honest failure reporting."""
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy.constants import e

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'beamline_impactx'))
from input_impactx import make_bunch, MASS_MEV
import ast
import json
notebook = json.loads((Path(__file__).resolve().parents[1] / 'htu_transport.ipynb').read_text())
for cell in notebook['cells']:
    if cell['cell_type'] == 'code':
        tree = ast.parse(''.join(cell['source']))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == 'analyze':
                exec(compile(ast.Module(body=[node], type_ignores=[]), '<notebook analysis>', 'exec'))


class IndependentHTUTest(unittest.TestCase):
    def test_energy_scan_preserves_geometry_angles_charge(self):
        beams = [make_bunch(energy) for energy in (100, 20)]
        slopes = []
        for beam, energy in zip(beams, (100,20)):
            gamma0=1+energy/MASS_MEV
            bg0=np.sqrt(gamma0**2-1)
            gamma=gamma0-beam['dpt']*bg0
            px=beam['dpx']*bg0
            py=beam['dpy']*bg0
            pz=np.sqrt(gamma**2-1-px**2-py**2)
            slopes.append((px/pz,py/pz))
            self.assertAlmostEqual(float(beam['w'].sum()*e/1e-12),80)
            self.assertAlmostEqual(float(((gamma-1)*MASS_MEV).mean()),energy)
        for key in ('dx','dy','dt','w'):
            np.testing.assert_array_equal(beams[0][key],beams[1][key])
        np.testing.assert_allclose(slopes[0],slopes[1],rtol=1e-12,atol=1e-15)

    def test_nonfinite_tracking_is_not_reported_as_transmission(self):
        with tempfile.TemporaryDirectory() as path:
            case=Path(path);(case/'diags').mkdir()
            np.savetxt(case/'diags/reduced_beam_characteristics.0',
                       [[0,-80e-12,1e-6,1e-6],[1,-40e-12,2e-6,2e-6],
                        [2,-40e-12,float('nan'),float('nan')]],
                       header='s charge_C sigma_x sigma_y',comments='')
            data,fraction,summary=analyze(case)
            self.assertIsNone(summary['final_transmission'])
            self.assertEqual(summary['first_nonfinite_s_m'],2)
            self.assertEqual(summary['last_valid_transmission'],0.5)
            self.assertEqual(len(data),2)

    def test_extinction_is_zero_transmission_not_invalid_tracking(self):
        with tempfile.TemporaryDirectory() as path:
            case=Path(path);(case/'diags').mkdir()
            np.savetxt(case/'diags/reduced_beam_characteristics.0',
                       [[0,-80e-12,1e-6,1e-6],[1,0,float('nan'),float('nan')]],
                       header='s charge_C sigma_x sigma_y',comments='')
            _,_,summary=analyze(case)
            self.assertEqual(summary['final_transmission'],0)
            self.assertIsNone(summary['first_nonfinite_s_m'])
            self.assertTrue(np.isfinite(summary['max_rms_size_m']))


if __name__=='__main__':
    unittest.main()
