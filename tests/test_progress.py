import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from halo_bridge.progress import ToolProgress,tool_label

class ProgressTests(unittest.TestCase):
    def test_silent_tool_and_latest_output(self):
        with tempfile.TemporaryDirectory() as tmp,patch('halo_bridge.progress.time.monotonic') as clock:
            clock.return_value=100
            log=Path(tmp)/'tool.log';messages=[]
            progress=ToolProgress('faux_farm_dillum',log,messages.append)
            progress();self.assertIn('3/16',messages[-1]);self.assertIn('waiting for progress output',messages[-1])
            log.write_text('Starting\r25 percent\n',encoding='utf-8')
            clock.return_value=105;progress()
            self.assertIn('00:05 elapsed',messages[-1]);self.assertIn('25 percent',messages[-1])
            clock.return_value=115;progress();self.assertIn('10s ago',messages[-1])
            self.assertIn('16/16',tool_label('faux-farm-compression-merge'))

if __name__=='__main__':unittest.main()
