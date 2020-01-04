from mnamer.argument import ArgParser


def test_invalid_arguments(e2e_main):
    result = e2e_main("--blablabla")
    assert result.code == 1
    assert result.out == "invalid arguments: --blablabla"


def test_no_arguments(e2e_main):
    result = e2e_main()
    assert result.code == 1
    assert result.out == ArgParser().usage


def test_no_files_found(e2e_main):
    result = e2e_main("")
    assert result.code == 0
    assert result.out == "Starting mnamer\n" "no media files found"
