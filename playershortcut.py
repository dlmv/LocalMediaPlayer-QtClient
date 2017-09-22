import os, sys

example = """
[Desktop Entry]
Type=Application
Name=Local Player
Version=1.0
Encoding=UTF-8
Terminal=false
Exec=python %PATH% %U
Icon=%ICONPATH%
"""[1:-1]

def create_linux_desktop(dirpath):
	path = os.path.join(dirpath, "player.py")
	iconpath = os.path.join(dirpath, "icon.png")
	data = example.replace("%PATH%", path).replace("%ICONPATH%", iconpath)
	with open("localplayer.desktop", "w") as f:
		f.write(data)
	os.system("desktop-file-install --dir=%s/.local/share/applications --rebuild-mime-info-cache localplayer.desktop" % os.path.expanduser("~"))



dirpath = os.getcwd()
create_linux_desktop(dirpath)
