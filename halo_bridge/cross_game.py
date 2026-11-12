"""Convert other games' imported preview materials into project-local destination shaders.

Any material whose shader comes from a game other than the Sapien destination
(Reach, ODST in a Halo 3 level, Halo CE, Halo 2, ...) is rebuilt from its
preview textures. Halo 3 and ODST share tag paths, so a shader that already
exists in the destination kit is reused instead of converted.
"""
import hashlib
from pathlib import Path
import bpy
import numpy as np
from .diagnostics import ValidationError
from . import compat, games


def _kit_has_shader(kit,tag):
    if not kit or not tag:return False
    from .export_review import shader_file
    try:shader_file(kit,tag);return True
    except ValueError:return False


def converts(obj,mat,config=None):
    """True when this material must be rebuilt from its preview textures."""
    target=(config or {}).get('game') or games.target_game()
    if not games.needs_conversion(obj,mat,target):return False
    source=games.material_game(obj,mat,target)
    if games.shares_tags(source,target) and config and _kit_has_shader(config.get('kit'),mat.get('hb_shader','')):
        return False
    return True


def reach_materials(objects,config=None):
    """Materials needing conversion (name kept for compatibility; covers every source game)."""
    return {m.as_pointer():m for o in objects for m in o.data.materials
            if m and not m.name.startswith('+') and (m.get('hb_custom_shader') or converts(o,m,config))}

converted_materials=reach_materials


def texture(socket):
    if not socket.is_linked:return None
    link=socket.links[0];node=link.from_node;channel=link.from_socket.name
    if node.type=='NORMAL_MAP':return texture(node.inputs['Color'])
    if node.type=='SEPARATE_COLOR':
        result=texture(node.inputs[0])
        return (result[0],{'Red':0,'Green':1,'Blue':2}[channel],result[2]) if result else None
    if node.type!='TEX_IMAGE' or not node.image:
        raise ValueError('Unsupported material nodes. Use the imported image textures or assign a Halo 3 shader.')
    tile=(1.,1.)
    if node.inputs['Vector'].is_linked:
        mapping=node.inputs['Vector'].links[0].from_node
        if mapping.type=='VECT_MATH' and mapping.operation=='MULTIPLY':tile=tuple(mapping.inputs[1].default_value[:2])
        elif mapping.type!='TEX_COORD':raise ValueError('Unsupported texture mapping; use imported UV mapping.')
    if not all(np.isfinite(x) and x>0 for x in tile):raise ValueError('Texture tiling must be positive.')
    return node.image,3 if channel=='Alpha' else None,tile


def _recorded(mat,usage):
    """The material's original texture of this usage, from its import metadata."""
    import json
    try:entries=json.loads(mat.get('hb_texture_sources','[]'))
    except ValueError:return None
    entry=next((t for t in entries if t.get('usage')==usage),None)
    if not entry:return None
    path=Path(mat.get('hb_texture_directory',''))/entry['path']
    if not path.is_file():raise ValueError('Missing texture: '+str(path))
    image=bpy.data.images.load(str(path),check_existing=True)
    if usage=='normal':image.colorspace_settings.name='Non-Color'
    tile=tuple(float(x) for x in (entry.get('tiling') or (1.,1.))[:2])
    if not all(np.isfinite(x) and x>0 for x in tile):tile=(1.,1.)
    channel={1:0,2:1,4:2}.get(entry.get('channels',8),3)
    return image,channel,tile


def sources(mat):
    """(base, normal, alpha) texture sources: (image, channel, tiling) or None each.

    Simple preview node trees (and user edits to them) are read from the nodes.
    Layered/detail previews (Halo 3, ODST, Halo 2 ...) fall back to the textures
    recorded when the material was imported.
    """
    bsdf=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if compat.nodes_enabled(mat) else None
    transparent=compat.is_transparent(mat)
    try:
        if not bsdf:raise ValueError('No Principled preview material found.')
        base=texture(bsdf.inputs['Base Color']);normal=texture(bsdf.inputs['Normal'])
        alpha=texture(bsdf.inputs['Alpha']) if transparent else None
        return base,normal,alpha,bsdf
    except ValueError:
        if not mat.get('hb_texture_sources'):raise
    base=_recorded(mat,'diffuse')
    alpha=None
    if transparent:
        alpha=_recorded(mat,'transparency') or (base and (base[0],3,base[2]))
    if base:base=(base[0],None,base[2])
    return base,_recorded(mat,'normal'),alpha,bsdf


