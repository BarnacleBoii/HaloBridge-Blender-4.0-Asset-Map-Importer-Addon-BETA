using System.Reflection;
using System.Text.Json;
using Reclaimer.Blam.Common;
using Reclaimer.Geometry;
using Reclaimer.Utilities;
using H1 = Reclaimer.Blam.Halo1;
using H2 = Reclaimer.Blam.Halo2;

// Halo: CE and Halo 2 (MCC) support. These games use different tag layouts from
// Halo 3, but Reclaimer decodes their models, BSPs and shaders into the same
// geometry/material objects, so the JSON written here matches the Halo 3 format.
internal static class ClassicSupport {
 internal static readonly string[] Halo1Shaders={"senv","soso","schi","scex","sotr","swat","sgla","smet","spla"};
 internal static bool IsClassic(ICacheFile cache)=>cache.Metadata.Engine==BlamEngine.Halo1 || (cache.Metadata.Engine==BlamEngine.Halo2 && cache.CacheType>CacheType.Halo2Beta);
 internal static string Game(ICacheFile cache)=>cache.Metadata.Engine==BlamEngine.Halo1?"halo1":"halo2";
 static bool IsH1(ICacheFile cache)=>cache.Metadata.Engine==BlamEngine.Halo1;
 internal static bool IsShader(ICacheFile cache,IIndexItem tag)=>IsH1(cache)?Halo1Shaders.Contains(tag.ClassCode):tag.ClassCode=="shad";
 internal static string ModelClass(ICacheFile cache)=>IsH1(cache)?"mod2":"mode";

 static string? RenderModelOf(ICacheFile cache,IIndexItem scenery) {
  if(IsH1(cache))return scenery.ReadMetadata<H1.SceneryTag>().Model.Tag?.TagName;
  return scenery.ReadMetadata<H2.SceneryTag>().Model.Tag?.ReadMetadata<H2.ModelTag>().RenderModel.Tag?.TagName;
 }

