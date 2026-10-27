# Renders Notes/pi 3mm_slice_flat.gif (stage 6: slice the deformed part flat) and Notes/pi 3mm_unwarp.gif
# (stage 7: un-warp the flat layers into curved layers). Outer walls only, 0.6 mm layers; the un-warp uses the
# same linear-in-tet (barycentric) map as S4. Run run_s4_headless.py first.
# Usage: xvfb-run -a python Notes/scripts/render_slice_unwarp.py <copy-of-repo> <output-folder>
import sys, os, numpy as np, pyvista as pv
pv.OFF_SCREEN = True
work, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
inp = pv.read(os.path.join(work, 'out', 'input_tet.vtu'))
dfm = pv.read(os.path.join(work, 'out', 'deformed_tet.vtu'))
assert inp.n_points == dfm.n_points
dfm.point_data['orig'] = inp.points.copy()
surf = dfm.extract_surface(algorithm='dataset_surface')      # boundary of the deformed part, carries original coords

LAYER = 0.6
zmax = dfm.bounds[5]
zs = np.arange(LAYER / 2, zmax, LAYER)
layers = []
for k, z in enumerate(zs):
    c = surf.slice(normal='z', origin=(0, 0, z))
    if c.n_points == 0:
        continue
    c.point_data['layer'] = np.full(c.n_points, float(k))
    layers.append(c)
lines = layers[0].merge(layers[1:], merge_points=False)
nL = len(zs)
print('layers', nL, 'points', lines.n_points)

lines_def = lines.points.copy(); lines_org = lines.point_data['orig'].copy()
surf_def = surf.points.copy();   surf_org = surf.point_data['orig'].copy()
layer_of_pt = lines.point_data['layer']

W, H = 1024, 768
CAM = [(-47.7, -70.8, 47.3), (0.0, 0.0, 11.5), (0.0, 0.0, 1.0)]
PART = '#8E9AA3'
CMAP = 'viridis'

def new_plotter():
    p = pv.Plotter(off_screen=True, window_size=[W, H])
    p.set_background('white')
    p.enable_anti_aliasing('ssaa')
    return p

# ---------- Stage 6: slice the deformed part with flat layers ----------
p = new_plotter()
p.open_gif(os.path.join(outdir, 'pi 3mm_slice_flat.gif'), fps=14)
part6 = surf.copy(); part6.points = surf_def
p.add_mesh(part6, color=PART, opacity=0.22, smooth_shading=True)
p.camera_position = CAM
plane_actor = None; line_actor = None
for k in list(range(nL)) + [nL - 1] * 20:
    if plane_actor is not None: p.remove_actor(plane_actor)
    if line_actor is not None: p.remove_actor(line_actor)
    shown = lines.extract_points(layer_of_pt <= k, adjacent_cells=False, include_cells=True)
    if shown.n_points:
        line_actor = p.add_mesh(shown, scalars='layer', cmap=CMAP, clim=[0, nL - 1], line_width=5,
                                render_lines_as_tubes=True, show_scalar_bar=False)
    if k < nL - 1 or True:
        plane = pv.Plane(center=(0, 0, zs[min(k, nL - 1)]), direction=(0, 0, 1), i_size=62, j_size=24)
        plane_actor = p.add_mesh(plane, color='#5B8DB8', opacity=0.18 if k < nL - 1 else 0.0)
    p.camera_position = CAM
    p.write_frame()
p.screenshot(os.path.join(outdir, 'pi 3mm_slice_flat.png'))
p.close()

# ---------- Stage 7: un-warp the flat layers back into the real part ----------
def ease(s): return s * s * (3 - 2 * s)
p = new_plotter()
p.open_gif(os.path.join(outdir, 'pi 3mm_unwarp.gif'), fps=14)
part7 = surf.copy(); lines7 = lines.copy()
pa = p.add_mesh(part7, color=PART, opacity=0.22, smooth_shading=True)
la = p.add_mesh(lines7, scalars='layer', cmap=CMAP, clim=[0, nL - 1], line_width=5,
                render_lines_as_tubes=True, show_scalar_bar=False)
p.camera_position = CAM
schedule = [0.0] * 12 + [ease(i / 44) for i in range(45)] + [1.0] * 28
for s in schedule:
    part7.points = (1 - s) * surf_def + s * surf_org
    lines7.points = (1 - s) * lines_def + s * lines_org
    p.camera_position = CAM
    p.render()
    p.write_frame()
p.screenshot(os.path.join(outdir, 'pi 3mm_unwarp.png'))
p.close()
print('done')
