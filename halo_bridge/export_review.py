"""Read-only, per-object export validation; no scene objects are deleted."""
from pathlib import Path
import math
import bpy
from . import cross_game

def shader_file(kit,tag):
    tag=tag.replace('/','\\')
    root=Path(kit)/'tags';p=root/tag
    if not tag or '..' in tag.split('\\') or not p.resolve().is_relative_to(root.resolve()):
        raise ValueError('No existing Halo shader is assigned. Apply a HaloBridge material to the object, not just select it in the Asset List.')
    regular=p.with_suffix('.shader')
    matches=[regular] if regular.is_file() else [f for f in p.parent.glob(p.name+'.shader*') if f.is_file()]
    if len(matches)!=1:raise ValueError('Missing or ambiguous Halo shader: '+tag)
    return matches[0]

def inspect(objects,config):
    issues={};used={};reach={};depsgraph=bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        errors=[];evaluated=obj.evaluated_get(depsgraph);mesh=None
        try:
            units=float(obj.get('hb_working_units',bpy.context.scene.get('hb_working_units',100)))
            if not math.isfinite(units) or units<=0:raise ValueError('Working scale must be finite and positive.')
            if any(not math.isfinite(v) for row in obj.matrix_world for v in row):raise ValueError('Object transform contains non-finite values.')
            if abs(obj.matrix_world.to_3x3().determinant())<1e-12:raise ValueError('Object has zero scale.')
            mesh=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=depsgraph)
            if not mesh.polygons:raise ValueError('No mesh faces remain after modifiers.')
            if any(not math.isfinite(x) for v in mesh.vertices for x in v.co):raise ValueError('Mesh contains non-finite coordinates.')
            slots=sorted({p.material_index for p in mesh.polygons})
            mats=[]
            for index in slots:
                mat=mesh.materials[index] if index<len(mesh.materials) else None
                if mat is None:
                    errors.append('Faces use an empty material slot. Assign a HaloBridge material.');continue
                # Evaluated materials retain their source ID where available.
                mat=getattr(mat,'original',mat);mats.append(mat)
                if mat.name.startswith('+'):continue
                try:
                    is_reach=mat.get('hb_shader_game')!='halo3' and (obj.get('hb_game')=='reach' or mat.get('hb_game')=='reach')
                    if is_reach:
                        bsdf=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if mat.use_nodes else None
                        if bsdf is None:raise ValueError('No supported Principled preview material.')
                        for socket in ('Base Color','Normal','Alpha'):
                            source=cross_game.texture(bsdf.inputs[socket])
                            if source and not all(source[0].size):raise ValueError('Missing texture: '+source[0].filepath)
                        reach[mat.as_pointer()]=mat
                    else:shader_file(config['kit'],mat.get('hb_shader',''))
                except (ValueError,RuntimeError) as e:errors.append(mat.name+': '+str(e))
            used[obj.name]=mats
        except Exception as e:errors.append(str(e))
        finally:
            if mesh is not None:evaluated.to_mesh_clear()
        if errors:issues[obj.name]=sorted(set(errors))
    valid={m.as_pointer() for name,mats in used.items() if name not in issues for m in mats}
    return issues,used,{key:mat for key,mat in reach.items() if key in valid}

def messages(issues):
    return [name+': '+reason for name,reasons in issues.items() for reason in reasons]
