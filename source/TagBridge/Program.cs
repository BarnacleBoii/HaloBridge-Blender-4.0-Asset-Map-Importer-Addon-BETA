using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Web.Script.Serialization;
using System.Security.Cryptography;
using Bungie;
using Bungie.Tags;

class Job { public int version,section; public string operation,kit,scenario,output,template,asset_name; public string[] sources; public float[] position; public ShaderImport[] shaders; public Placement[] placements; public Dictionary<string,string> previous; }
class ShaderImport { public string path,base_map,normal_map,alpha_map; }
class Placement { public string id,tag; public float[] position,rotation; public float scale=1; }
class Program {
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode)] static extern bool SetDllDirectory(string p);
 static string kit; static JavaScriptSerializer js=new JavaScriptSerializer {MaxJsonLength=int.MaxValue};
 static int Main(string[] args) {try {
  var j=js.Deserialize<Job>(File.ReadAllText(args[0])); if(j.version!=1)throw new Exception("Unsupported job version");
  kit=Path.GetFullPath(j.kit);SetDllDirectory(kit);Environment.CurrentDirectory=kit;
  AppDomain.CurrentDomain.AssemblyResolve+=(s,e)=>{string p=Path.Combine(kit,"bin",new AssemblyName(e.Name).Name+".dll");return File.Exists(p)?Assembly.LoadFrom(p):null;};
  Assembly.GetExecutingAssembly().GetType("TagOps").GetMethod("Run").Invoke(null,new object[]{j});return 0;
 }catch(Exception e){Console.Error.WriteLine(e);return 1;}}
}
class TagOps {
 static string kit; static JavaScriptSerializer js=new JavaScriptSerializer {MaxJsonLength=int.MaxValue};
 static T F<T>(TagField[] fields,string name) where T:TagField {return (T)fields.Single(f=>f.FieldName==name);}
 static TagField[] S(TagField[] fields,string name){return F<TagFieldStruct>(fields,name).Elements[0].Fields;}
 static string Hash(TagFieldBlock b,int i){using(var h=SHA256.Create())return Convert.ToBase64String(h.ComputeHash(b.SerializeElement(i)));}
 static string Safe(string p){if(String.IsNullOrWhiteSpace(p)||Path.IsPathRooted(p)||p.Split('\\','/').Any(x=>x==".."))throw new Exception("Invalid relative tag path");return p.Replace('/','\\');}
 [MethodImpl(MethodImplOptions.NoInlining)] public static void Run(Job j) {
  kit=Path.GetFullPath(j.kit);
  ManagedBlamSystem.InitializeProject(InitializationType.TagsOnly,kit);
  if(j.operation=="prepare_bitmaps") { PrepareBitmaps(j);return; }
  if(j.operation=="import_shaders") { ImportShaders(j);return; }
  if(j.operation=="list_skies") { ListSkies(j);return; }
  if(j.operation=="recover_source") { RecoverSource(j);return; }
  if(j.operation=="collision") { Collision(j);return; }
  if(j.operation=="inspect_bsp") { InspectBsp(j);return; }
  if(j.operation=="resolve_scenery") { ResolveScenery(j);return; }
  if(j.operation=="copy_level") { CopyLevel(j);return; }
  if(j.operation=="verify_base") { VerifyCopiedScenario(Safe(j.template),Safe(j.scenario),true);File.WriteAllText(j.output,js.Serialize(new{version=1,ok=true,original_gameplay_verified=true}));return; }
  if(j.operation=="verify_copy") { VerifyCopiedScenario(Safe(j.template),Safe(j.scenario));File.WriteAllText(j.output,js.Serialize(new{version=1,ok=true,scenario_data_verified=true}));return; }
  var path=TagPath.FromPathAndType(Safe(j.scenario),"scnr*");
  using(var tag=new TagFile(path)) {
   var scenery=F<TagFieldBlock>(tag.Fields,"scenery");var palette=F<TagFieldBlock>(tag.Fields,"scenery palette");var names=F<TagFieldBlock>(tag.Fields,"object names");
   var owned=new Dictionary<string,int>();
   for(int i=0;i<scenery.Elements.Count;i++) {int ni=F<TagFieldBlockIndex>(scenery.Elements[i].Fields,"name").Value;if(ni>=0 && ni<names.Elements.Count) {string n=F<TagFieldElementStringNormal>(names.Elements[ni].Fields,"name").Data;if(n.StartsWith("hb_")){if(owned.ContainsKey(n))throw new Exception("Duplicate managed placement name: "+n);owned[n]=i;}}}
   if(j.operation=="sync") {
    var prev=j.previous??new Dictionary<string,string>();
    foreach(var pair in prev) if(!owned.ContainsKey(pair.Key)||Hash(scenery,owned[pair.Key])!=pair.Value)throw new Exception("CONFLICT: Sapien changed or removed Blender placement "+pair.Key+". Restore it or explicitly resolve ownership before exporting.");
    foreach(var pair in owned)if(!prev.ContainsKey(pair.Key))throw new Exception("CONFLICT: Untracked Blender placement "+pair.Key);
    var placements=j.placements??new Placement[0];
    if(placements.Select(p=>p.id).Distinct().Count()!=placements.Length)throw new Exception("Duplicate placement IDs");
    foreach(var p in placements) {if(!p.id.StartsWith("hb_")||p.id.Length>31||p.position.Length!=3||p.rotation.Length!=3||p.scale<=0||p.position.Concat(p.rotation).Concat(new[]{p.scale}).Any(x=>float.IsNaN(x)||float.IsInfinity(x)))throw new Exception("Invalid placement");if(!File.Exists(Path.Combine(kit,"tags",Safe(p.tag)+".scenery")))throw new Exception("Missing scenery tag: "+p.tag);}
    var wanted=new HashSet<string>(placements.Select(p=>p.id));
    foreach(var pair in owned.Where(p=>!wanted.Contains(p.Key)).OrderByDescending(p=>p.Value)) {int ni=F<TagFieldBlockIndex>(scenery.Elements[pair.Value].Fields,"name").Value;scenery.RemoveElement(pair.Value);F<TagFieldBlockIndex>(names.Elements[ni].Fields,"scenario_datum_index").Value=-1;}
    owned.Clear();
    for(int i=0;i<scenery.Elements.Count;i++){int ni=F<TagFieldBlockIndex>(scenery.Elements[i].Fields,"name").Value;if(ni>=0 && ni<names.Elements.Count)owned[F<TagFieldElementStringNormal>(names.Elements[ni].Fields,"name").Data]=i;}
    foreach(var p in placements) {
     int pi=-1;for(int i=0;i<palette.Elements.Count;i++){var r=F<TagFieldReference>(palette.Elements[i].Fields,"name").Path;if(r!=null && r.RelativePath.Equals(p.tag,StringComparison.OrdinalIgnoreCase))pi=i;}
     if(pi<0){pi=palette.Elements.Count;F<TagFieldReference>(palette.AddElement().Fields,"name").Path=TagPath.FromPathAndType(Safe(p.tag),"scen*");}
     int si;TagField[] f;
     if(owned.TryGetValue(p.id,out si))f=scenery.Elements[si].Fields;
     else {si=scenery.Elements.Count;f=scenery.AddElement().Fields;int ni=names.Elements.Count;var nf=names.AddElement().Fields;F<TagFieldElementStringNormal>(nf,"name").Data=p.id;F<TagFieldBlockIndex>(nf,"object_type").Value=6;F<TagFieldBlockIndex>(nf,"scenario_datum_index").Value=si;F<TagFieldBlockIndex>(f,"name").Value=ni;
      var d=S(f,"object data");var oid=S(d,"object id");F<TagFieldElementInteger>(oid,"unique id").Data=Convert.ToInt32(p.id.Substring(3,7),16);F<TagFieldEnum>(oid,"type").Value=6;F<TagFieldEnum>(oid,"source").Value=1;F<TagFieldBlockIndex>(oid,"origin bsp index").Value=-1;
     }
     F<TagFieldBlockIndex>(f,"type").Value=pi;var data=S(f,"object data");F<TagFieldElementArraySingle>(data,"position").Data=p.position;F<TagFieldElementArraySingle>(data,"rotation").Data=p.rotation;F<TagFieldElementSingle>(data,"scale").Data=p.scale;
    }
    // Reconcile name indices after scenery deletions, including Sapien-owned names.
    for(int i=0;i<scenery.Elements.Count;i++){int ni=F<TagFieldBlockIndex>(scenery.Elements[i].Fields,"name").Value;if(ni>=0)F<TagFieldBlockIndex>(names.Elements[ni].Fields,"scenario_datum_index").Value=i;}
    tag.Save();
   } else if(j.operation=="ensure_spawn") {
    var starts=F<TagFieldBlock>(tag.Fields,"player starting locations");
    if(starts.Elements.Count==0) {
     if(j.position==null || j.position.Length!=3 || j.position.Any(x=>Single.IsNaN(x)||Single.IsInfinity(x)))throw new Exception("Invalid test spawn position");
     starts.AddElement();var fields=starts.Elements[0].Fields;
     F<TagFieldElementArraySingle>(fields,"position").Data=j.position;
     F<TagFieldElementInteger>(fields,"bsp index").Data=0;
     tag.Save();
    }
   } else if(j.operation=="environment") {
    using(var donor=new TagFile(TagPath.FromPathAndType(Safe(j.template),"scnr*"))) {
     var originalSkies=F<TagFieldBlock>(donor.Fields,"skies");var destinationSkies=F<TagFieldBlock>(tag.Fields,"skies");
     if(originalSkies.Elements.Count==0)throw new Exception("The chosen map has no sky references.");
     var chosen=AllReferences(originalSkies.Elements[0].Fields).FirstOrDefault(r=>r.Path!=null);
     if(chosen==null || !File.Exists(chosen.Path.Filename))throw new Exception("The chosen map sky tag is missing.");
     if(destinationSkies.Elements.Count==0) {
      while(originalSkies.Elements.Count>1)originalSkies.RemoveElement(originalSkies.Elements.Count-1);
      destinationSkies.DeserializeEntireBlock(originalSkies.SerializeEntireBlock());
     } else {
      // Keep existing slots/BSP masks so all BSP sky indices stay valid.
      foreach(var element in destinationSkies.Elements) {
       var reference=AllReferences(element.Fields).Single(r=>r.FieldName==chosen.FieldName);reference.Path=chosen.Path;
      }
     }
    }tag.Save();
   } else if(j.operation!="inspect")throw new Exception("Unknown operation");
  }
  using(var tag=new TagFile(path)) {
   var scenery=F<TagFieldBlock>(tag.Fields,"scenery");var names=F<TagFieldBlock>(tag.Fields,"object names");var state=new Dictionary<string,string>();var items=new List<object>();
   for(int i=0;i<scenery.Elements.Count;i++){var f=scenery.Elements[i].Fields;int ni=F<TagFieldBlockIndex>(f,"name").Value;string n=ni>=0?F<TagFieldElementStringNormal>(names.Elements[ni].Fields,"name").Data:"";if(n.StartsWith("hb_"))state[n]=Hash(scenery,i);var d=S(f,"object data");items.Add(new{name=n,position=F<TagFieldElementArraySingle>(d,"position").Data,rotation=F<TagFieldElementArraySingle>(d,"rotation").Data,scale=F<TagFieldElementSingle>(d,"scale").Data});}
   var spawns=F<TagFieldBlock>(tag.Fields,"player starting locations");
   File.WriteAllText(j.output,js.Serialize(new{version=1,ok=true,state=state,placements=items,scenery_count=scenery.Elements.Count,skies=AllReferences(F<TagFieldBlock>(tag.Fields,"skies").Elements.Cast<TagElement>().SelectMany(e=>e.Fields).ToArray()).Where(r=>r.Path!=null).Select(r=>r.Path.RelativePathWithExtension).ToArray(),spawn_count=spawns.Elements.Count,spawns=Convert.ToBase64String(spawns.SerializeEntireBlock())}));Console.WriteLine("Scenario tags verified");
  }
 }
 static void PrepareBitmaps(Job j) {
  string prefix=Path.GetDirectoryName(Safe(j.scenario))+"\\bitmaps\\reach\\";
  foreach(var item in j.shaders??new ShaderImport[0])foreach(var pair in new Dictionary<string,string>{{"base",item.base_map},{"normal",item.normal_map},{"alpha",item.alpha_map}}) {
   if(String.IsNullOrEmpty(pair.Value))continue;
   string target=Safe(pair.Value);
   if(!target.StartsWith(prefix,StringComparison.OrdinalIgnoreCase))throw new Exception("Converted bitmap is outside this level.");
   var path=TagPath.FromPathAndType(target,"bitm");
   using(var tag=new TagFile()) {
    if(File.Exists(Path.Combine(kit,"tags",target+".bitmap")))tag.Load(path);else tag.New(path);
    F<TagFieldEnum>(tag.Fields,"Usage").Value=pair.Key=="normal"?13:pair.Key=="alpha"?18:0;
    F<TagFieldEnum>(tag.Fields,"force bitmap format").Value=2;
    F<TagFieldEnum>(tag.Fields,"curve mode").Value=pair.Key=="base"?2:1;
    Directory.CreateDirectory(Path.GetDirectoryName(Path.Combine(kit,"tags",target)));
    tag.Save();
   }
  }
  File.WriteAllText(j.output,js.Serialize(new{version=1,ok=true}));
 }
 static void ImportShaders(Job j) {
  string prefix=Path.GetDirectoryName(Safe(j.scenario))+"\\shaders\\";
  var verified=new List<object>();
  foreach(var item in j.shaders??new ShaderImport[0]) {
   string target=Safe(item.path);
   if(!target.StartsWith(prefix,StringComparison.OrdinalIgnoreCase))throw new Exception("Generated shader is outside this level.");
   using(var tag=new TagFile(TagPath.FromPathAndType("shaders\\invalid","rmsh"))) {
    var fields=S(tag.Fields,"render_method");
    var options=F<TagFieldBlock>(fields,"options");
    for(int i=0;i<options.Elements.Count;i++)F<TagFieldElementInteger>(options.Elements[i].Fields,"short").Data=0;
    F<TagFieldElementInteger>(options.Elements[1].Fields,"short").Data=String.IsNullOrEmpty(item.normal_map)?0:1;
    F<TagFieldElementInteger>(options.Elements[2].Fields,"short").Data=String.IsNullOrEmpty(item.alpha_map)?0:1;
    F<TagFieldElementInteger>(options.Elements[9].Fields,"short").Data=1;
    var parameters=F<TagFieldBlock>(fields,"parameters");while(parameters.Elements.Count>0)parameters.RemoveElement(parameters.Elements.Count-1);
    var maps=new Dictionary<string,string>{{"base_map",item.base_map},{"bump_map",item.normal_map},{"alpha_test_map",item.alpha_map}};
    foreach(var pair in maps) {
     if(String.IsNullOrEmpty(pair.Value))continue;
     string bitmap=Safe(pair.Value);
     if(!File.Exists(Path.Combine(kit,"tags",bitmap+".bitmap")))throw new Exception("Converted bitmap missing: "+bitmap);
     var f=parameters.AddElement().Fields;
     F<TagFieldElementStringID>(f,"parameter name").Data=pair.Key;
     F<TagFieldEnum>(f,"parameter type").Value=0;
     F<TagFieldReference>(f,"bitmap").Path=TagPath.FromPathAndType(bitmap,"bitm");
    }
    Directory.CreateDirectory(Path.GetDirectoryName(Path.Combine(kit,"tags",target)));
    tag.SaveAs(TagPath.FromPathAndType(target,"rmsh"));
   }
   using(var tag=new TagFile(TagPath.FromPathAndType(target,"rmsh"))) {
    var references=AllReferences(tag.Fields).Where(r=>r.Path!=null).Select(r=>r.Path.RelativePathWithExtension).ToArray();
    if(!references.Contains(item.base_map+".bitmap"))throw new Exception("Generated shader lost its base texture.");
    verified.Add(new{shader=target,references=references});
   }
  }
  File.WriteAllText(j.output,js.Serialize(new{version=1,ok=true,shaders=verified}));
 }
 static long I(TagField[] f,string name){return F<TagFieldElementInteger>(f,name).Data;}
 static IEnumerable<TagFieldReference> References(TagField[] fields) {
  foreach(var f in fields) {
   var reference=f as TagFieldReference;if(reference!=null)yield return reference;
   var structure=f as TagFieldStruct;
   if(structure!=null)foreach(var e in structure.Elements)foreach(var r in References(e.Fields))yield return r;
  }
 }
 static IEnumerable<TagFieldReference> AllReferences(TagField[] fields) {
  foreach(var field in fields) {
   var reference=field as TagFieldReference;if(reference!=null)yield return reference;
   var structure=field as TagFieldStruct;
   if(structure!=null)foreach(var e in structure.Elements)foreach(var r in AllReferences(e.Fields))yield return r;
   var block=field as TagFieldBlock;
   if(block!=null)foreach(var e in block.Elements)foreach(var r in AllReferences(e.Fields))yield return r;
  }
 }
 static string Remap(string path,string source,string target) {
  if(path.Equals(source,StringComparison.OrdinalIgnoreCase))return target;
  string oldRoot=Path.GetDirectoryName(source)+"\\",newRoot=Path.GetDirectoryName(target)+"\\";
  return path.StartsWith(oldRoot,StringComparison.OrdinalIgnoreCase)?newRoot+path.Substring(oldRoot.Length):path;
 }
 static string Digest(byte[] data) {using(var h=SHA256.Create())return Convert.ToBase64String(h.ComputeHash(data));}
 static void VerifyCopiedScenario(string source,string target,bool allowAddedScenery=false) {
  using(var original=new TagFile(TagPath.FromPathAndType(source,"scnr*")))
  using(var copy=new TagFile(TagPath.FromPathAndType(target,"scnr*"))) {
   foreach(var reference in AllReferences(copy.Fields)) {
    if(reference.Path==null)continue;
    var old=reference.Path;string normalized=Remap(old.RelativePath,target,source);
    if(normalized!=old.RelativePath)reference.Path=TagPath.FromPathAndType(normalized,old.Type);
   }
   if(allowAddedScenery) {
    foreach(string name in new[]{"scenery","scenery palette","object names"}) {
     var before=F<TagFieldBlock>(original.Fields,name);var after=F<TagFieldBlock>(copy.Fields,name);
     if(after.Elements.Count<before.Elements.Count)throw new Exception("Original "+name+" entries were removed.");
     for(int i=0;i<before.Elements.Count;i++)if(Digest(before.SerializeElement(i))!=Digest(after.SerializeElement(i)))throw new Exception("Original "+name+" entry changed: "+i);
     after.DeserializeEntireBlock(before.SerializeEntireBlock());
    }
    F<TagFieldBlock>(copy.Fields,"skies").DeserializeEntireBlock(F<TagFieldBlock>(original.Fields,"skies").SerializeEntireBlock());
   }
   // Halo's save postprocessor sorts firing positions within AI zones and
   // recomputes derived area statistics. Verify those exact point multisets,
   // tolerate only tiny derived-stat rounding, then normalize in memory only.
   var oz=original.Fields.OfType<TagFieldBlock>().Single(b=>b.FieldName=="zones");
   var cz=copy.Fields.OfType<TagFieldBlock>().Single(b=>b.FieldName=="zones");
   if(oz.Elements.Count!=cz.Elements.Count)throw new Exception("AI zone count changed.");
   for(int i=0;i<oz.Elements.Count;i++) {
    var op=F<TagFieldBlock>(oz.Elements[i].Fields,"firing positions");var cp=F<TagFieldBlock>(cz.Elements[i].Fields,"firing positions");
    var left=Enumerable.Range(0,op.Elements.Count).Select(n=>Digest(op.SerializeElement(n))).OrderBy(x=>x).ToArray();
    var right=Enumerable.Range(0,cp.Elements.Count).Select(n=>Digest(cp.SerializeElement(n))).OrderBy(x=>x).ToArray();
    if(!left.SequenceEqual(right))throw new Exception("AI firing-position data changed in zone "+i);
    cp.DeserializeEntireBlock(op.SerializeEntireBlock());
    var oa=F<TagFieldBlock>(oz.Elements[i].Fields,"areas");var ca=F<TagFieldBlock>(cz.Elements[i].Fields,"areas");
    if(oa.Elements.Count!=ca.Elements.Count)throw new Exception("AI area count changed.");
    for(int n=0;n<oa.Elements.Count;n++)foreach(var field in oa.Elements[n].Fields.Where(f=>f.FieldName.StartsWith("runtime "))) {
     var other=ca.Elements[n].Fields.Single(f=>f.FieldName==field.FieldName && f.GetType()==field.GetType());
     var number=field as TagFieldElementSingle;
     if(number!=null) {var value=(TagFieldElementSingle)other;if(Math.Abs(number.Data-value.Data)>0.0001f)throw new Exception("AI runtime statistic changed beyond rounding tolerance.");value.Data=number.Data;}
     var vector=field as TagFieldElementArraySingle;
     if(vector!=null) {var value=(TagFieldElementArraySingle)other;if(vector.Data.Length!=value.Data.Length || vector.Data.Zip(value.Data,(a,b)=>Math.Abs(a-b)).Any(d=>d>0.0001f))throw new Exception("AI runtime vector changed beyond rounding tolerance.");value.Data=vector.Data;}
    }
   }
   if(Digest(original.Serialize())!=Digest(copy.Serialize()))throw new Exception("Copied scenario data changed beyond relocated references and verified AI save normalization.");
  }
 }
 static void CopyLevel(Job j) {
  string source=Safe(j.template),target=Safe(j.scenario),root=Path.Combine(kit,"tags");
  string parent=Path.GetDirectoryName(target),leaf=Path.GetFileName(target);
  if(parent!="levels\\multi\\"+leaf || leaf.Length<3 || leaf.Length>32 || leaf.Any(c=>!(c>='a'&&c<='z')&&!(c>='0'&&c<='9')&&c!='_'))throw new Exception("Copy destination must be a new HaloBridge level namespace.");
  string srcRoot=Path.GetFullPath(Path.Combine(root,Path.GetDirectoryName(source))),dstRoot=Path.GetFullPath(Path.Combine(root,parent));
  if(!srcRoot.StartsWith(Path.GetFullPath(root)+"\\",StringComparison.OrdinalIgnoreCase) || dstRoot.StartsWith(srcRoot+"\\",StringComparison.OrdinalIgnoreCase) || srcRoot.Equals(dstRoot,StringComparison.OrdinalIgnoreCase))throw new Exception("Invalid source/destination relationship.");
  if(!File.Exists(Path.Combine(root,source+".scenario")))throw new Exception("The original editable scenario is missing. Extract the Editing Kit tag archives first: "+source);
  if(Directory.Exists(dstRoot))throw new Exception("The destination level already exists. Choose a new output level name.");
  var files=Directory.GetFiles(srcRoot,"*",SearchOption.AllDirectories);
  var hashes=new Dictionary<string,string>();var copied=new List<string>();var missing=new HashSet<string>();var bytePreserved=new List<string>();int redirected=0,verified=0;
  foreach(var file in files) {
   if((File.GetAttributes(file)&FileAttributes.ReparsePoint)!=0)throw new Exception("Linked source files are not supported: "+file);
   string relative=file.Substring(root.Length+1);string sourceTag=relative.Substring(0,relative.Length-Path.GetExtension(file).Length);
   string destination=Path.Combine(root,Remap(sourceTag,source,target)+Path.GetExtension(file));
   if(!Path.GetFullPath(destination).StartsWith(dstRoot+"\\",StringComparison.OrdinalIgnoreCase))throw new Exception("Copy escaped the destination namespace.");
   hashes[file]=Digest(File.ReadAllBytes(file));Directory.CreateDirectory(Path.GetDirectoryName(destination));File.Copy(file,destination,false);copied.Add(destination);
  }
  for(int i=0;i<copied.Count;i++) {
   string file=copied[i];File.WriteAllText(j.output+".progress.json",js.Serialize(new{message="Verifying copied level tags "+(i+1)+"/"+copied.Count+": "+Path.GetFileName(file)}));
   // This installed ManagedBlam cannot enumerate RealSlider fields in camera
   // settings. Preserve these opaque tags byte-for-byte, only when no original
   // level path occurs in either supported tag-string encoding.
   if(Path.GetExtension(file)==".camera_fx_settings") {
    var bytes=File.ReadAllBytes(file);string prefix=Path.GetDirectoryName(source)+"\\";
    if(System.Text.Encoding.UTF8.GetString(bytes).IndexOf(prefix,StringComparison.OrdinalIgnoreCase)>=0 || System.Text.Encoding.Unicode.GetString(bytes).IndexOf(prefix,StringComparison.OrdinalIgnoreCase)>=0)throw new Exception("Camera settings contain level-local paths that this ManagedBlam cannot safely relocate: "+file);
    bytePreserved.Add(file.Substring(root.Length+1));continue;
   }
   // Byte-identical copies retain embedded resource streams; only referenced
   // paths inside the original level namespace are changed through ManagedBlam.
   using(var tag=new TagFile(TagPath.FromFilename(file))) {
    string before=Digest(tag.Serialize());bool changed=false;
    var changedRefs=new List<Tuple<TagFieldReference,TagPath>>();
    foreach(var reference in AllReferences(tag.Fields)) {
     if(reference.Path==null)continue;
     var old=reference.Path;string replacement=Remap(old.RelativePath,source,target);
     if(replacement==old.RelativePath)continue;
     if(!File.Exists(Path.Combine(root,replacement+Path.GetExtension(old.RelativePathWithExtension)))) {
      if(File.Exists(old.Filename))throw new Exception("A source dependency was not copied: "+old.RelativePathWithExtension);
      missing.Add(old.RelativePathWithExtension);continue; // Retain original dangling references, never invent replacement tags.
     }
     reference.Path=TagPath.FromPathAndType(replacement,old.Type);changedRefs.Add(Tuple.Create(reference,old));changed=true;redirected++;
    }
    if(changed)tag.Save();
    foreach(var pair in changedRefs)pair.Item1.Path=pair.Item2;
    if(Digest(tag.Serialize())!=before)throw new Exception("Tag data changed beyond reference relocation: "+file);
    verified++;
   }
  }
  foreach(var pair in hashes)if(Digest(File.ReadAllBytes(pair.Key))!=pair.Value)throw new Exception("Original tags changed while copying. Retry after closing other tag editors.");
  VerifyCopiedScenario(source,target);
  using(var original=new TagFile(TagPath.FromPathAndType(source,"scnr*")))
  using(var copy=new TagFile(TagPath.FromPathAndType(target,"scnr*"))) {
   var counts=original.Fields.OfType<TagFieldBlock>().ToDictionary(b=>b.FieldName,b=>b.Elements.Count);
   foreach(var b in copy.Fields.OfType<TagFieldBlock>())if(counts[b.FieldName]!=b.Elements.Count)throw new Exception("Scenario block count changed: "+b.FieldName);
   File.WriteAllText(j.output,js.Serialize(new{version=1,ok=true,scenario=target,source=source,copied_files=copied.Count,verified_tags=verified,byte_preserved_camera_settings=bytePreserved,redirected_references=redirected,scenario_blocks=counts,originals_unchanged=true,missing_original_references=missing.ToArray(),shared_assets="Tags outside the source level folder remain shared references."}));
  }
 }
 static void ResolveScenery(Job j) {
  var wanted=new HashSet<string>((j.sources??new string[0]).Select(Safe),StringComparer.OrdinalIgnoreCase);
  var matches=new List<object>();var errors=new List<string>();string root=Path.Combine(kit,"tags");
  foreach(string file in Directory.EnumerateFiles(root,"*.scenery",SearchOption.AllDirectories)) {
   string source=file.Substring(root.Length+1);source=source.Substring(0,source.Length-8);
   try {
    using(var scenery=new TagFile(TagPath.FromPathAndType(source,"scen*"))) {
     var modelRef=References(scenery.Fields).FirstOrDefault(r=>r.FieldName=="model" && r.Path!=null);
     if(modelRef==null)continue;
     using(var model=new TagFile(TagPath.FromPathAndType(modelRef.Path.RelativePath,"hlmt*"))) {
      var refs=References(model.Fields).ToArray();
      var render=refs.FirstOrDefault(r=>r.FieldName=="render model" && r.Path!=null);
      if(render==null || !wanted.Contains(render.Path.RelativePath))continue;
      var collision=refs.FirstOrDefault(r=>r.FieldName=="collision model" && r.Path!=null);
      if(collision==null || !File.Exists(Path.Combine(root,collision.Path.RelativePath+".collision_model")))continue;
      matches.Add(new {render=render.Path.RelativePath,scenery=source,model=modelRef.Path.RelativePath,collision=collision.Path.RelativePath});
     }
    }
   }catch(Exception e){errors.Add(source+": "+e.Message);}
  }
  File.WriteAllText(j.output,js.Serialize(new{version=1,matches=matches,warnings=errors}));
 }
 static void ListSkies(Job j) {
  var items=new List<object>();var warnings=new List<string>();string root=Path.Combine(kit,"tags");
  foreach(var file in Directory.EnumerateFiles(Path.Combine(root,"levels"),"*.scenario",SearchOption.AllDirectories).OrderBy(x=>x)) {
   string scenario=file.Substring(root.Length+1);scenario=scenario.Substring(0,scenario.Length-9);
   try {using(var tag=new TagFile(TagPath.FromPathAndType(scenario,"scnr*"))) {
    var skies=F<TagFieldBlock>(tag.Fields,"skies");var refs=AllReferences(skies.Elements.Cast<TagElement>().SelectMany(e=>e.Fields).ToArray()).Where(x=>x.Path!=null).Select(x=>x.Path.RelativePathWithExtension).ToArray();
    if(refs.Length>0 && refs.All(x=>File.Exists(Path.Combine(root,x))))items.Add(new{scenario=scenario,name=Path.GetFileName(scenario),skies=refs});
   }}catch(Exception e){warnings.Add(scenario+": "+e.Message);}
  }
  File.WriteAllText(j.output,js.Serialize(new{version=1,items=items,warnings=warnings}));
 }
 static void RecoverSource(Job j) {
  using(var tag=new TagFile(TagPath.FromPathAndType(Safe(j.scenario),"sbsp*"))) {
   var stream=TagAlternateStreamType.TagImportInformation;
   if(!tag.DoesAlternateStreamExist(stream))throw new Exception("This BSP has no embedded source geometry. Original source files are required to rebuild it.");
   var fields=((TagElement)tag.GetAlternateStream(stream)).Fields;
   var files=F<TagFieldBlock>(fields,"files");var items=new List<object>();
   string folder=Path.GetDirectoryName(Path.GetFullPath(j.output));
   Directory.CreateDirectory(folder);
   for(int i=0;i<files.Elements.Count;i++) {
    var f=files.Elements[i].Fields;string name=F<TagFieldElementLongString>(f,"path").Data;
    if(!name.EndsWith(".ass",StringComparison.OrdinalIgnoreCase))continue;
    byte[] zipped=F<TagFieldData>(f,"zipped data").GetData();
    string compressed="source-"+i+".zlib";
    // Never use embedded absolute/relative source names as output paths.
    using(var output=new FileStream(Path.Combine(folder,compressed),FileMode.CreateNew,FileAccess.Write))output.Write(zipped,0,zipped.Length);
    items.Add(new{source_path=name,compressed=compressed,size=I(f,"size"),crc32=unchecked((uint)I(f,"checksum"))});
   }
   if(items.Count==0)throw new Exception("This BSP contains no recoverable ASS source geometry.");
   var shaders=AllReferences(tag.Fields).Where(r=>r.Path!=null && r.Path.Extension.StartsWith("shader",StringComparison.OrdinalIgnoreCase)).Select(r=>r.Path.RelativePath).Distinct(StringComparer.OrdinalIgnoreCase).ToArray();
   File.WriteAllText(j.output,js.Serialize(new{version=1,source=j.scenario,files=items,shaders=shaders}));
  }
 }
 static void InspectBsp(Job j) {
  using(var tag=new TagFile(TagPath.FromPathAndType(Safe(j.scenario),"sbsp*"))) {
   var block=F<TagFieldBlock>(tag.Fields,"instanced geometry instances");var items=new List<object>();
   foreach(var e in block.Elements)items.Add(new{name=F<TagFieldElementStringID>(e.Fields,"name").Data,position=F<TagFieldElementArraySingle>(e.Fields,"position").Data,scale=F<TagFieldElementSingle>(e.Fields,"scale").Data,definition=F<TagFieldBlockIndex>(e.Fields,"instance definition").Value,vectors=e.Fields.OfType<TagFieldElementArraySingle>().ToDictionary(f=>f.FieldName,f=>f.Data)});
   var resources=F<TagFieldBlock>(S(tag.Fields,"resource interface"),"raw_resources");var defs=new List<object>();
   foreach(var r in resources.Elements)foreach(var d in F<TagFieldBlock>(S(r.Fields,"raw_items"),"instanced geometries definitions").Elements) {var c=S(d.Fields,"collision info");defs.Add(new{mesh_index=I(d.Fields,"mesh index"),vertices=F<TagFieldBlock>(c,"vertices").Elements.Count,surfaces=F<TagFieldBlock>(c,"surfaces").Elements.Count});}
   File.WriteAllText(j.output,js.Serialize(new{version=1,instances=items,definitions=defs}));
  }
 }
 static void Collision(Job j) {
  using(var tag=new TagFile(TagPath.FromPathAndType(Safe(j.scenario),"sbsp*"))) {
   var ri=S(tag.Fields,"resource interface");var resources=F<TagFieldBlock>(ri,"raw_resources");
   int expectedDefinition=-1;
   if(!String.IsNullOrEmpty(j.asset_name)) {
    var instances=F<TagFieldBlock>(tag.Fields,"instanced geometry instances");
    foreach(var inst in instances.Elements)if(F<TagFieldElementStringID>(inst.Fields,"name").Data==j.asset_name)expectedDefinition=F<TagFieldBlockIndex>(inst.Fields,"instance definition").Value;
    if(expectedDefinition<0)throw new Exception("Source map and editing-kit tag do not contain the same named instance: "+j.asset_name);
   }
   var meshes=new List<object>();
   foreach(var raw in resources.Elements) {
    var defs=F<TagFieldBlock>(S(raw.Fields,"raw_items"),"instanced geometries definitions");
    for(int definitionIndex=0;definitionIndex<defs.Elements.Count;definitionIndex++) {var def=defs.Elements[definitionIndex];if(I(def.Fields,"mesh index")!=j.section)continue;
     if(expectedDefinition>=0 && definitionIndex!=expectedDefinition)throw new Exception("Source map/tag geometry indices differ; collision was not guessed.");
     var c=S(def.Fields,"collision info");var vertices=F<TagFieldBlock>(c,"vertices");var edges=F<TagFieldBlock>(c,"edges");var surfaces=F<TagFieldBlock>(c,"surfaces");
     var points=vertices.Elements.Cast<TagElement>().Select(e=>F<TagFieldElementArraySingle>(e.Fields,"point").Data).ToArray();var faces=new List<int[]>();
     for(int si=0;si<surfaces.Elements.Count;si++) {
      var face=new List<int>();int first=(int)I(surfaces.Elements[si].Fields,"first edge"),edge=first;
      do {if(edge<0||edge>=edges.Elements.Count||face.Count>edges.Elements.Count)throw new Exception("Invalid collision edge loop");var f=edges.Elements[edge].Fields;bool left=I(f,"left surface")==si;face.Add((int)I(f,left?"start vertex":"end vertex"));edge=(int)I(f,left?"forward edge":"reverse edge");}while(edge!=first);
      if(face.Count>=3)faces.Add(face.ToArray());
     }
     meshes.Add(new{positions=points,faces=faces});
    }
   }
   if(meshes.Count!=1)throw new Exception("Could not uniquely match original collision definition; export is blocked until collision is supplied.");
   File.WriteAllText(j.output,js.Serialize(new{version=1,meshes=meshes,source=j.scenario,section=j.section}));Console.WriteLine("Original collision extracted");
  }
 }
}

