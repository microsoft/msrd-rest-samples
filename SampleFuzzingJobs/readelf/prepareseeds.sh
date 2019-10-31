# Limit to file under <43k.
# We assume the compressed file is sent using the 'direct-upload to MSRD' REST API
# which limits the size to 4MB at most.
# (Sending files via a URL does not have the limitation but has the disadvantage of requiring a storage account).
echo 'Preparing some ELF seeds'
rm -Rf /opt/seeds/
mkdir /opt/seeds
find /usr/bin/* -size -30k -type f -executable -exec readelf -h {} \; -exec cp {} /opt/seeds/ \;
for i in /opt/seeds/*; do mv $i $i.elf; done
tar -czvf elfseeds.tgz /opt/seeds/
ls -lisa *.tgz