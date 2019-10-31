# Install and build gcc and AFL 2.42b
sudo apt install gcc autoconf automake g++
sudo apt install make
wget http://lcamtuf.coredump.cx/afl/releases/afl-2.42b.tgz -O afl-2.42b.tgz
sudo tar -xvf afl-2.42b.tgz -C /opt
cd /opt/afl-2.42b/
export AFL_NO_X86=1
sudo make
export CC=/opt/afl-2.42b/afl-gcc
export CXX=/opt/afl-2.42b/afl-g++
export AS=/opt/afl-2.42b/afl-as