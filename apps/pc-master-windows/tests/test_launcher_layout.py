"""Aceptación geométrica Tk en Windows: los botones no requieren maximizar."""
import importlib.util
import os
from pathlib import Path

import pytest


@pytest.mark.skipif(os.name!='nt',reason='Requiere Tk Windows')
@pytest.mark.parametrize('geometry',['800x600','960x720'])
def test_actions_remain_visible_when_form_overflows(geometry,monkeypatch,tmp_path):
    spec=importlib.util.spec_from_file_location('layout_launcher',Path(__file__).parents[1]/'pc_master.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module,'CONFIG_FILE',tmp_path/'settings.json')
    app=module.PcMasterApp()
    try:
        app.geometry(geometry)
        app.update()
        for button in app.controls_frame.winfo_children():
            top=button.winfo_rooty()-app.winfo_rooty()
            left=button.winfo_rootx()-app.winfo_rootx()
            assert 0<=top and top+button.winfo_height()<=app.winfo_height()
            assert 0<=left and left+button.winfo_width()<=app.winfo_width()
        canvas=app.form_canvas
        assert canvas.bbox('all')[3]>canvas.winfo_height()
        canvas.yview_moveto(1)
        app.update()
        assert canvas.yview()[0]>0
    finally:
        app.destroy()
