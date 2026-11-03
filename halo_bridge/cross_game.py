"""Convert imported Reach preview materials into project-local Halo 3 shaders."""
import hashlib
from pathlib import Path
import bpy
import numpy as np
from .diagnostics import ValidationError


def reach_materials(objects):
    return {m.as_pointer():m for o in objects for m in o.data.materials
            if m and not m.name.startswith('+') and m.get('hb_shader_game')!='halo3' and (o.get('hb_game')=='reach' or m.get('hb_game')=='reach')}


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
    for index,(pointer,mat) in enumerate(materials.items(),1):
        progress(f'Converting Reach material {index}/{len(materials)}: '+mat.get('hb_label',mat.name))
        try:
            bsdf=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if mat.use_nodes else None
            if not bsdf:raise ValueError('No Principled preview material found.')
            base=texture(bsdf.inputs['Base Color']);normal=texture(bsdf.inputs['Normal']);alpha=texture(bsdf.inputs['Alpha']) if mat.blend_method!='OPAQUE' else None
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
    if issues:raise ValidationError(issues,'Reach material conversion')
    return result
