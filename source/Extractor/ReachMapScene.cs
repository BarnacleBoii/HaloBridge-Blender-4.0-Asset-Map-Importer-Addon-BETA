using System.Numerics;
using System.Text.Json;
using Reclaimer.Blam.Common;
using Reclaimer.Blam.HaloReach;
using Reclaimer.Geometry;
using Reclaimer.Utilities;

// Preserve Halo world coordinates. System.Numerics uses row-vector matrices;
// the Blender reader transposes these matrices exactly once.
internal sealed class ReachMapScene {
 readonly string output;
 readonly List<string> warnings=new();
 readonly List<object> placements=new();
 readonly Dictionary<string,string> meshes=new();
 readonly Dictionary<int,object> materials=new();
 readonly Dictionary<string,Model> models=new();
 readonly Dictionary<string,int> counts=new();
 int expectedBsps,decodedBsps;
 ReachMapScene(string output) {this.output=output;Directory.CreateDirectory(output);}
 static float[] V(Vector3 v)=>new[]{v.X,v.Y,v.Z};
 static float[][] M(Matrix4x4 m)=>new[]{new[]{m.M11,m.M12,m.M13,m.M14},new[]{m.M21,m.M22,m.M23,m.M24},new[]{m.M31,m.M32,m.M33,m.M34},new[]{m.M41,m.M42,m.M43,m.M44}};
 void Save(string name,object value)=>File.WriteAllText(Path.Combine(output,name),JsonSerializer.Serialize(value));
 internal static int Probe(Model model,string folder) {var writer=new ReachMapScene(folder);writer.AddModel(model,Matrix4x4.Identity,"Terrain",model.OriginalPath,true);return writer.placements.Count;}
 void Progress(string message) {var temp=Path.Combine(output,"progress.tmp");File.WriteAllText(temp,JsonSerializer.Serialize(new{message}));File.Move(temp,Path.Combine(output,"progress.json"),true);}

 internal static void Export(ICacheFile cache,string output) {
  var writer=new ReachMapScene(output);
  var tag=cache.TagIndex.GetGlobalTag("scnr");
  var scenario=tag.ReadMetadata<ScenarioTag>();
  writer.expectedBsps=scenario.StructureBsps.Count;
  foreach(var block in scenario.StructureBsps) {
   var bsp=block.BspReference.Tag;
   try {
    writer.Progress("Reading terrain and BSP instances: "+bsp.TagName);
    var model=((IContentProvider<Model>)bsp.ReadMetadata<ScenarioStructureBspTag>()).GetContent();
    writer.AddModel(model,Matrix4x4.Identity,"Terrain",bsp.TagName,true);
    writer.decodedBsps++;
   } catch(Exception e) {writer.warnings.Add("BSP "+bsp?.TagName+": "+e.Message);Console.Error.WriteLine("BSP "+bsp?.TagName+": "+e);}
  }
  if(writer.decodedBsps==0)throw new Exception("No terrain BSP could be decoded. "+string.Join("; ",writer.warnings));
  writer.AddPlacements<SceneryTag,SceneryPlacementBlock>(scenario.SceneryPalette,scenario.Scenery,"Scenery");
  writer.AddPlacements<DeviceMachineTag,MachinePlacementBlock>(scenario.MachinePalette,scenario.Machines,"Machines");
  writer.AddPlacements<DeviceControlTag,ControlPlacementBlock>(scenario.ControlPalette,scenario.Controls,"Controls");
  writer.AddPlacements<CrateTag,CratePlacementBlock>(scenario.CratePalette,scenario.Crates,"Crates");
  foreach(var sky in scenario.Skies??Enumerable.Empty<SkyReferenceBlock>()) {
   try {
    var skyTag=sky.SkyReference.Tag;
    var model=((IContentProvider<Model>)skyTag.ReadMetadata<SceneryTag>().ReadRenderModel()).GetContent();
    writer.AddModel(model,Matrix4x4.Identity,"Skies",skyTag.TagName,false);
   } catch(Exception e) {writer.warnings.Add("Sky: "+e.Message);}
  }
  writer.Save("scene.json",new{version=1,kind="halo3_map_scene",game="reach",scenario=tag.TagName,units="halo",matrix_convention="row_vector",expected_bsps=writer.expectedBsps,decoded_bsps=writer.decodedBsps,
   meshes=writer.meshes,placements=writer.placements,counts=writer.counts,warnings=writer.warnings.Distinct().ToArray(),
   limitations=new[]{"Static visual layout only; not a reconstructed playable scenario.","AI, player starts, weapons, vehicles, scripts, triggers, animated device state, baked lighting and original collision are not imported.","Variant selection is approximated when multiple render permutations exist; affected assets are reported.","All BSPs are imported together, including campaign areas normally streamed separately."}});
  writer.Progress("Map scene extracted: "+writer.placements.Count+" mesh placements");
 }

