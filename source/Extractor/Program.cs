using System.Numerics;
using System.Text.Json;
using Reclaimer.Blam.Common;
using Reclaimer.Blam.Halo3;
using Reclaimer.Geometry;
using Reclaimer.Utilities;

// Geometry stays in Halo world units. RMF is retained as the interchange master;
// a small JSON preview avoids requiring the RMF importer's Qt UI inside Blender.
class Program {
 static JsonSerializerOptions json = new() { WriteIndented = false };
 static void Save(string path, object value) { Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path))!);File.WriteAllText(path,JsonSerializer.Serialize(value,json)); }
 static float[] V(Vector3 v)=>new[]{v.X,v.Y,v.Z};
 static int Main(string[] args) {
  try {
   var job=JsonDocument.Parse(File.ReadAllText(args[0])).RootElement;
   if(job.GetProperty("version").GetInt32()!=1) throw new Exception("Unsupported job version");
   var map=job.GetProperty("map").GetString()!; var output=job.GetProperty("output").GetString()!;
   var cache=CacheFactory.ReadCacheFile(map);
   bool reach=cache.Metadata.Engine==BlamEngine.HaloReach;
   if((cache.Metadata.Engine!=BlamEngine.Halo3 && !reach) || !cache.Metadata.IsMcc) throw new Exception("Select an MCC PC Halo 3 or Halo: Reach map.");
   if(job.TryGetProperty("game",out var requested) && requested.GetString()!=(reach?"reach":"halo3")) throw new Exception("The map belongs to a different game. Change the Halo game selector or maps folder.");
   var op=job.GetProperty("operation").GetString();
   if(new[]{"extract","material","map_scene"}.Contains(op))Save(Path.Combine(output,"texture_names.json"),new{version=1,textures=cache.TagIndex.Where(t=>t.ClassCode=="bitm").ToDictionary(t=>t.Id.ToString(),t=>t.TagName)});
   if(op=="texture_names") {
    Save(output,new{version=1,textures=cache.TagIndex.Where(t=>t.ClassCode=="bitm").ToDictionary(t=>t.Id.ToString(),t=>t.TagName)});
   } else if(op=="audit_variants") {
    Save(output,ModelSelection.Audit(cache,reach));
   } else if(op=="scenario_info") {
    Save(output,new{version=1,scenario=cache.TagIndex.GetGlobalTag("scnr").TagName});
   } else if(op=="index") {
    if(reach){ReachSupport.Index(cache,map,output);return 0;}
    var assets=new List<object>();
    foreach(var tag in cache.TagIndex) {
     if(new[]{"rmsh","rmtr","rmfl","rmhg","rmw ","rmcs"}.Contains(tag.ClassCode)) assets.Add(new {tag=tag.TagName,kind="material",name=Path.GetFileName(tag.TagName),section=-1});
     if(tag.ClassCode=="scen") {
      try { var scenery=tag.ReadMetadata<SceneryTag>();var render=scenery.ReadRenderModel();
       assets.Add(new {tag=scenery.Model.Tag.ReadMetadata<ModelTag>().RenderModel.Tag.TagName,scenery_tag=tag.TagName,kind="scenery",name=Path.GetFileName(tag.TagName),section=-1});
      }catch(Exception e){Console.Error.WriteLine("Skipping scenery "+tag.TagName+": "+e.Message);}
     }
     if(tag.ClassCode=="mode") assets.Add(new { tag=tag.TagName, kind="model", name=Path.GetFileName(tag.TagName), section=-1 });
     if(tag.ClassCode=="sbsp") {
      var bsp=tag.ReadMetadata<ScenarioStructureBspTag>();
      foreach(var group in bsp.GeometryInstances.GroupBy(i=>i.SectionIndex)) {
       var instance=group.First(); assets.Add(new {tag=tag.TagName,kind="instance",name=instance.Name.ToString(),section=(int)instance.SectionIndex});
      }
     }
    }
    Save(output,new {version=1,map,assets});
   } else if(op=="bsp_diagnostics") {
    var tag=cache.TagIndex.First(t=>t.TagName==job.GetProperty("tag").GetString() && t.ClassCode=="sbsp");
    var bsp=tag.ReadMetadata<ScenarioStructureBspTag>();
    var details=new Dictionary<string,object?> { ["tag"]=tag.TagName,["clusters"]=bsp.Clusters.Count,["instances"]=bsp.GeometryInstances.Count,["sections"]=bsp.Sections.Count };
    try {var model=((IContentProvider<Model>)bsp).GetContent();details["meshes"]=model.Meshes.Count;details["placements"]=MapScene.Probe(model,Path.Combine(Path.GetDirectoryName(Path.GetFullPath(output))!,tag.FileName+"_preview"));details["ok"]=true;}
    catch(Exception e){details["ok"]=false;details["error"]=e.ToString();}
    Save(output,details);
   } else if(op=="map_scene") {
    if(reach)ReachMapScene.Export(cache,output);else MapScene.Export(cache,output);
   } else if(op=="material") {
    if(reach){ReachSupport.Material(cache,job.GetProperty("tag").GetString()!,output);return 0;}
    var tag=cache.TagIndex.First(t=>t.TagName==job.GetProperty("tag").GetString() && t.ClassCode.StartsWith("rm"));
    var method=typeof(ShaderBlock).Assembly.GetType("Reclaimer.Blam.Halo3.Halo3Common")!.GetMethod("GetMaterials")!;
    var materials=(IEnumerable<Material>)method.Invoke(null,new object[]{new[]{new ShaderBlock{ShaderReference=new TagReference(cache,tag.ClassId,tag.Id)}}})!;
    Save(Path.Combine(output,"preview.json"),new{version=1,materials=WriteMaterials(materials,output),meshes=Array.Empty<object>()});
   } else if(op=="extract") {
    var tagPath=job.GetProperty("tag").GetString();int section=job.GetProperty("section").GetInt32();
    var tag=cache.TagIndex.First(t=>t.TagName==tagPath && t.ClassCode==(section>=0?"sbsp":"mode"));
    if(!ContentFactory.TryGetGeometryContent(tag,out var provider))throw new Exception("Reclaimer cannot decode this geometry.");
    var scene=provider.GetContent(); var model=scene.EnumerateModels().First();
    if(section>=0) {
     foreach(var region in model.Regions) foreach(var p in region.Permutations) p.Export=false;
     var perm=model.Regions.SelectMany(r=>r.Permutations).First(p=>p.MeshIndices.Contains(section));
     perm.Export=true;perm.Transform=Matrix4x4.Identity;perm.Scale=Vector3.One;
    }
    var allParts=model.Regions.Where(r=>r.Export).SelectMany((r,ri)=>r.Permutations.Where(p=>p.Export).SelectMany((p,pi)=>p.MeshIndices.Select(i=>(index:i,region:r.Name,permutation:p.Name,choice:ri+":"+pi,perm:p)))).Where(p=>section<0||p.index==section).ToArray();
    Directory.CreateDirectory(output);scene.WriteRMF(Path.Combine(output,"asset.rmf"));
    var selection=section<0?ModelSelection.Apply(model):Array.Empty<object>();
    var used=section>=0?new[]{section}:allParts.Select(p=>p.index).Distinct().ToArray();
    var materialList=used.SelectMany(i=>model.Meshes[i]?.Segments ?? new()).Select(s=>s.Material).Where(m=>m!=null).DistinctBy(m=>m.Id).ToList();
    var warnings=new List<string>();
    var mats=WriteMaterials(materialList!,output,warnings,true);
    var meshes=new List<object>();
    var enabledMeshes=new List<object>();
    foreach(var part in allParts) {
     var i=part.index;
     var mesh=model.Meshes[i];if(mesh==null)continue;
     // Preserve the original model-space coordinates. Applying node transforms
     // again scattered already positioned rigid pieces in the previous build.
     var pos=mesh.GetPositions().Select(p=>V(Vector3.Transform(p,mesh.PositionBounds.CreateExpansionMatrix()))).ToArray();
     var uv=mesh.GetTexCoords()?.Select(p=>{var v=Vector2.Transform(p,mesh.TextureBounds.CreateExpansionMatrix());return new[]{v.X,1-v.Y};}).ToArray();
     var normals=mesh.GetNormals()?.Select(V).ToArray();
     var item=new {name="mesh_"+i,source_mesh=i,region=part.region,permutation=part.permutation,choice=part.choice,enabled=part.perm.Export,positions=pos,uv,normals,segments=mesh.Segments.Select(s=>new{material=s.Material?.Id??-1,indices=mesh.GetTriangleIndicies(s).ToArray()}).ToArray()};
     meshes.Add(item);if(part.perm.Export)enabledMeshes.Add(item);
    }
    if(section<0)Save(Path.Combine(output,"parts.json"),new{version=1,materials=mats,meshes});
    Save(Path.Combine(output,"preview.json"),new{version=1,tag=tagPath,section,units="halo",collision="missing",selection_policy=2,selection,warnings,materials=mats,meshes=enabledMeshes});
   } else throw new Exception("Unknown operation: "+op);
   Console.WriteLine(JsonSerializer.Serialize(new{version=1,ok=true,output}));return 0;
  } catch(Exception e){Console.Error.WriteLine(e);return 1;}
 }
 internal static List<object> WriteMaterials(IEnumerable<Material> materials,string output,List<string>? warnings=null,bool strictTextures=false) {
    Directory.CreateDirectory(output);var mats=new List<object>();
    foreach(var m in materials) {
     var textures=new List<object>();
     foreach(var tm in m.TextureMappings.Where(t=>t.Texture!=null && new[]{"diffuse","normal","transparency","blend","color_change","diffuse_detail"}.Contains(t.Usage))) {
      var tex=tm.Texture;var texName="texture_"+tex.Id+".png";var full=Path.Combine(output,texName);
      try {if(!File.Exists(full)||new FileInfo(full).Length==0) {var temp=full+".writing.png";try {tex.GetDds().WriteToDisk(temp,System.Drawing.Imaging.ImageFormat.Png);File.Move(temp,full,true);}finally {if(File.Exists(temp))File.Delete(temp);}}textures.Add(new{name=tex.Name,parameter=tm.Parameter,usage=tm.Usage,path=texName,tiling=new[]{tm.Tiling.X,tm.Tiling.Y},gamma=tex.Gamma,channels=(int)tm.ChannelMask,blend_channel=(int)tm.BlendChannel});}
      catch(Exception e) when(tm.Usage=="normal" && String.Equals(tex.Name,@"shaders\default_bitmaps\bitmaps\default_vector",StringComparison.OrdinalIgnoreCase) && e is IndexOutOfRangeException) {
       // A neutral tangent normal is represented by the unconnected Blender normal socket.
       Console.Error.WriteLine("Using a flat normal for the unavailable default_vector placeholder.");
      }
      catch(Exception e){Console.Error.WriteLine("Texture "+tex.Name+": "+e.Message);if(warnings==null || (strictTextures && tm.Usage!="normal"))throw;warnings.Add("Missing texture "+tex.Name+": "+e.Message);}
     }
     m.CustomProperties.TryGetValue("tag_name",out var shader);
     m.CustomProperties.TryGetValue("hb_source_game",out var sourceGame);
     var options=m.CustomProperties.Where(p=>p.Key.StartsWith("hb_option_")).ToDictionary(p=>p.Key.Substring(10),p=>p.Value?.ToString());
     mats.Add(new{id=m.Id,name=m.Name,shader=shader?.ToString()??"",alpha=m.AlphaMode,source_game=sourceGame?.ToString(),options,tints=m.Tints.Select(t=>new{usage=t.Usage,blend_channel=(int)t.BlendChannel,color=new[]{t.Color.R/255f,t.Color.G/255f,t.Color.B/255f,t.Color.A/255f}}).ToArray(),textures});
    }
    return mats;
 }
}


