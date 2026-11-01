import importlib.util
import json
import os
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest

spec=importlib.util.spec_from_file_location('setup_pc_master',Path(__file__).parents[1]/'setup_pc_master.py')
setup=importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


def test_existing_complete_installation_never_reprovisions(tmp_path,monkeypatch):
    data={}
    for name in ('operator_auth_file','tls_cert','tls_key','pgpassfile'):
        file=tmp_path/name
        file.write_text('existing-content')
        data[name]=str(file)
    data['state_dir']=str(tmp_path)
    settings=tmp_path/'settings.json'
    before=json.dumps(data)
    settings.write_text(before)
    monkeypatch.setattr(setup,'require_normal_user',lambda:None)
    database=Mock(side_effect=AssertionError('No debe modificar PostgreSQL'))
    monkeypatch.setattr(setup,'prepare_database',database)
    setup.provision('unused-admin','unused-operator','',Mock(),directory=tmp_path)
    assert settings.read_text()==before
    database.assert_not_called()


def test_partial_installation_is_not_overwritten(tmp_path,monkeypatch):
    file=tmp_path/'operator-auth.json'
    file.write_text('preserve-me')
    monkeypatch.setattr(setup,'require_normal_user',lambda:None)
    with pytest.raises(RuntimeError,match='incompleta'):
        setup.provision('password','password-valid-123','',Mock(),directory=tmp_path)
    assert file.read_text()=='preserve-me'


def test_elevated_process_is_refused_before_writing(tmp_path,monkeypatch):
    def reject():
        raise RuntimeError('sin Ejecutar como administrador')
    monkeypatch.setattr(setup,'require_normal_user',reject)
    with pytest.raises(RuntimeError,match='administrador'):
        setup.provision('admin','operator','',Mock(),directory=tmp_path/'new')
    assert not (tmp_path/'new').exists()


def test_invalid_operator_password_does_not_create_directory(tmp_path,monkeypatch):
    monkeypatch.setattr(setup,'require_normal_user',lambda:None)
    with pytest.raises(ValueError,match='12'):
        setup.provision('admin','short','',Mock(),directory=tmp_path/'new')
    assert not (tmp_path/'new').exists()


@pytest.mark.skipif(not os.environ.get('TEST_DATABASE_URL'),reason='Requiere PostgreSQL desechable')
def test_generated_scram_authenticates_in_postgresql():
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import conninfo_to_dict
    dsn=os.environ['TEST_DATABASE_URL']
    role='setup_test_'+uuid4().hex[:16]
    password='random-ascii-'+uuid4().hex
    with psycopg.connect(dsn,autocommit=True) as admin:
        try:
            admin.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(role),sql.Literal(setup.scram_verifier(password))))
            options=conninfo_to_dict(dsn)
            options.update(user=role,password=password)
            with psycopg.connect(**options) as reader:
                assert reader.execute('SELECT current_user').fetchone()[0]==role
        finally:
            admin.execute(sql.SQL('DROP ROLE IF EXISTS {}').format(sql.Identifier(role)))
