"""Preview extracted terrain blend layers using their shader texture channels."""
from pathlib import Path
import bpy

def apply(mat, meta, directory):
    textures=meta.get('textures',[])
    blend=next((t for t in textures if t['usage']=='blend'),None)
    layers=[t for t in textures if t['usage']=='diffuse' and t.get('blend_channel') in (1,2,4,8)]
    if not blend or not layers:return
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    uv=nodes.new('ShaderNodeTexCoord').outputs['UV']
    def image(t,data=False):
        tex=nodes.new('ShaderNodeTexImage');tex.label=t.get('name','').split('\\')[-1]
        tex.image=bpy.data.images.load(str(Path(directory)/t['path']),check_existing=True)
        if data:tex.image.colorspace_settings.name='Non-Color'
        mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(*t['tiling'],1)
        links.new(uv,mapping.inputs[0]);links.new(mapping.outputs[0],tex.inputs['Vector']);return tex
    mask=image(blend,True);split=nodes.new('ShaderNodeSeparateColor');links.new(mask.outputs['Color'],split.inputs[0])
    weights={1:split.outputs[0],2:split.outputs[1],4:split.outputs[2],8:mask.outputs['Alpha']}
    def mix(a,b,operation):
        node=nodes.new('ShaderNodeMixRGB');node.blend_type=operation;node.inputs[0].default_value=1
        links.new(a,node.inputs[1]);links.new(b,node.inputs[2]);return node.outputs[0]
    combined=None
    for t in layers:
        color=image(t).outputs['Color'];channel=t['blend_channel']
        detail=next((d for d in textures if d['usage']=='diffuse_detail' and d.get('blend_channel')==channel),None)
        if detail:
            color=mix(color,image(detail).outputs['Color'],'MULTIPLY');color=mix(color,color,'ADD')
        weighted=mix(color,weights[channel],'MULTIPLY');combined=weighted if combined is None else mix(combined,weighted,'ADD')
    bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');links.new(combined,bsdf.inputs['Base Color'])
    mat['hb_layered_preview']=True
