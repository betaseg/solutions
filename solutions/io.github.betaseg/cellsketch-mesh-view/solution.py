from album.runner.api import setup


def run():
    from album.runner.api import get_args
    import vtkplotlib as vpl
    from pathlib import Path
    import z5py

    project = Path(get_args().project)
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
    masks = project_file.attrs['masks'] if 'masks' in project_file.attrs else []
    labelmaps = project_file.attrs['labelmaps'] if 'labelmaps' in project_file.attrs else []
    filaments = project_file.attrs['filaments'] if 'filaments' in project_file.attrs else []
    cellbounds = project_file.attrs['cellbounds'] if 'cellbounds' in project_file.attrs else []
    meshes = []
    for mask in masks:
        if mask == "membrane border":
            continue
        meshes.append(import_dataset(include, exclude, project_file, output_path, masks[mask]))
    for labelmap in labelmaps:
        meshes.append(
            import_dataset(include, exclude, project_file, output_path, labelmaps[labelmap]))
    for filament in filaments:
        meshes.append(import_dataset(include, exclude, project_file, output_path, filaments[filament]))
    for cellbound in cellbounds:
        meshes.append(import_dataset(include, exclude, project_file, output_path, cellbounds[cellbound]))

    if meshes:
        figure = vpl.figure()
        figure.render_size = (800, 600)
        for mesh, color in meshes:
            if mesh:
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
    import os
    from stl import mesh
    if include:
        if not any(_include in str(item) for _include in include):
            return None, None
    if exclude:
        if any(_exclude in str(item) for _exclude in exclude):
            return None, None
    item = item.lstrip(os.sep)
    print("Loading dataset from %s.." % item)
    project_item = project[item]
    output_path = output_path.joinpath(item + ".stl")
    if not output_path.exists():
        return None, None
    print("Loading mesh from %s.." % output_path)
    mesh = mesh.Mesh.from_file(output_path)
    try:
        color = project_item.attrs['color']
        return mesh, color
    except:
        # no color given
        return None, mesh

setup(
    group="io.github.betaseg",
    name="cellsketch-mesh-view",
    version="0.1.0",
    album_api_version="0.5.3",
    title="CellSketch: Display exported meshes",
    description="Displays all exported meshes from a CellSketch project using vtkplotlib. Colors can be adjusted in the CellSketch BigDataViewer app.",
    solution_creators=['Deborah Schmidt'],
    tags=["mesh", "cellsketch"],
    cite=[{
        "text": "Schroeder, W.; Martin, K.; Lorensen, B. (2006). The Visualization Toolkit (4th ed.), Kitware, ISBN 978-1-930934-19-1",
        "url": "https://vtk.org/"
    },{
        "text": "Pape, C. (2019). constantinpape/z5",
        "doi": "10.5281/ZENODO.3585752"
    }],
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
    }],
    covers=[{
        "description": "Screenshot of a raw image next to the mesh generated from it and displayed using vtkplotlib.",
        "source": "cover.png"
    }],
    dependencies={'parent': {'resolve_solution': 'io.github.betaseg:cellsketch-mesh-export:0.1.0'}}
)
