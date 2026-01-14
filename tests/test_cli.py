from utils.cli import parse_cli


def test_parse_cli_defaults(monkeypatch):
    # no arguments -> all flags False
    ns = parse_cli([])
    assert not ns.check_compat
    assert not ns.version
    assert not ns.debug


def test_parse_cli_flags():
    ns = parse_cli(["--check-compat", "--debug"])
    assert ns.check_compat
    assert not ns.version
    assert ns.debug

    ns2 = parse_cli(["-v"])
    assert ns2.version
