"""Progress based on real export counts and external-tool output, never estimated percentages."""
import time
from pathlib import Path

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
    def __call__(self):
        now=time.monotonic()
        if now-self.last_update<1:return
        self.last_update=now
        try:
            size=self.log.stat().st_size
            if size!=self.size:
                with self.log.open('rb') as stream:
                    stream.seek(max(0,size-4096));data=stream.read().decode('utf-8',errors='replace')
                lines=[line.strip() for line in data.replace('\r','\n').splitlines() if line.strip()]
                if lines:self.latest=lines[-1][:200]
                self.size=size;self.last_output=now
        except OSError:pass  # Halo may temporarily hold its log exclusively.
        elapsed=int(now-self.started);quiet=int(now-self.last_output)
        text=f'{self.label} | {elapsed//60:02}:{elapsed%60:02} elapsed'
        if self.latest:text+=f' | Last tool output ({quiet}s ago): {self.latest}'
        else:text+=' | Tool is running; waiting for progress output.'
        self.report(text)
