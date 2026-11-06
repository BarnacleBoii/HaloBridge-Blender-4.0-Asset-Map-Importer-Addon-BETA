"""UV-painted materials baked to level-local Halo shaders; original tags stay intact."""
import json
import uuid
from pathlib import Path
import bpy
from . import cross_game


def image_node(mat, name, image, uv, tile=(1,1), data=False):
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    node=nodes.new('ShaderNodeTexImage');node.name=name;node.label=name;node.image=image
    mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.name=name+' Tiling'
    mapping.inputs[1].default_value=(tile[0],tile[1],1)
    links.new(uv,mapping.inputs[0]);links.new(mapping.outputs[0],node.inputs['Vector'])
    return node


def make(context, mode):
    obj=context.active_object
    if not obj or obj.type!='MESH' or not obj.data.uv_layers:raise ValueError('Select a mesh with a UV map first.')
    if obj.get('hb_preview'):raise ValueError('Place the asset first before creating editable materials.')
    if obj.get('hb_vehicle_tag'):raise ValueError('Use static mesh instead first; original vehicle tags control their own materials.')
    if obj.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    old=obj.active_material
    if not old or not old.use_nodes:raise ValueError('Apply an imported material first.')
    old_bsdf=next((n for n in old.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if not old_bsdf:raise ValueError('Select a material with a Principled shader.')
    try:source=cross_game.texture(old_bsdf.inputs['Base Color'])
    except ValueError:source=None
    source_textures=json.loads(old.get('hb_texture_sources','[]'))
    diffuse=[t for t in source_textures if t['usage']=='diffuse']
    if not source and diffuse:
        chosen=next((t for t in diffuse if t.get('blend_channel')==2),diffuse[0])
        image=bpy.data.images.load(str(Path(old['hb_texture_directory'])/chosen['path']),check_existing=True)
        source=(image,None,tuple(chosen['tiling']))
    if not source:raise ValueError('The current material needs a base-color image. Choose a plain imported material first.')
    base,_,tile=source
    normal=cross_game.texture(old_bsdf.inputs['Normal'])
    mat=bpy.data.materials.new(old.name+' - Editable '+mode.title());mat.use_nodes=True
    mat['hb_custom_shader']=mode;mat['hb_custom_id']=uuid.uuid4().hex;mat['hb_bake_size']=1024
    mat['hb_source_shader']=old.get('hb_shader','');mat['hb_shader']=old.get('hb_shader','')
    mat.blend_method=old.blend_method;mat.use_backface_culling=old.use_backface_culling
    if 'hb_collision_mode' in old:mat['hb_collision_mode']=old['hb_collision_mode']
    if hasattr(old,'ass_jms'):
        for flag in ('two_sided','transparent_1_sided','transparent_2_sided','render_only','collision_only'):
            if hasattr(old.ass_jms,flag):setattr(mat.ass_jms,flag,getattr(old.ass_jms,flag))
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;nodes.clear()
    uv=nodes.new('ShaderNodeTexCoord').outputs['UV']
    bsdf=nodes.new('ShaderNodeBsdfPrincipled');bsdf.name='HaloBridge Surface'
    output=nodes.new('ShaderNodeOutputMaterial');links.new(bsdf.outputs[0],output.inputs['Surface'])
    mask=bpy.data.images.new(mat.name+' Paint Mask',width=1024,height=1024,alpha=True)
    mask.colorspace_settings.name='Non-Color';mask.generated_color=(0,0,0,1) if mode=='terrain' else (1,0,0,0)
    mat['hb_mask_source']='Painted mask; Color 1 initially covers this whole material'
    if mode=='colors' and old.get('hb_change_mask_image'):
        found=bpy.data.images.get(old['hb_change_mask_image'])
        if found:
            bpy.data.images.remove(mask);mask=found.copy();mask.name=mat.name+' Color Mask';mask.colorspace_settings.name='Non-Color';mat['hb_mask_source']='Original Halo color-change mask'
    mask.pack()
    masknode=image_node(mat,'Paint Mask',mask,uv)
    channels=nodes.new('ShaderNodeSeparateColor');links.new(masknode.outputs['Color'],channels.inputs[0])
    basecopy=base.copy();basecopy.name=mat.name+' Base';basecopy.pack()
    if mode=='terrain':
        layers=[]
        for name in ('Grass','Rock','Dirt'):
            image=basecopy if name=='Grass' else basecopy.copy();layer_tile=tile
            channel={'Grass':2,'Rock':1,'Dirt':4}[name]
            chosen=next((t for t in diffuse if t.get('blend_channel')==channel),None)
            if chosen:
                image=bpy.data.images.load(str(Path(old['hb_texture_directory'])/chosen['path']),check_existing=False);image.pack();layer_tile=tuple(chosen['tiling'])
            tex=image_node(mat,name,image,uv,layer_tile)
            layers.append(tex.outputs['Color'])
        for index in range(2):
            mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX'
            links.new(channels.outputs[index],mix.inputs[0]);links.new(layers[0] if index==0 else previous,mix.inputs[1]);links.new(layers[index+1],mix.inputs[2]);previous=mix.outputs[0]
        links.new(previous,bsdf.inputs['Base Color'])
        mat.blend_method='OPAQUE'
    else:
        tex=image_node(mat,'Base Texture',basecopy,uv,tile);previous=tex.outputs['Color']
        for index in range(4):
            tint=nodes.new('ShaderNodeMixRGB');tint.name='Color '+str(index+1);tint.label=tint.name;tint.blend_type='MULTIPLY';tint.inputs[2].default_value=(1,1,1,1)
            links.new(channels.outputs[index] if index<3 else masknode.outputs['Alpha'],tint.inputs[0]);links.new(previous,tint.inputs[1]);previous=tint.outputs[0]
        links.new(previous,bsdf.inputs['Base Color'])
        if mat.blend_method!='OPAQUE':links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha'])
    if mode=='terrain' and all(any(t['usage']=='normal' and t.get('blend_channel')==channel for t in source_textures) for channel in (2,1,4)):
        normal_outputs=[]
        for name,channel in (('Grass',2),('Rock',1),('Dirt',4)):
            t=next(t for t in source_textures if t['usage']=='normal' and t.get('blend_channel')==channel)
            image=bpy.data.images.load(str(Path(old['hb_texture_directory'])/t['path']),check_existing=False);image.colorspace_settings.name='Non-Color';image.pack()
            normal_outputs.append(image_node(mat,name+' Normal',image,uv,t['tiling']).outputs['Color'])
        for index in range(2):
            mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';links.new(channels.outputs[index],mix.inputs[0]);links.new(normal_outputs[0] if index==0 else previous,mix.inputs[1]);links.new(normal_outputs[index+1],mix.inputs[2]);previous=mix.outputs[0]
        normalnode=nodes.new('ShaderNodeNormalMap');links.new(previous,normalnode.inputs['Color']);links.new(normalnode.outputs[0],bsdf.inputs['Normal'])
    elif normal:
        n=image_node(mat,'Normal Texture',normal[0].copy(),uv,normal[2]);n.image.pack()
        normalnode=nodes.new('ShaderNodeNormalMap');links.new(n.outputs['Color'],normalnode.inputs['Color']);links.new(normalnode.outputs[0],bsdf.inputs['Normal'])
    for i,node in enumerate(nodes):node.location=((i%5)*230,-(i//5)*220)
    nodes.active=masknode;masknode.select=True
    if obj.data.users>1:obj.data=obj.data.copy()
    obj.data.materials[obj.active_material_index]=mat
    return mat


def validate(mat):
    if not mat.use_nodes:raise ValueError('Enable material nodes for the editable material.')
    allowed={'BSDF_PRINCIPLED','OUTPUT_MATERIAL','TEX_COORD','TEX_IMAGE','VECT_MATH','MIX_RGB','SEPARATE_COLOR','NORMAL_MAP','RGB','VALUE','MATH','UVMAP','REROUTE'}
    for node in mat.node_tree.nodes:
        if node.type not in allowed:raise ValueError('Unsupported editable-material node: '+node.name+'. This exporter supports UV/image-based materials.')
        if node.type=='TEX_IMAGE' and (not node.image or not all(node.image.size)):raise ValueError('Choose an image for '+node.name)
        if node.type=='TEX_COORD' and any(s.is_linked for s in node.outputs if s.name!='UV'):raise ValueError('Editable materials must use UV coordinates.')
    if not any(n.type=='BSDF_PRINCIPLED' for n in mat.node_tree.nodes):raise ValueError('Missing Principled shader.')
    if int(mat.get('hb_bake_size',1024)) not in (512,1024,2048,4096):raise ValueError('Texture resolution must be 512, 1024, 2048 or 4096.')


def repeats_on_uv_tiles(mat):
    """Recognize the color editor's unit-period UV graph before allowing wrapped UVs."""
    if mat.get('hb_custom_shader') != 'colors':
        return False
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_COORD':
            if any(link.to_node.type != 'VECT_MATH' or link.to_socket != link.to_node.inputs[0]
                   for link in node.outputs['UV'].links):
                return False
        elif node.type == 'VECT_MATH':
            if node.operation != 'MULTIPLY' or node.inputs[1].is_linked:
                return False
            if any(not float(v).is_integer() for v in node.inputs[1].default_value[:2]):
                return False
            if any(link.to_node.type != 'TEX_IMAGE' or link.to_socket.name != 'Vector'
                   for link in node.outputs[0].links):
                return False
        elif node.type == 'TEX_IMAGE':
            if node.extension != 'REPEAT' or node.projection != 'FLAT':
                return False
            if any(link.from_node.type != 'VECT_MATH' for link in node.inputs['Vector'].links):
                return False
        elif node.type == 'UVMAP':
            return False
    return True


def pack(mat):
    for node in mat.node_tree.nodes:
        if node.type=='TEX_IMAGE' and node.image:node.image.pack()


def bake(mat, folder, progress=None):
    """Bake base-color nodes with emission, so lighting is never baked in."""
    validate(mat);pack(mat);folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    name='custom_'+mat['hb_custom_id'][:20];size=int(mat.get('hb_bake_size',1024))
    original_scene=bpy.context.window.scene
    scene=bpy.data.scenes.new('HaloBridge texture bake');copy=mat.copy();mesh=bpy.data.meshes.new('Bake UV tile');obj=bpy.data.objects.new('Bake UV tile',mesh)
    images=[];maps={}
    try:
        scene.collection.objects.link(obj);mesh.from_pydata([(0,0,0),(1,0,0),(1,1,0),(0,1,0)],[],[(0,1,2,3)])
        uv=mesh.uv_layers.new(name='UVMap')
        for loop,co in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]):loop.uv=co
        mesh.materials.append(copy);scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1
        bpy.context.window.scene=scene;obj.select_set(True);bpy.context.view_layer.objects.active=obj
        nodes=copy.node_tree.nodes;links=copy.node_tree.links
        bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
        emission=nodes.new('ShaderNodeEmission');links.new(emission.outputs[0],output.inputs['Surface'])
        sources=[('base_map',bsdf.inputs['Base Color'],True)]
        if bsdf.inputs['Normal'].is_linked:
            normal=bsdf.inputs['Normal'].links[0].from_node
            if normal.type!='NORMAL_MAP':raise ValueError('Use a Normal Map node for editable normal textures.')
            sources.append(('normal_map',normal.inputs['Color'],False))
        if mat.blend_method!='OPAQUE':sources.append(('alpha_map',bsdf.inputs['Alpha'],False))
        for usage,socket,color in sources:
            if progress:progress('Baking '+mat.name+' / '+usage+' ('+str(size)+' x '+str(size)+')')
            for link in list(emission.inputs['Color'].links):links.remove(link)
            if socket.is_linked:links.new(socket.links[0].from_socket,emission.inputs['Color'])
            else:
                value=socket.default_value;emission.inputs['Color'].default_value=(value,value,value,1) if isinstance(value,(float,int)) else value
            image=bpy.data.images.new(name+' '+usage,width=size,height=size,alpha=True);images.append(image)
            image.colorspace_settings.name='sRGB' if color else 'Non-Color'
            target=nodes.new('ShaderNodeTexImage');target.image=image;nodes.active=target
            result=bpy.ops.object.bake(type='EMIT',margin=0,use_clear=True)
            if result!={'FINISHED'}:raise RuntimeError('Texture bake did not finish.')
            path=folder/(name+'_'+usage+'.tif');image.filepath_raw=str(path);image.file_format='TIFF';image.save();maps[usage]=str(path);nodes.remove(target)
        return dict(name=name,tiling=(1.,1.),maps=maps)
    finally:
        bpy.context.window.scene=original_scene
        bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(mesh);bpy.data.materials.remove(copy);bpy.data.scenes.remove(scene)
        for image in images:bpy.data.images.remove(image)
