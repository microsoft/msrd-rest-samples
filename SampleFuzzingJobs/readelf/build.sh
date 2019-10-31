# Build readelf with AFL
wget http://ftp.gnu.org/gnu/binutils/binutils-2.28.tar.gz -O /opt/binutils.tar.gz
rm -Rf /opt/binutils-2.28
tar -xvf /opt/binutils.tar.gz -C /opt
cd /opt/binutils-2.28
export CC=/opt/afl-2.42b/afl-gcc
export CXX=/opt/afl-2.42b/afl-g++
export AS=/opt/afl-2.42b/afl-as
./configure
make
