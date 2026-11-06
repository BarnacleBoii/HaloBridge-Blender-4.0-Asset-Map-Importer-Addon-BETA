using Reclaimer.Blam.Common;
using Reclaimer.Geometry;

// A region's permutations are alternatives, not additional pieces of a model.
internal static class ModelSelection {
 internal static ModelPermutation[] Select(ModelRegion region) {
  var choices=region.Permutations.Where(p=>p.Export).ToArray();
  if(choices.Length<=1 || choices.All(p=>p.IsInstanced))return choices;
  return new[]{choices.FirstOrDefault(p=>string.Equals(p.Name,"default",StringComparison.OrdinalIgnoreCase))??choices.FirstOrDefault(p=>string.Equals(p.Name,"base",StringComparison.OrdinalIgnoreCase))??choices[0]};
 }
 internal static object[] Apply(Model model) {
  var result=new List<object>();
  foreach(var region in model.Regions.Where(r=>r.Export)) {
   var available=region.Permutations.Where(p=>p.Export).ToArray();
   var selected=Select(region);
   foreach(var permutation in available)permutation.Export=selected.Contains(permutation);
   result.Add(new{region=region.Name,selected=selected.Select(p=>p.Name).ToArray(),available=available.Select(p=>p.Name).ToArray(),instanced=available.All(p=>p.IsInstanced)});
  }
  var owners=new HashSet<string>(model.Regions.SelectMany(r=>r.Permutations.Where(p=>p.Export&&!p.IsInstanced).Select(p=>r.Name+"\\"+p.Name)));
  foreach(var p in model.Regions.SelectMany(r=>r.Permutations).Where(p=>p.IsInstanced&&p.Export))
   if(p.CustomProperties.TryGetValue("permutation_name",out var value) && value is IEnumerable<string> names && names.Any())
    p.Export=names.Any(owners.Contains);
  return result.ToArray();
 }
 internal record Permutation(string name,int section,int count);
 internal record Region(string name,Permutation[] permutations);
 internal static object Audit(ICacheFile cache,bool reach) {
  var models=new List<object>();var errors=new List<object>();
  foreach(var tag in cache.TagIndex.Where(t=>t.ClassCode=="mode")) {
   try {
    Region[] regions;
    if(reach)regions=tag.ReadMetadata<Reclaimer.Blam.HaloReach.RenderModelTag>().Regions.Select(r=>new Region(r.Name.ToString(),r.Permutations.Select(p=>new Permutation(p.Name.ToString(),p.SectionIndex,p.SectionCount)).ToArray())).ToArray();
    else regions=tag.ReadMetadata<Reclaimer.Blam.Halo3.RenderModelTag>().Regions.Select(r=>new Region(r.Name.ToString(),r.Permutations.Select(p=>new Permutation(p.Name.ToString(),p.SectionIndex,p.SectionCount)).ToArray())).ToArray();
    models.Add(new{tag=tag.TagName,regions,has_alternatives=regions.Any(r=>r.permutations.Length>1)});
   }catch(Exception e){errors.Add(new{tag=tag.TagName,error=e.Message});}
  }
  return new{version=1,game=reach?"reach":"halo3",models,errors};
 }
}

