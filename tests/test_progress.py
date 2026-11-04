import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from halo_bridge.progress import ToolProgress,tool_label,PreparationActivity

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

    def test_activity_retains_output_and_cpu_without_spinner_spam(self):
        with tempfile.TemporaryDirectory() as tmp,patch('halo_bridge.progress.time.monotonic') as clock:
            clock.return_value=0;messages=[]
            activity=PreparationActivity(Path(tmp)/'activity.log',messages.append)
            activity.stage(3,'Compile geometry and collision')
            log=Path(tmp)/'compiler.log';tool=ToolProgress('structure',log,activity)
            from types import SimpleNamespace
            process=SimpleNamespace(poll=lambda:None)
            samples=iter([(10,104857600),(12,104857600),(12,104857600)])
            tool.bind_process(process,lambda p:next(samples))
            log.write_text('Starting\ncreating initial planes...  0% \\\n',encoding='utf-8');tool()
            clock.return_value=2
            with log.open('a') as stream:stream.write('creating initial planes...  0% |\n')
            tool();self.assertIn('CPU: 100%',messages[-1]);self.assertIn('100 MB',messages[-1])
            clock.return_value=70;tool()
            self.assertIn('Little CPU activity',messages[-1]);self.assertIn('68s',messages[-1])
            self.assertIn('Time remaining: unknown',messages[-1])
            saved=activity.path.read_text(encoding='utf-8')
            self.assertEqual(saved.count('creating initial planes'),1)
            self.assertIn('Starting',saved);self.assertIn('Stage 3/5',saved)
            self.assertEqual(activity.current_log,str(log))
            self.assertEqual(activity.stage_number,3)

    def test_short_process_final_output_without_newline(self):
        with tempfile.TemporaryDirectory() as tmp:
            from types import SimpleNamespace
            activity=PreparationActivity(Path(tmp)/'activity.log',lambda _:None)
            log=Path(tmp)/'tool.log';log.write_bytes(b'last line without newline')
            tool=ToolProgress('structure',log,activity)
            tool.bind_process(SimpleNamespace(poll=lambda:0),lambda p:None)
            tool()
            self.assertIn('last line without newline',activity.path.read_text())

    def test_real_child_process_reporting(self):
        from halo_bridge.jobs import run_process
        with tempfile.TemporaryDirectory() as tmp:
            messages=[];activity=PreparationActivity(Path(tmp)/'activity.log',messages.append)
            log=Path(tmp)/'child.log'
            command='import time; print("starting",flush=True); end=time.monotonic()+1.3\nwhile time.monotonic()<end: pass\nprint("finished",flush=True)'
            result=run_process([sys.executable,'-c',command],log,status=ToolProgress('structure',log,activity))
            self.assertIn('finished',result)
            self.assertIn('finished',activity.path.read_text())
            self.assertTrue(any('CPU:' in m for m in messages))

if __name__=='__main__':unittest.main()