 // Halo: CE and Halo 2: Reclaimer builds the whole scenario as a Scene (BSPs,
 // skies and object placements), which is written in the same scene.json format.
 internal static void ExportScene(ICacheFile cache,string game,string output) {
  var writer=new ReachMapScene(output);
  var tag=cache.TagIndex.GetGlobalTag("scnr");
  writer.Progress("Reading the scenario: "+tag.TagName);
  if(!ContentFactory.TryGetPrimaryContent(tag,out var content) || content is not IContentProvider<Scene> provider)throw new Exception("Reclaimer cannot read this scenario.");
  var scene=provider.GetContent();
  var categories=new Dictionary<string,string>{["scenario_structure_bsps"]="Terrain",["skies"]="Skies",["scenery"]="Scenery",["device_machines"]="Machines",["device_controls"]="Controls",["crates"]="Crates"};
  foreach(var top in scene.ChildGroups) {
   var category=categories.GetValueOrDefault(top.Name,top.Name);bool bsp=category=="Terrain";
   if(bsp)writer.expectedBsps+=top.ChildObjects.Count;
   foreach(var group in top.EnumerateHierarchy()) {
    int number=0;
    foreach(var item in group.ChildObjects) {
     try {
      if(item.Object is not Model model)continue;
      var transform=item.Transform;
      writer.Progress("Reading "+category+": "+model.OriginalPath);
      writer.AddModel(model,transform,category,(model.OriginalPath??model.Name)+(bsp?"":" #"+number++),bsp);
      if(bsp)writer.decodedBsps++;
     } catch(Exception e) {writer.warnings.Add(category+": "+e.Message);}
    }
   }
  }
  if(writer.decodedBsps==0)throw new Exception("No terrain BSP could be decoded. "+string.Join("; ",writer.warnings));
  writer.Save("scene.json",new{version=1,kind="halo3_map_scene",game,scenario=tag.TagName,units="halo",matrix_convention="row_vector",expected_bsps=writer.expectedBsps,decoded_bsps=writer.decodedBsps,
   meshes=writer.meshes,placements=writer.placements,counts=writer.counts,warnings=writer.warnings.Distinct().ToArray(),
   limitations=new[]{"Static visual layout only; not a reconstructed playable scenario.","AI, player starts, weapons, vehicles, scripts, triggers, animated device state, baked lighting and original collision are not imported.","Variant selection is approximated when multiple render permutations exist; affected assets are reported.","All BSPs are imported together."}});
  writer.Progress("Map scene extracted: "+writer.placements.Count+" mesh placements");
 }

