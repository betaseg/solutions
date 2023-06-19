from album.runner.api import setup


def create_mesh_and_save(data, file_name):
    import numpy as np
    from stl import mesh
    import vtk

    from vtkplotlib.image_io import vtkimagedata_from_array
    image3D = vtk.vtkImageAppend()
    image3D.SetAppendAxis(2)
    data = data.astype(np.uint8)
    for i in range(data.shape[2]):
        image_data = vtkimagedata_from_array(data[:,:,i])
        image3D.AddInputData(image_data)

    image3D.Update()

    discrete = vtk.vtkFlyingEdges3D()
    discrete.SetInputData(image3D.GetOutput())
    discrete.GenerateValues(1, 1, 1)
    discrete.Update()

    smoothing_iterations = 10
    pass_band = 0.001
    feature_angle = 120.0

    smoother = vtk.vtkWindowedSincPolyDataFilter()
    smoother.SetInputConnection(discrete.GetOutputPort())
    smoother.SetNumberOfIterations(smoothing_iterations)
    smoother.BoundarySmoothingOn()
    smoother.FeatureEdgeSmoothingOn()
    smoother.SetFeatureAngle(feature_angle)
    smoother.SetPassBand(pass_band)
    smoother.NonManifoldSmoothingOn()
    smoother.NormalizeCoordinatesOn()
    smoother.Update()

    decimate = vtk.vtkDecimatePro()
    decimate.SetInputData(smoother.GetOutput())
    decimate.SetTargetReduction(0.5)
    decimate.PreserveTopologyOn()
    decimate.Update()
    #
    # decimated = vtk.vtkPolyData()
    # decimated.ShallowCopy(decimate.GetOutput())

    # tt('After decimation')
    # print(f'There are {decimated.GetNumberOfPoints()} points.')
    # print(f'There are {decimated.GetNumberOfPolys()} polygons.')
    # print(
    #     f'Reduction: {(shape.GetNumberOfPolys() - decimated.GetNumberOfPolys()) / shape.GetNumberOfPolys()}')

    if file_name:
        # decimated.save(file_name)
        writer = vtk.vtkSTLWriter()
        writer.SetInputData(decimate.GetOutput())
        writer.SetFileTypeToBinary()
        writer.SetFileName(file_name)
        writer.Write()
    # return PolyData(discrete.GetOutput())
    return mesh.Mesh.from_file(file_name)


def run():
    from album.runner.api import get_args
    import vtkplotlib as vpl
    from pathlib import Path
    import z5py

    project = Path(get_args().project)
    headless = get_args().headless
    include = None
    exclude = None
    if get_args().include:
        include = get_args().include.split(",")
    if get_args().exclude:
        exclude = get_args().exclude.split(",")
    output_path = project.joinpath("export", "meshes")
    output_path.mkdir(exist_ok=True, parents=True)
    project_file = z5py.File(str(project))
    project_name = Path(project).name.rstrip(".n5")
    masks = project_file.attrs['masks']
    labelmaps = project_file.attrs['labelmaps']
    filaments = project_file.attrs['filaments']
    meshes = []
    print(headless)
    breakpoint()
    for mask in masks:
        if mask == "membrane border":
            continue
        mesh = import_dataset(include, exclude, project_file, output_path, masks[mask])
        if not headless:
            meshes.append(mesh)
    for labelmap in labelmaps:
        mesh = import_dataset(include, exclude, project_file, output_path, labelmaps[labelmap])
        if not headless:
            meshes.append(mesh)
    for filament in filaments:
        mesh = import_dataset(include, exclude, project_file, output_path, filaments[filament])
        if not headless:
            meshes.append(mesh)
    if 'cellbounds' in project_file.attrs:
        cellbound_volume = project_file.attrs['cellbounds']
        if not cellbound_volume.startswith(project_name):
            cellbound_volume = project_name + "_" + cellbound_volume
        mesh = import_dataset(include, exclude, project_file, output_path, cellbound_volume)
        if not headless:
            meshes.append(mesh)
    if meshes and not headless:
        figure = vpl.figure()
        figure.render_size = (800, 600)
        for mesh, color in meshes:
            if mesh:
                # mesh.to_plot()
                if color == 0:
                    vpl.mesh_plot(mesh, color=[255, 255, 255, 255])
                else:
                    vpl.mesh_plot(mesh, color=[red(color), green(color), blue(color), alpha(color)])
        vpl.show()


def red(value):
    return (value >> 16) & 0xff


def green(value):
    return (value >> 8) & 0xff


def blue(value):
    return value & 0xff


def alpha(value):
    return (value >> 24) & 0xff


def import_dataset(include, exclude, project, output_path, item):
    import numpy as np
    import os
    import json
    if include:
        if not any(_include in str(item) for _include in include):
            return None, None
    if exclude:
        if any(_exclude in str(item) for _exclude in exclude):
            return None, None
    item = item.lstrip(os.sep)
    print("Loading dataset from %s.." % item)
    project_item = project[item]
    data = np.array(project_item)
    data = data > 0
    output_path_mesh = output_path.joinpath(item + ".stl")
    print("Exporting mesh to %s.." % output_path_mesh)
    mesh = create_mesh_and_save(data, output_path_mesh)
    try:
        color = project_item.attrs['color']
    except:
        # no color given
        color = None

    if color is not None:
        # hack to save color, should be done by storing it with the mesh (i.e. as OBJ)
        output_color_path = output_path.joinpath(item + "_attrs.json")
        with open(output_color_path, "w") as outfile:
            outfile.write(json.dumps({"color": color}, indent=4))
    return mesh, color


env_file = """channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.9
  - numpy=1.21.2
  - scikit-image=0.18.3
  - numpy-stl=3.0.0
  - z5py=2.0.16
  - vtk=9.2.5
  - pip
  - pip:
    - vtkplotlib==1.4.1
"""

setup(
    group="io.github.betaseg",
    name="cellsketch-mesh-export",
    version="0.1.0",
    album_api_version="0.5.5",
    title="CellSketch: Export masks and labelmaps as meshes",
    description="VTK based mesh generation from pixel data, exports all masks and labelmaps from CellSketch project as meshes.",
    solution_creators=['Deborah Schmidt'],
    run=run,
    args=[{
        "name": "project",
        "type": "directory",
        "description": "The CellSketch project (ends with .n5)",
        "required": True
    }, {
        "name": "include",
        "type": "string",
        "description": "List of names of elements which should be loaded, comma separated",
        "required": False
    }, {
        "name": "exclude",
        "type": "string",
        "description": "List of names of elements which should not be loaded, comma separated",
        "required": False
    }, {
        "name": "headless",
        "type": "boolean",
        "description": "Do not display mesh after processing it. Set this to true if you run into memory issues.",
        # "default": False,
    }],
    covers=[{
        "description": "Screenshot of a raw image next to the mesh generated from it and displayed using vtkplotlib.",
        "source": "cover.png"
    }],
    dependencies={'environment_file': env_file}
)