 internal static void Index(ICacheFile cache,string map,string output) {
  var assets=new List<object>();var warnings=new List<string>();
  foreach(var tag in cache.TagIndex) {
   if(IsShader(cache,tag))assets.Add(new{tag=tag.TagName,kind="material",name=tag.FileName,section=-1});
   if(tag.ClassCode==ModelClass(cache))assets.Add(new{tag=tag.TagName,kind="model",name=tag.FileName,section=-1});
   if(tag.ClassCode=="scen") {
    try {var render=RenderModelOf(cache,tag);if(render!=null)assets.Add(new{tag=render,scenery_tag=tag.TagName,kind="scenery",name=tag.FileName,section=-1});}
    catch(Exception e){warnings.Add("Scenery "+tag.TagName+": "+e.Message);}
   }
   if(tag.ClassCode=="sbsp" && !IsH1(cache)) {
    // Halo 2 instanced geometry; Halo CE BSPs have no instances and come in through whole-map import.
    try {
     var model=((IContentProvider<Model>)tag.ReadMetadata<H2.ScenarioStructureBspTag>()).GetContent();
     foreach(var group in model.Regions.SelectMany(r=>r.Permutations).Where(p=>p.IsInstanced)
       .SelectMany(p=>p.MeshIndices.Select(i=>(permutation:p,index:i))).GroupBy(p=>p.index))
      assets.Add(new{tag=tag.TagName,kind="instance",name=group.First().permutation.Name,section=group.Key});
    }catch(Exception e){warnings.Add("BSP "+tag.TagName+": "+e.Message);}
   }
  }
  Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(output))!);
  File.WriteAllText(output,JsonSerializer.Serialize(new{version=1,game=Game(cache),map,assets,warnings}));
 }

 static readonly Assembly Blam=typeof(ICacheFile).Assembly;

 // One shader as a Reclaimer material (textures and alpha mode).
 internal static Material? ShaderMaterial(ICacheFile cache,IIndexItem tag) {
  if(IsH1(cache)) {
   using var reader=cache.CreateReader(cache.DefaultAddressTranslator);
   var method=Blam.GetType("Reclaimer.Blam.Halo1.Halo1Common")!.GetMethod("GetMaterials",BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic)!;
   var refs=new[]{new TagReference(cache,tag.ClassId,tag.Id)};
   return ((IEnumerable<Material>)method.Invoke(null,new object[]{refs,reader})!).ToList().FirstOrDefault();
  }
  var material=new Material{Id=tag.Id,Name=tag.FileName};
  material.CustomProperties.Add("tag_name",tag.TagName);
  var helper=Blam.GetType("Reclaimer.Blam.Halo2.MaterialHelper")!.GetMethod("PopulateTextureMappings",BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic)!;
  helper.Invoke(null,new object[]{new Dictionary<int,H2.BitmapTag>(),material,tag.ReadMetadata<H2.ShaderTag>()});
  return material;
 }

 // The open classic cache, so material writing can fill textures Reclaimer leaves out.
 internal static ICacheFile? Current;

 // Reclaimer reads only some classic shader types: Halo: CE shader_transparent_generic
 // (most sky parts) gets no texture and shader_transparent_chicago only its first map;
 // Halo 2 shaders whose template passes it does not recognise (skies, many effects)
 // lose their bitmaps. When a material has no diffuse texture, its first bitmap is used.
 internal static void FillMissingDiffuse(Material material) {
  var cache=Current;
  if(cache==null || material.TextureMappings.Any(t=>t.Usage==TextureUsage.Diffuse && t.Texture!=null))return;
  try {
   var tag=cache.TagIndex.FirstOrDefault(t=>t.Id==material.Id && IsShader(cache,t));
   if(tag==null)return;
   IIndexItem? bitmap;
   if(IsH1(cache))bitmap=FirstH1Bitmap(cache,tag);
   else {
    // Slot 0 is often a placeholder (shaders\default_bitmaps\...); prefer the bitmap Reclaimer
    // already mapped (as transparency), then the first real one.
    var all=tag.ReadMetadata<H2.ShaderTag>().ShaderProperties.SelectMany(p=>p.Bitmaps).Select(b=>b.BitmapReference.Tag).Where(b=>b!=null && !b.TagName.StartsWith(@"shaders\default_bitmaps",StringComparison.OrdinalIgnoreCase)).ToList();
    var mapped=material.TextureMappings.Where(t=>t.Texture!=null).Select(t=>t.Texture.Id).ToHashSet();
    bitmap=all.FirstOrDefault(b=>mapped.Contains(b.Id)) ?? all.FirstOrDefault();
   }
   if(bitmap==null)return;
   var texture=new Texture{Id=bitmap.Id,ContentProvider=IsH1(cache)?bitmap.ReadMetadata<H1.BitmapTag>():bitmap.ReadMetadata<H2.BitmapTag>()};
   texture.CustomProperties.Add("tag_name",bitmap.TagName);  // Reclaimer's source tag property
   // An existing "transparency" map of the same bitmap stays; it is unused while the material is opaque.
   material.TextureMappings.Insert(0,new TextureMapping{Usage=TextureUsage.Diffuse,Tiling=System.Numerics.Vector2.One,Texture=texture});
  } catch(Exception e){Console.Error.WriteLine("Classic shader "+material.Name+": "+e.Message);}
 }

 // Halo: CE tag data lays a tag's blocks out right after its main struct, so the
 // shader's bitmap references are found by scanning to the next tag's data.
 static IIndexItem? FirstH1Bitmap(ICacheFile cache,IIndexItem shader) {
  var bitmapClass=cache.TagIndex.FirstOrDefault(t=>t.ClassCode=="bitm");
  if(bitmapClass==null)return null;
  long start=shader.MetaPointer.Address;
  long next=cache.TagIndex.Select(t=>t.MetaPointer.Address).Where(a=>a>start).DefaultIfEmpty(start+4096).Min();
  int length=(int)Math.Clamp(next-start,0,8192);
  if(length<16)return null;
  using var reader=cache.CreateReader(cache.DefaultAddressTranslator);
  reader.Seek(start,SeekOrigin.Begin);
  var data=reader.ReadBytes(length);  for(int i=0;i+16<=data.Length;i+=4) {
   if(BitConverter.ToInt32(data,i)!=bitmapClass.ClassId)continue;
   int index=BitConverter.ToInt16(data,i+12);
   if(index<0 || index>=cache.TagIndex.TagCount)continue;
   var candidate=cache.TagIndex[index];
   if(candidate!=null && candidate.ClassCode=="bitm")return candidate;
  }
  return null;
 }

 internal static void Material(ICacheFile cache,string path,string output) {
  var tag=cache.TagIndex.First(t=>t.TagName==path && IsShader(cache,t));
  var material=ShaderMaterial(cache,tag) ?? throw new Exception("Shader has no material data: "+path);
  Directory.CreateDirectory(output);
  File.WriteAllText(Path.Combine(output,"preview.json"),JsonSerializer.Serialize(new{version=1,materials=Program.WriteMaterials(new[]{material},output),meshes=Array.Empty<object>()}));
 }
}
