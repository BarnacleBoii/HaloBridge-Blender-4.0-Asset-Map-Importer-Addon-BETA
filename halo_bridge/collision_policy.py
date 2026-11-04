"""Collision policy for current-mesh exports; never infer foliage from names."""
from pathlib import Path

# Citadel's third leaf material uses the generic shader class. Verified with the
# stock plant_tree_pine: excluding these leaf cards removes its remaining overlap
# warnings while the bark remains collidable. This is an exact tag, not a name rule.
VERIFIED_LEAF_TAGS={r'levels\solo\100_citadel\shaders\cit_tree_leafc'}

def render_only(material,shader_source=None,shader_tag=''):
    mode=getattr(material,'hb_collision_mode','AUTO')
    if mode=='SOLID':return False
    if mode=='RENDER_ONLY':return True
    # A generic transparent shader can be glass, so alpha alone is not enough.
    return bool(material.ass_jms.render_only or
                (shader_source and shader_tag.replace('/','\\').lower() in VERIFIED_LEAF_TAGS) or
                (shader_source and Path(shader_source).suffix.lower()=='.shader_foliage'))
