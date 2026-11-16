from pathlib import PureWindowsPath

import pytest


@pytest.mark.parametrize(
    "raw_path",
    [
        r"C:\Users\Cliente\Videos\audiencia.mp4",
        r"C:\Users\Cliente\Desktop\video teste.mp4",
        r"D:\Audiencias\processo-123.mp3",
        r"C:\Users\Cliente\Área de Trabalho\reunião.wav",
    ],
)
def test_windows_absolute_paths(raw_path):

    path = PureWindowsPath(raw_path)

    assert path.is_absolute()
    assert path.drive
    assert path.name
    assert path.suffix in [".mp4", ".mp3", ".wav"]


def test_windows_path_with_spaces():

    path = PureWindowsPath(
        r"C:\Users\Cliente\Meus Vídeos\Audiência 001.mp4"
    )

    assert path.name == "Audiência 001.mp4"

    assert path.parent.name == "Meus Vídeos"


def test_windows_path_with_special_characters():

    path = PureWindowsPath(
        r"C:\Users\Cliente\Documentos\Reunião nº 01.mp4"
    )

    assert path.name == "Reunião nº 01.mp4"


def test_windows_network_path():

    path = PureWindowsPath(
        r"\\Servidor\Compartilhado\audiencia.mp4"
    )

    assert path.is_absolute()

    assert path.name == "audiencia.mp4"

    assert path.suffix == ".mp4"


def test_windows_different_drives():

    path_c = PureWindowsPath(
        r"C:\Videos\video.mp4"
    )

    path_d = PureWindowsPath(
        r"D:\Audiencias\video.mp4"
    )

    assert path_c.drive == "C:"

    assert path_d.drive == "D:"