def pixels(image):
    if not image.has_data:image.reload()
    w,h=image.size
    if not w or not h:raise ValueError('Missing texture: '+image.filepath)
    result=np.empty(w*h*4,dtype=np.float32);image.pixels.foreach_get(result)
    return result.reshape(h,w,4)


def write_image(image,path):
    save_pixels(pixels(image),path,color=image.colorspace_settings.name!='Non-Color')


def sampled(data,width,height,ratio):
    # Wrap UVs just like the imported image nodes; different resolutions are allowed.
    y=(np.floor((np.arange(height)+.5)/height*ratio[1]*data.shape[0]).astype(int)%data.shape[0])
    x=(np.floor((np.arange(width)+.5)/width*ratio[0]*data.shape[1]).astype(int)%data.shape[1])
    return data[y[:,None],x[None,:]]


def save_pixels(data,path,color=False):
    image=bpy.data.images.new('HaloBridge converted texture',width=data.shape[1],height=data.shape[0],alpha=True)
    try:
        image.colorspace_settings.name='sRGB' if color else 'Non-Color'
        image.pixels.foreach_set(np.ascontiguousarray(data,dtype=np.float32).ravel())
        image.filepath_raw=str(path);image.file_format='TIFF';image.save()
    finally:bpy.data.images.remove(image)


def prepare(objects,folder,progress=None,materials=None):
    progress=progress or (lambda message:None)
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    result={};issues=[]
    materials=reach_materials(objects) if materials is None else materials
    custom_ids=set()
    for index,(pointer,mat) in enumerate(materials.items(),1):
        progress(f'Preparing material {index}/{len(materials)}: '+mat.get('hb_label',mat.name))
        try:
            if mat.get('hb_custom_shader'):
                from . import editable_materials
                import uuid
                if mat.get('hb_custom_id') in custom_ids:mat['hb_custom_id']=uuid.uuid4().hex
                custom_ids.add(mat.get('hb_custom_id'))
                result[pointer]=editable_materials.bake(mat,folder,progress)
                continue
            base,normal,alpha,bsdf=sources(mat)
            if not bsdf and not base:raise ValueError('No Principled preview material found.')
            key='reach_'+hashlib.sha256((mat.get('hb_conversion_id',mat.name)+'|'+mat.get('hb_shader','')).encode()).hexdigest()[:20]
            maps={};tile=base[2] if base else (1.,1.)
            path=folder/(key+'_base.tif')
            if base:write_image(base[0],path)
            else:
                data=np.empty((4,4,4),dtype=np.float32);data[:]=tuple(bsdf.inputs['Base Color'].default_value);save_pixels(data,path,color=True)
            maps['base_map']=str(path)
            for label,source in (('normal_map',normal),('alpha_map',alpha)):
                if source is None:continue
                image,channel,uv=source;path=folder/(key+('_normal.tif' if label=='normal_map' else '_alpha.tif'))
                ratio=tuple(uv[i]/tile[i] for i in range(2))
                if label=='normal_map' and ratio==(1.,1.):write_image(image,path)
                else:
                    data=pixels(image);data=sampled(data,data.shape[1],data.shape[0],ratio)
                    if label=='alpha_map':
                        channel=channel if channel is not None else 0
                        mask=data[:,:,channel].copy();data=np.repeat(mask[:,:,None],4,axis=2)
                    save_pixels(data,path)
                maps[label]=str(path)
            result[pointer]=dict(name=key,tiling=tile,maps=maps)
        except Exception as error:issues.append(mat.get('hb_label',mat.name)+': '+str(error))
    if issues:raise ValidationError(issues,'Material conversion')
    return result