 void AddPlacements<TTag,TPlacement>(IEnumerable<ObjectPaletteBlock>? palette,IEnumerable<TPlacement>? instances,string category)
  where TTag:ObjectTag where TPlacement:ObjectPlacementBlockBase {
  if(palette==null||instances==null)return;
  var table=palette.ToArray();int index=0;
  foreach(var instance in instances) {
   var number=index++;
   try {
    var reference=table.ElementAtOrDefault(instance.PaletteIndex)?.TagReference;
    if(reference==null||!reference.Value.IsValid) {warnings.Add(category+" placement "+number+": invalid palette reference");continue;}
    var tag=reference.Value.Tag;
    Progress("Reading "+category+" placement "+number+": "+tag.TagName);
    if(!models.TryGetValue(tag.TagName,out var model)) {
     model=((IContentProvider<Model>)tag.ReadMetadata<TTag>().ReadRenderModel()).GetContent();models[tag.TagName]=model;
    }
    var scale=instance.Scale==0?1:instance.Scale;
    var transform=Matrix4x4.CreateScale(scale)*Matrix4x4.CreateFromQuaternion((Quaternion)instance.Rotation)*Matrix4x4.CreateTranslation(instance.Position.ToVector3());
    AddModel(model,transform,category,tag.TagName+" #"+number,false);
   } catch(Exception e) {warnings.Add(category+" placement "+number+": "+e.Message);}
  }
 }

 void AddModel(Model model,Matrix4x4 transform,string category,string label,bool bsp) {

  foreach(var region in model.Regions.Where(r=>r.Export)) {
   var permutations=region.Permutations.Where(p=>p.Export).ToArray();
   if(!bsp&&permutations.Length>1&&!permutations.All(p=>p.IsInstanced)) {
    warnings.Add("Variant approximation: "+model.OriginalPath+" / "+region.Name+"; using default or first permutation.");
    permutations=new[]{permutations.FirstOrDefault(p=>p.Name=="default")??permutations[0]};
   }
   foreach(var permutation in permutations)foreach(var index in permutation.MeshIndices) {
    var mesh=model.Meshes.ElementAtOrDefault(index);if(mesh==null)continue;
    var key=model.OriginalPath+"|"+index;
    if(!meshes.TryGetValue(key,out var file)) {
     file="mesh_"+meshes.Count+".json";
     var mats=mesh.Segments.Select(s=>s.Material).Where(m=>m!=null).DistinctBy(m=>m.Id).ToArray();
     foreach(var mat in mats)if(!materials.ContainsKey(mat.Id))materials[mat.Id]=Program.WriteMaterials(new[]{mat},output,warnings)[0];
     var bone=mesh.BoneIndex.HasValue?model.GetBoneWorldTransform(mesh.BoneIndex.Value):Matrix4x4.Identity;
     if(mesh.VertexBuffer.HasBlendWeights)warnings.Add("Bind-pose geometry (no animation): "+model.OriginalPath);
     var positions=mesh.GetPositions().Select(p=>V(Vector3.Transform(Vector3.Transform(p,mesh.PositionBounds.CreateExpansionMatrix()),bone))).ToArray();
     var uv=mesh.GetTexCoords()?.Select(p=>{var v=Vector2.Transform(p,mesh.TextureBounds.CreateExpansionMatrix());return new[]{v.X,1-v.Y};}).ToArray();
     Matrix4x4.Invert(bone,out var inverseBone);var normalMatrix=Matrix4x4.Transpose(inverseBone);
     var normals=mesh.GetNormals()?.Select(n=>V(Vector3.Normalize(Vector3.TransformNormal(n,normalMatrix)))).ToArray();
     Save(file,new{version=1,materials=mats.Select(m=>materials[m.Id]).ToArray(),meshes=new[]{new{positions,uv,normals,segments=mesh.Segments.Select(s=>new{material=s.Material?.Id??-1,indices=mesh.GetTriangleIndicies(s).ToArray()}).ToArray()}}});
     meshes[key]=file;
    }
    var group=bsp&&permutation.IsInstanced?"BSP instances":category;
    placements.Add(new{name=label+" / "+region.Name+" / "+permutation.Name,mesh=key,group,source_tag=model.OriginalPath,matrix=M(permutation.GetFinalTransform()*transform)});
    counts[group]=counts.GetValueOrDefault(group)+1;
   }
  }
 }
}
