original_dir=$(dirname "$(readlink -f "$0")")
echo "Original directory: $original_dir"
echo "Building JamTools executable..."
cd ${original_dir}
cd ../../ && pyinstaller installer.spec  -y 
cd ${original_dir}

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
file="jamtools_installer.deb"
if [ -f "$file" ]; then
    rm "$file"
    echo "File $file is deleted."

fi
version=$(grep -m 1 'VERSON' ../../installer.spec | cut -d'"' -f2)
echo "Version: $version"
fpm -C package -s dir -t deb -n "jamtools" -v "${version}" -p "$file"
echo "Done!"
