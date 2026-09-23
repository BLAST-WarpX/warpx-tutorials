#!/usr/bin/env python3
"""
Analysis helpers for the LLNL ImpactX notebook.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import openpmd_api as io
from scipy.constants import c, e, m_e
from impactx import RefPart, elements

from htu_lattice import get_lattice

# ImpactX notebook analysis
COLORS = ("#087e8b", "#d1495b", "#7656a5", "#dd8b16")


def measurements(run):
    return json.loads((Path(run) / "performance.json").read_text())


def analyze(case):
    files = sorted((case / "diags").glob("reduced_beam_characteristics.*"))
    if not files:
        raise RuntimeError(f"No beam diagnostics in {case}")
    data = np.genfromtxt(files[0], names=True)
    data = np.atleast_1d(data)
    # Beam moments can be undefined after all particles are lost. Never call
    # nonfinite moments a measurement of loss; use the charge diagnostic.
    charge = np.abs(data["charge_C"])
    if not np.all(np.isfinite(charge)):
        raise RuntimeError(f"Nonfinite charge diagnostic in {case}")
    if charge[0] <= 0:
        raise RuntimeError(f"No initial beam charge in {case}")
    fraction = charge / charge[0]
    active = fraction > 0
    finite = np.isfinite(data["sigma_x"]) & np.isfinite(data["sigma_y"])
    bad = np.flatnonzero(active & ~finite)
    stop = int(bad[0]) if len(bad) else len(data)
    # Once the tracking map is invalid, its remaining-particle count is not
    # a trustworthy transmission prediction. Plot only the valid prefix.
    summary = dict(
        final_transmission=(None if len(bad) else float(fraction[-1])),
        first_nonfinite_s_m=(float(data["s"][stop]) if len(bad) else None),
        last_valid_transmission=float(fraction[max(0, stop - 1)]),
        max_rms_size_m=float(
            max(
                np.max(data["sigma_x"][:stop][(active & finite)[:stop]], initial=0),
                np.max(data["sigma_y"][:stop][(active & finite)[:stop]], initial=0),
            )
        ),
    )
    data = data[:stop]
    fraction = fraction[:stop]
    return data, fraction, summary


def screens(case):
    """Read all saved transverse snapshots in beamline order, including exit."""
    _, _, summary = analyze(case)
    cutoff = summary['first_nonfinite_s_m']
    result = []
    for path in sorted((case / 'diags/openPMD').glob('*.h5')):
        series = io.Series(str(path), io.Access.read_only)
        try:
            for iteration in series.iterations:
                beam = series.iterations[iteration].particles['beam']
                s = float(beam.get_attribute('s_ref'))
                if cutoff is not None and s >= cutoff:
                    continue
                frame = beam.to_df()
                values = frame[['position_x', 'position_y', 'weighting']].to_numpy()
                if not np.all(np.isfinite(values)):
                    raise ValueError(f'Invalid tracking at {path.name}; no snapshot shown.')
                name = path.stem
                if name == 'monitor':
                    name = 'Source' if iteration == min(series.iterations) else 'Exit'
                result.append(dict(name=name, s=s, values=values))
        finally:
            series.close()
    return sorted(result, key=lambda item: item['s'])


def histogram(values, limit=None):
    """Full-beam charge map: no percentile cuts or discarded halo particles."""
    if not np.all(np.isfinite(values)):
        raise ValueError('Cannot histogram nonfinite particle coordinates or weights.')
    xy = values[:, :2] * 1e3  # mm throughout; viewer formats small scales as µm.
    if limit is None:
        limit = max(np.max(np.abs(xy), initial=0) * 1.03, 1e-6)
    hist, _, _ = np.histogram2d(*xy.T, bins=48,
        range=[[-limit, limit]] * 2, weights=values[:, 2] * e * 1e12)
    return hist.T, float(limit)


def beam_explorer(run):
    """Create and save a standalone, offline slider/play viewer."""
    import html
    from IPython.display import IFrame
    cases = []
    for record in measurements(run):
        energy = record['total_energy_MeV']
        case = Path(run) / f'{energy:g}MeV'
        snapshots = screens(case)
        _, _, summary = analyze(case)
        if not snapshots:
            raise RuntimeError(f'No valid saved screens in {case}')
        common = max(histogram(snap['values'])[1] for snap in snapshots)
        frames = []
        for snap in snapshots:
            hist, limit = histogram(snap['values'])
            fixed, _ = histogram(snap['values'], common)
            frames.append(dict(name=snap['name'], s=snap['s'], limit=limit,
                hist=hist.tolist(), fixed=fixed.tolist(),
                charge=float(snap['values'][:, 2].sum()*e*1e12)))
        cases.append(dict(energy=energy, frames=frames, common=common,
            invalid_at=summary['first_nonfinite_s_m']))
    positive = [v for case in cases for frame in case['frames']
                for mode in ('hist', 'fixed') for row in frame[mode] for v in row if v > 0]
    low, high = (min(positive), max(positive)) if positive else (.001, 1.)
    high = max(high, low*10)
    palette = (plt.get_cmap('magma')(np.linspace(0, 1, 256))[:, :3]*255).astype(int).tolist()
    payload = dict(cases=cases, low=low, high=high, palette=palette)
    document = BEAM_EXPLORER_HTML.replace('__BEAM_DATA__', json.dumps(payload, allow_nan=False))
    (Path(run)/'beam_explorer.html').write_text(document)
    return IFrame('about:blank', width='100%', height=660, extras=[
        'title="HTU beam explorer"', 'sandbox="allow-scripts"',
        'srcdoc="'+html.escape(document, quote=True)+'"'])


def plot_lattice(ax, total_energy_MeV):
    """Draw the HTU lattice with ImpactX's survey and an electron reference."""
    mass_MeV = m_e * c**2 / e / 1e6
    ref = RefPart()
    ref.set_charge_qe(-1.0).set_mass_MeV(mass_MeV).set_kin_energy_MeV(
        total_energy_MeV - mass_MeV
    )
    lattice = elements.KnownElementsList()
    lattice.extend(get_lattice("impactx"))
    lattice.plot_survey(ref=ref, ax=ax)
    ax.set_box_aspect(None)  # Keep the survey aligned with the shared beam-size axis.


