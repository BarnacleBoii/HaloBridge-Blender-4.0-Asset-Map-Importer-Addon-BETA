using System.Text.Json;
using Reclaimer.Blam.Common;
using Reclaimer.Blam.HaloReach;
using Reclaimer.Geometry;
using Reclaimer.Utilities;

internal static class ReachSupport {
 internal static void Index(ICacheFile cache,string map,string output) {
  var assets=new List<object>();var warnings=new List<string>();
  foreach(var tag in cache.TagIndex) {
   if(new[]{"rmsh","rmtr","rmfl","rmhg","rmw ","rmcs"}.Contains(tag.ClassCode))
    assets.Add(new{tag=tag.TagName,kind="material",name=tag.FileName,section=-1});
   if(tag.ClassCode=="mode")assets.Add(new{tag=tag.TagName,kind="model",name=tag.FileName,section=-1});
   if(tag.ClassCode=="scen") {
    try {
     var obj=tag.ReadMetadata<SceneryTag>();
     var render=obj.Model.Tag.ReadMetadata<ModelTag>().RenderModel.Tag;
     if(render!=null)assets.Add(new{tag=render.TagName,scenery_tag=tag.TagName,kind="scenery",name=tag.FileName,section=-1});
    }catch(Exception e){warnings.Add("Scenery "+tag.TagName+": "+e.Message);}
   }
   if(tag.ClassCode=="sbsp") {
    try {
     // Reach instance section indices are resource fixups, not the initial tag values.
     var model=((IContentProvider<Model>)tag.ReadMetadata<ScenarioStructureBspTag>()).GetContent();
     foreach(var group in model.Regions.SelectMany(r=>r.Permutations).Where(p=>p.IsInstanced)
       .SelectMany(p=>p.MeshIndices.Select(i=>(permutation:p,index:i))).GroupBy(p=>p.index))
      assets.Add(new{tag=tag.TagName,kind="instance",name=group.First().permutation.Name,section=group.Key});
    }catch(Exception e){warnings.Add("BSP "+tag.TagName+": "+e.Message);}
   }
  }
  Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(output))!);
  File.WriteAllText(output,JsonSerializer.Serialize(new{version=1,game="reach",map,assets,warnings}));
 }
 internal static void Material(ICacheFile cache,string path,string output) {
  var tag=cache.TagIndex.First(t=>t.TagName==path && t.ClassCode.StartsWith("rm"));
  var method=typeof(ShaderBlock).Assembly.GetType("Reclaimer.Blam.HaloReach.HaloReachCommon")!.GetMethod("GetMaterials")!;
  var materials=(IEnumerable<Material>)method.Invoke(null,new object[]{new[]{new ShaderBlock{ShaderReference=new TagReference(cache,tag.ClassId,tag.Id)}}})!;
  Directory.CreateDirectory(output);
  File.WriteAllText(Path.Combine(output,"preview.json"),JsonSerializer.Serialize(new{version=1,materials=Program.WriteMaterials(materials,output),meshes=Array.Empty<object>()}));
 }
 // Preview textures for a Reach Editing Kit scenario import, looked up by exact shader tag path.
 internal static void Materials(ICacheFile cache,string[] tags,string output) {
  var wanted=tags.Select(t=>t.Replace('/','\\')).Distinct(StringComparer.OrdinalIgnoreCase).ToArray();
  var shaders=cache.TagIndex.Where(t=>t.ClassCode.StartsWith("rm")).GroupBy(t=>t.TagName,StringComparer.OrdinalIgnoreCase).ToDictionary(g=>g.Key,g=>g.First(),StringComparer.OrdinalIgnoreCase);
  var method=typeof(ShaderBlock).Assembly.GetType("Reclaimer.Blam.HaloReach.HaloReachCommon")!.GetMethod("GetMaterials")!;
  var found=new Dictionary<string,object>();var missing=new List<string>();var warnings=new List<string>();
  Directory.CreateDirectory(output);
  foreach(var name in wanted) {
   if(!shaders.TryGetValue(name,out var tag)){missing.Add(name);continue;}
   try {
    var materials=(IEnumerable<Material>)method.Invoke(null,new object[]{new[]{new ShaderBlock{ShaderReference=new TagReference(cache,tag.ClassId,tag.Id)}}})!;
    var written=Program.WriteMaterials(materials,output,warnings);
    if(written.Count>0)found[name]=written[0];else missing.Add(name);
   } catch(Exception e){warnings.Add(name+": "+e.Message);missing.Add(name);}
  }
  File.WriteAllText(Path.Combine(output,"materials.json"),JsonSerializer.Serialize(new{version=1,materials=found,missing,warnings}));
 }
}
