# Runs main.ipynb's deformation cells (2, 3, 4, 7, 11) headless on pi 3mm and saves the undeformed and
# deformed tet meshes to <work>/out/*.vtu for render_slice_unwarp.py.
# Usage: run on a COPY of the repo folder (cell 11 overwrites output_models/):
#   xvfb-run -a python Notes/scripts/run_s4_headless.py <copy-of-repo>
import json, os, sys
work = sys.argv[1]
os.chdir(work)
for d in ['input_models','input_gcode','output_models','output_gcode','pickle_files','gifs']:
    os.makedirs(d, exist_ok=True)
import pyvista as pv
pv.OFF_SCREEN = True
pv.DataSet.plot = lambda self, *a, **k: None          # skip interactive plots
nb = json.load(open('main.ipynb', encoding='utf-8'))
src = lambda i: ''.join(nb['cells'][i]['source'])
ns = {}
for i in [2, 3, 4, 7, 11]:
    code = src(i)
    code = code.replace("INTERACTIVE_PLOTS = True", "INTERACTIVE_PLOTS = False")
    code = code.replace("pv.set_jupyter_backend('static')", "pass")
    code = code.replace("SAVE_GIF = True", "SAVE_GIF = False")
    code = code.replace("verbose=2", "verbose=0")
    print(f"--- running cell {i}", flush=True)
    exec(compile(code, f"cell{i}", "exec"), ns)
inp, dfm = ns['input_tet'], ns['deformed_tet']
print("tets:", inp.number_of_cells, "points:", inp.number_of_points, "deformed bounds:", dfm.bounds)
out = os.path.join(work, 'out')
g_in = pv.UnstructuredGrid({pv.CellType.TETRA: inp.cells.reshape(-1,5)[:,1:]}, inp.points.copy())
g_df = pv.UnstructuredGrid({pv.CellType.TETRA: dfm.cells.reshape(-1,5)[:,1:]}, dfm.points.copy())
g_df.cell_data['rotation_field'] = ns['rotation_field']
g_in.save(os.path.join(out, 'input_tet.vtu')); g_df.save(os.path.join(out, 'deformed_tet.vtu'))
print("saved")
