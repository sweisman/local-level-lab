import json,os,sys,time
assert 'numpy' not in sys.modules and 'scipy' not in sys.modules
def evaluate(task,context):
    values=json.loads(context.input_path().read_text())['values'];i=task['payload']['i']
    context.charge(native_calls=1,packet_visits=3)
    context.charge(bound_calls=1,bound_steps=3)
    context.save('execution.json',dict(i=i,pid=os.getpid(),session=os.getsid(0)))
    if task['payload'].get('wait'):
        context.save('ready.json',dict(ready=True));deadline=time.monotonic()+15.
        while not (context.root/'release.json').exists():
            if time.monotonic()>deadline:raise RuntimeError('fixture handshake deadline')
            time.sleep(.01)
    time.sleep(task['payload'].get('delay',0.))
    assert 'numpy' not in sys.modules and 'scipy' not in sys.modules
    return dict(passed=True,scientific_decision='abstain',value=values[i]*values[i],numerical_imports=False)
