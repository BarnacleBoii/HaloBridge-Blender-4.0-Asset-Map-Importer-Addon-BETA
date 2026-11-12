"""Original Halo 3 vehicle references, kept out of static level geometry."""
import math
import re
from pathlib import Path
from mathutils import Matrix,Vector
from . import blender_ops
from .diagnostics import ValidationError
from .catalog import read_json

def selected_vehicle(obj):return bool(obj and obj.type=='MESH' and obj.get('hb_vehicle_tag'))

def validate_preview(obj):
    if not obj.get('hb_source_tag') or not obj.get('hb_mesh_signature'):
        raise ValueError('This object has no verified original model identity. Place its model from the Indexed Asset List first.')
    if obj.modifiers:raise ValueError('Remove modifiers before using an original vehicle tag; mesh edits cannot be applied to the original vehicle.')
    if blender_ops.mesh_signature(obj.data)==obj.get('hb_mesh_signature'):return Vector((0,0,0))
    # An origin change translates local vertices but does not reshape the model.
    # Recover that offset from the original cached preview, never from a guess.
    data=read_json(Path(obj.get('hb_cache',''))/'preview.json',{}) if obj.get('hb_cache') else {}
    positions=[];faces=[]
    for mesh in data.get('meshes',[]):
        start=len(positions);positions.extend(mesh['positions'])
        for segment in mesh['segments']:
            faces.extend(tuple(start+v for v in segment['indices'][i:i+3]) for i in range(0,len(segment['indices']),3))
    if positions and len(positions)==len(obj.data.vertices) and len(faces)==len(obj.data.polygons):
        offset=Vector(positions[0])-obj.data.vertices[0].co
        if all((Vector(p)-v.co-offset).length<1e-5 for p,v in zip(positions,obj.data.vertices)) and all(tuple(p.vertices)==f for p,f in zip(obj.data.polygons,faces)):
            return offset
    raise ValueError('This preview mesh was edited. Reimport the original model before using a vehicle tag; mesh edits cannot be applied to the original vehicle.')

def plan(scene,config):
    placements=[];issues=[];ids=set()
    for obj in scene.objects:
        if not selected_vehicle(obj) or obj.get('hb_preview') or (obj.get('hb_ignore') and not obj.get('hb_map_reference')):continue
        try:
            if obj.get('hb_game','halo3')!=config.get('game','halo3'):raise ValueError('Original vehicle placement requires assets from the Sapien destination game; use the static mesh instead.')
            origin_offset=validate_preview(obj)
            tag=obj['hb_vehicle_tag'];root=Path(config['kit'])/'tags';path=root/(tag+'.vehicle')
            if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():raise ValueError('Original vehicle tag is missing: '+tag)
            if obj.get('hb_vehicle_render')!=obj.get('hb_source_tag'):raise ValueError('The model identity changed. Find matching vehicles again.')
            units=float(obj.get('hb_working_units',100));loc,rot,scale=obj.matrix_world.decompose()
            if not math.isfinite(units) or units<=0:raise ValueError('Invalid working scale.')
            if any(not math.isfinite(v) for row in obj.matrix_world for v in row):raise ValueError('Invalid transform.')
            # Tolerances are relative: at 100x working scale float32 rounding alone is ~1e-5.
            if min(scale)<=0 or max(scale)-min(scale)>1e-4*max(scale):raise ValueError('Original vehicles require positive uniform scale.')
            matrix=Matrix.LocRotScale(loc,rot,scale)
            if max(abs(matrix[r][c]-obj.matrix_world[r][c]) for r in range(4) for c in range(4))>1e-5*max(1.0,max(scale)):raise ValueError('Remove transform shear before placing this vehicle.')
            identity=obj.get('hb_vehicle_id','')
            if not re.fullmatch(r'hb_[0-9a-f]{24}',identity) or identity in ids:
                identity=blender_ops.new_id();obj['hb_vehicle_id']=identity
            # Halo yaw/pitch/roll is Blender 'ZYX' order (see source_formats.euler_matrix).
            ids.add(identity);euler=rot.to_euler('ZYX')
            loc=(obj.matrix_world@Matrix.Translation(-origin_offset)).translation
            placements.append(dict(id=identity,tag=tag,position=list(loc/units),rotation=[math.degrees(euler.z),-math.degrees(euler.y),math.degrees(euler.x)],scale=float(scale.x)/units))
        except (ValueError,TypeError) as error:issues.append(obj.name+': '+str(error))
    if issues:raise ValidationError(issues,'Original vehicle validation')
    return placements