def plot_beam_sizes(run):
    """Show focusing in both planes and screen landmarks; preserve validity checks."""
    fig, (ax, lattice_ax) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True,
        gridspec_kw={'height_ratios': [4, 1]}, constrained_layout=True)
    records = measurements(run)
    plot_lattice(lattice_ax, records[0]["total_energy_MeV"])
    summaries = {}
    for i, record in enumerate(records):
        energy = record['total_energy_MeV']
        case = Path(run)/f'{energy:g}MeV'
        data, fraction, summary = analyze(case)
        summaries[f'{energy:g} MeV'] = summary
        for j, plane in enumerate(('x', 'y')):
            sizes = np.where(fraction > 0, data[f'sigma_{plane}']*1e3, np.nan)
            ax.plot(data['s'], sizes, color=COLORS[(2*i+j)%len(COLORS)],
                    ls='-' if j == 0 else '--', lw=2.5, label=f'{energy:g} MeV · {plane}')
        if summary['first_nonfinite_s_m'] is not None:
            ax.axvline(summary['first_nonfinite_s_m'], color='red', ls=':')
            ax.text(.02, .05, 'Tracking invalid: curves stop at the last valid sample.',
                    transform=ax.transAxes, color='red')
        if i == 0:
            for snap in screens(case):
                if snap['name'] in ('TCPhosphor', 'ChicaneSlit', 'UC_VisaEBeam1'):
                    ax.axvline(snap['s'], color='#9aa9b5', lw=1, alpha=.5)
                    label = {'TCPhosphor':'After focusing', 'ChicaneSlit':'Mid-chicane',
                             'UC_VisaEBeam1':'Undulator screens'}[snap['name']]
                    ax.text(snap['s'], 1.02, label, transform=ax.get_xaxis_transform(),
                            fontsize=9, ha='center')
    ax.set(yscale='log', ylabel='Rms beam size (mm)', title='Focusing and expansion along HTU\n')
    ax.grid(alpha=.18); ax.legend(loc='best', ncol=2)
    (Path(run)/'summary.json').write_text(json.dumps(summaries, indent=2)+'\n')
    fig.savefig(Path(run)/'beam_sizes.png', dpi=160)
    for label, summary in summaries.items():
        fraction = summary['final_transmission']
        print(f"{label}: remaining charge = {100*fraction:.1f}%" if fraction is not None
              else f'{label}: invalid tracking; transmission is not a prediction.')
    print('No apertures are modeled: remaining charge does not tell us whether a real beam fits.')
    plt.show()
    return fig


