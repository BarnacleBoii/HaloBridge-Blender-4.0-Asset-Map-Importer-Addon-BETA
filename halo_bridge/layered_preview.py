"""Preview stock terrain weights; an optional RGB paint overlay overrides them."""
from pathlib import Path
import json
import bpy


def apply(mat, meta, directory, editable=False):
    textures=meta.get('textures',[])
    blend=next((t for t in textures if t['usage']=='blend'),None)
    layers=sorted((t for t in textures if t['usage']=='diffuse' and t.get('blend_channel') in (1,2,4,8)),key=lambda t:t['blend_channel'])
    if not blend or not layers:return
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    uv=nodes.new('ShaderNodeTexCoord').outputs['UV']
    def image(t,name,data=False):
        tex=nodes.new('ShaderNodeTexImage');tex.name=name;tex.label=t.get('name','').split(chr(92))[-1]
        tex.image=bpy.data.images.load(str(Path(directory)/t['path']),check_existing=not editable)
        if data:tex.image.colorspace_settings.name='Non-Color'
        if editable:tex.image.pack()
        mapping=nodes.new('ShaderNodeVectorMath');mapping.name=name+' Tiling';mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(*t['tiling'],1)
        links.new(uv,mapping.inputs[0]);links.new(mapping.outputs[0],tex.inputs['Vector']);return tex
    mask=image(blend,'Original Blend',True);split=nodes.new('ShaderNodeSeparateColor');links.new(mask.outputs['Color'],split.inputs[0])
    weights={1:split.outputs[0],2:split.outputs[1],4:split.outputs[2],8:mask.outputs['Alpha']}
    def mix(a,b,operation):
        node=nodes.new('ShaderNodeMixRGB');node.blend_type=operation;node.inputs[0].default_value=1
        links.new(a,node.inputs[1]);links.new(b,node.inputs[2]);return node.outputs[0]
    def math(op,a,b):
        node=nodes.new('ShaderNodeMath');node.operation=op
        links.new(a,node.inputs[0]);links.new(b,node.inputs[1]);return node.outputs[0]
    if editable:
        paint=nodes.new('ShaderNodeTexImage');paint.name='Paint Mask'
        paint.image=bpy.data.images.new(mat.name+' Layer Paint',width=1024,height=1024,alpha=False)
        paint.image.colorspace_settings.name='Non-Color';paint.image.generated_color=(0,0,0,1);paint.image.pack()
        links.new(uv,paint.inputs['Vector'])
        rgb=nodes.new('ShaderNodeSeparateColor');links.new(paint.outputs['Color'],rgb.inputs[0]);r,g,b=rgb.outputs[:3]
        strength=math('MAXIMUM',math('MAXIMUM',r,g),b)
        # White selects layer four. Black restores the stock blend.
        fourth=math('MINIMUM',math('MINIMUM',r,g),b)
        channels=[math('SUBTRACT',v,fourth) for v in (r,g,b)]+[fourth]
        # RGB brush mixtures must retain unit total weight across soft strokes.
        total=math('ADD',math('ADD',channels[0],channels[1]),math('ADD',channels[2],fourth))
        for index,t in enumerate(layers):
            ch=t['blend_channel'];n=nodes.new('ShaderNodeMixRGB');links.new(strength,n.inputs[0]);links.new(weights[ch],n.inputs[1]);links.new(math('DIVIDE',channels[index],total),n.inputs[2]);weights[ch]=n.outputs[0]
        mat['hb_layers']=json.dumps(['Shader '+str(i+1) for i in range(len(layers))])
    combined=None;normal_sum=None
    for index,t in enumerate(layers):
        name='Shader '+str(index+1);color=image(t,name).outputs['Color'];channel=t['blend_channel']
        detail=next((d for d in textures if d['usage']=='diffuse_detail' and d.get('blend_channel')==channel),None)
        if detail:
            color=mix(color,image(detail,name+' Detail').outputs['Color'],'MULTIPLY');color=mix(color,color,'ADD')
        weighted=mix(color,weights[channel],'MULTIPLY');combined=weighted if combined is None else mix(combined,weighted,'ADD')
        normal=next((d for d in textures if d['usage']=='normal' and d.get('blend_channel')==channel),None)
        if normal:
            weighted=mix(image(normal,name+' Normal',True).outputs['Color'],weights[channel],'MULTIPLY')
            normal_sum=weighted if normal_sum is None else mix(normal_sum,weighted,'ADD')
    bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');links.new(combined,bsdf.inputs['Base Color'])
    if normal_sum:
        n=nodes.new('ShaderNodeNormalMap');links.new(normal_sum,n.inputs['Color']);links.new(n.outputs[0],bsdf.inputs['Normal'])
    mat['hb_layered_preview']=True
    if editable:nodes.active=paint
    return True
