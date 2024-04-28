# pyinstaller installer.spec  -y 
echo "Building JamTools DEB package..."
rm -rf package
mkdir -p package/opt
mkdir -p package/usr/share/applications
mkdir -p package/usr/share/icons/hicolor/scalable/apps

echo "Copying files to package directory..."
cp -r ../../dist/JamTools package/opt/JamTools
cp ../../icon.png package/usr/share/icons/hicolor/scalable/apps/icon.png
cp JamTools.desktop package/usr/share/applications

echo "Setting permissions..."
chmod +x package/opt/JamTools/JamTools

echo "Building DEB package..."
rm  jamtools_installer.deb
fpm -C package -s dir -t deb -n "jamtools" -v 0.1.0 -p jamtools_installer.deb
echo "Done!"