# Offline viewer template
BEAM_EXPLORER_HTML = r'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HTU beam explorer</title>
<style>
body{margin:0;background:#101627;color:#edf3fa;font:15px system-ui,sans-serif;padding:20px;box-sizing:border-box}h2{margin:0 0 5px}p{color:#bdc9db;margin:8px 0}button,select{font:inherit;padding:7px 12px;border-radius:8px;border:1px solid #75849d;background:#202d45;color:white}button{cursor:pointer}label{display:inline-block;margin:8px 16px 8px 0}input[type=range]{width:100%;accent-color:#ffc36b}canvas{max-width:100%;display:block;margin:auto} .view{display:flex;gap:24px;align-items:center;justify-content:center}.stats{max-width:260px}.badge{color:#ffd18b;font-size:24px;font-weight:bold}#route{height:8px;background:#33435c;border-radius:8px;margin:12px 0}#progress{height:100%;background:#ffc36b;border-radius:8px}.small{font-size:12px}#warning{color:#ffb9bf} @media(max-width:600px){.view{gap:8px}.stats{max-width:160px}body{padding:10px}}
</style>
<h2>HTU beam explorer</h2><p>Follow the bunch through saved HTU screens. Where does it focus, and where does it expand?</p>
<label>Beam <select id="energy" aria-label="Beam energy"></select></label>
<label><input id="fit" type="checkbox" checked> Zoom to fit each screen</label>
<div class="view"><canvas id="beam" width="390" height="360" aria-label="Transverse charge map"></canvas>
<div class="stats"><div id="name" class="badge"></div><p id="position"></p><p id="charge"></p><p id="scale"></p>
<p class="small">Color: charge per bin (pC), logarithmic scale. Bin area changes when zooming; color alone does not compare charge per unit area.</p>
<canvas id="legend" width="240" height="45" aria-label="Charge color scale"></canvas><p id="warning"></p></div></div>
<div id="route"><div id="progress"></div></div>
<label><button id="play" type="button">▶ Play screens</button> <span id="step"></span></label>
<input id="slider" aria-label="Saved screen" type="range" min="0" value="0" step="1">
<p class="small">Snapshots in beamline order, not a movie in physical time. All particles are included. No apertures or collective fields are modeled. Uncheck zoom to compare beam sizes on the same axes.</p>
<script>
const data=__BEAM_DATA__;
const $=id=>document.getElementById(id), canvas=$('beam'), ctx=canvas.getContext('2d');
let timer=null;
for(const c of data.cases){const o=document.createElement('option');o.textContent=c.energy+' MeV';$('energy').append(o);}
function color(v){if(v<=0)return '#100d22';const t=Math.max(0,Math.min(1,Math.log(v/data.low)/Math.log(data.high/data.low)));return 'rgb('+data.palette[Math.round(t*255)].join(',')+')';}
function draw(){
 const c=data.cases[$('energy').selectedIndex], i=Number($('slider').value), f=c.frames[i], fit=$('fit').checked;
 const h=fit?f.hist:f.fixed, limit=fit?f.limit:c.common;
 ctx.clearRect(0,0,390,360);const left=57,top=10,size=292;
 ctx.fillStyle='#100d22';ctx.fillRect(left,top,size,size);
 for(let y=0;y<48;y++)for(let x=0;x<48;x++){ctx.fillStyle=color(h[y][x]);ctx.fillRect(left+x*size/48,top+(47-y)*size/48,size/48+.3,size/48+.3);}
 ctx.strokeStyle='#a5b6cd';ctx.strokeRect(left,top,size,size);ctx.fillStyle='#edf3fa';ctx.font='12px system-ui';
 const unit=limit<.1?'µm':'mm', factor=limit<.1?1000:1, extent=(limit*factor).toPrecision(3);
 ctx.textAlign='center';ctx.fillText('-'+extent,left,321);ctx.fillText('0',left+size/2,321);ctx.fillText(extent,left+size,321);ctx.fillText('x ('+unit+')',left+size/2,348);
 ctx.textAlign='right';ctx.fillText(extent,left-5,18);ctx.fillText('0',left-5,top+size/2);ctx.fillText('-'+extent,left-5,top+size);
 ctx.save();ctx.translate(12,top+size/2);ctx.rotate(-Math.PI/2);ctx.textAlign='center';ctx.fillText('y ('+unit+')',0,0);ctx.restore();
 $('name').textContent=f.name;$('position').textContent='s = '+f.s.toFixed(3)+' m';$('charge').textContent=f.charge.toFixed(2)+' pC on this screen';
 $('scale').textContent=(fit?'Zoom to fit':'Fixed axes')+' · ±'+extent+' '+unit;
 $('step').textContent='Screen '+(i+1)+' / '+c.frames.length;
 $('progress').style.width=100*(f.s-c.frames[0].s)/Math.max(c.frames.at(-1).s-c.frames[0].s,1e-12)+'%';
 $('warning').textContent=c.invalid_at===null?'':'Tracking becomes invalid at s = '+c.invalid_at.toFixed(3)+' m. Later screens are excluded.';
}
function stop(){clearInterval(timer);timer=null;$('play').textContent='▶ Play screens';}
function reset(){stop();$('slider').max=data.cases[$('energy').selectedIndex].frames.length-1;$('slider').value=0;draw();}
$('energy').onchange=reset;$('fit').onchange=draw;$('slider').oninput=()=>{stop();draw();};
$('play').onclick=()=>{if(timer){stop();return;}if(Number($('slider').value)===Number($('slider').max))$('slider').value=0;$('play').textContent='⏸ Pause';draw();timer=setInterval(()=>{const next=Number($('slider').value)+1;if(next>Number($('slider').max)){stop();return;}$('slider').value=next;draw();},650);};
const legend=$('legend').getContext('2d');for(let x=0;x<240;x++){legend.fillStyle=color(data.low*Math.pow(data.high/data.low,x/239));legend.fillRect(x,0,1,16);}legend.fillStyle='#edf3fa';legend.font='12px system-ui';legend.fillText(data.low.toPrecision(2),0,34);legend.textAlign='right';legend.fillText(data.high.toPrecision(2)+' pC',240,34);
reset();
</script></html>
'''
