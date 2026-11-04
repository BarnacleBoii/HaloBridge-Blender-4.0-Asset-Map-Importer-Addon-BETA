"""Progress based on real export counts and external-tool output, never estimated percentages."""
import time
import re
import threading
from pathlib import Path


class PreparationActivity:
    """Disk-backed event history; worker threads never access Blender data."""
    def __init__(self,path,report):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text('HaloBridge preparation activity\nStage counts are not time estimates. Compiler percentages apply only to the named substep.\n',encoding='utf-8')
        self.report=report;self.started=time.monotonic();self.ended=None;self.phase='Validation';self.stage_number=0;self.current_log=''
        self.recent=();self.revision=0;self.last='';self.lock=threading.Lock()
    def event(self,message):
        message=str(message)
        with self.lock:
            if message==self.last:return
            self.last=message;elapsed=int(time.monotonic()-self.started)
            line=f'[{elapsed//60:02}:{elapsed%60:02}] {message}'
            with self.path.open('a',encoding='utf-8') as stream:stream.write(line+'\n')
            self.recent=(*self.recent[-5:],line);self.revision+=1
    def __call__(self,message):
        self.event(message);self.report(message)
    def heartbeat(self,message):self.report(message)
    def stage(self,number,name):
        self.stage_number=number
        self.phase=f'Stage {number}/5 — {name}'
        self(self.phase)

LIGHTING=[('faux_data_sync','Collecting lighting geometry'),('faux_farm_begin','Setting up test lighting')]
for key,label in [('dillum','Direct lighting'),('pcast','Photon tracing'),('radest','Radiosity'),('extillum','External illumination'),('fgather','Final gathering')]:
    LIGHTING.extend([('faux_farm_'+key,label),('faux_farm_'+key+'_merge','Merging '+label.lower())])
LIGHTING.extend([('faux_farm_finish','Finishing lightmaps'),('faux-build-linear-textures-with-intensity-from-quadratic','Converting lightmap textures'),('faux-compress-scenario-bitmaps-dxt5','Compressing lightmaps'),('faux-farm-compression-merge','Finalizing lighting')])


def tool_label(command):
    for index,(key,label) in enumerate(LIGHTING,1):
        if command==key:return f'Test lighting {index}/{len(LIGHTING)}: {label}'
    return {'structure':'Compiling level geometry and collision','bitmaps':'Compiling converted textures'}.get(command,command)


class ToolProgress:
    def __init__(self,command,log,report):
        self.label=tool_label(command);self.log=Path(log);self.report=report
        self.started=time.monotonic();self.last_update=-float('inf');self.last_output=self.started
        self.size=0;self.latest=''
        self.process=None;self.sample=None;self.cpu=None;self.observed=None;self.activity='CPU activity: waiting for a sample.'
        self.last_event='';self.pending=b''
        if hasattr(report,'current_log'):report.current_log=str(self.log)
        if hasattr(report,'event'):report.event('Compiler log: '+str(self.log))
    def bind_process(self,process,sample):
        self.process=process;self.sample=sample
    def __call__(self):
        now=time.monotonic()
        if now-self.last_update<1:return
        self.last_update=now
        try:
            size=self.log.stat().st_size
            if size!=self.size:
                with self.log.open('rb') as stream:
                    stream.seek(self.size if size>=self.size else 0);data=stream.read()
                data=self.pending+data.replace(b'\r',b'\n')
                parts=data.split(b'\n');self.pending=parts.pop()
                if self.process is not None and self.process.poll() is not None and self.pending:
                    parts.append(self.pending);self.pending=b''
                lines=[line.decode('utf-8',errors='replace').strip() for line in parts if line.strip()]
                for line in lines:
                    self.latest=line[:200]
                    # Rotating spinner characters are activity, not new progress.
                    meaningful=re.sub(r'\s+[|/\\-]\s*$','',line)
                    if meaningful!=self.last_event:
                        self.last_event=meaningful
                        if hasattr(self.report,'event'):self.report.event(self.label+': '+meaningful)
                self.size=size;self.last_output=now
        except OSError:pass  # Halo may temporarily hold its log exclusively.
        elapsed=int(now-self.started);quiet=int(now-self.last_output)
        if self.sample:
            sample=self.sample(self.process)
            if sample:
                cpu,memory=sample
                if self.cpu is not None:
                    busy=max(0,cpu-self.cpu)/max(.001,now-self.observed)*100
                    self.activity=f'CPU: {busy:.0f}% of one core | Memory: {memory/1048576:.0f} MB'
                    if busy<1:self.activity+=' | Little CPU activity; this alone does not prove a stall.'
                self.cpu=cpu;self.observed=now
        text=f'{self.label} | {elapsed//60:02}:{elapsed%60:02} elapsed\n{self.activity}'
        if self.latest:text+=f' | Last tool output ({quiet}s ago): {self.latest}'
        else:text+=' | Tool is running; waiting for progress output.'
        text+='\nTime remaining: unknown. Any % above is this compiler substep only.'
        if quiet>=60:text+='\nNo new compiler output for '+str(quiet)+'s; activity does not guarantee successful completion.'
        getattr(self.report,'heartbeat',self.report)(text)
