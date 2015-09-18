# install a MassBank Dev machine
export DEBIAN_FRONTEND=noninteractive

# Freshen package index
apt-get update

# Set timezone
echo "Europe/Berlin" | tee /etc/timezone
dpkg-reconfigure --frontend noninteractive tzdata

# set locale
export LANGUAGE=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

locale-gen en_US.UTF-8 de_DE.UTF-8
dpkg-reconfigure locales


# install Apache
apt-get install -y apache2 unzip apache2-utils

# install GIT
apt-get install -y git-core

# install editors
apt-get install -y nano joe

# install lynx
apt-get install -y lynx

# download latest version of efpbrowse
git clone https://github.com/sneumann/efpbrowser

cat >/etc/apache2/sites-available/efp.conf <<EOF
<Directory "/var/www/html/efp/cgi-bin">
  Options +ExecCGI
  AddHandler cgi-script .cgi .pl
</Directory>
EOF

# enable required apache modules
a2enmod cgi
a2ensite efp

# restart Apache
service apache2 restart

cd efpbrowser

# efpBrowser requires patched PIL not in Ubuntu
# apt-get install -y python-imaging python-lxml python-mysqldb python-matplotlib

apt-get install -y python-lxml python-mysqldb python-matplotlib
apt-get install -y python-pip 
apt-get build-dep -y python-imaging
apt-get install -y libjpeg62 libjpeg62-dev libfreetype6-dev

## From: http://askubuntu.com/questions/156484/how-do-i-install-python-imaging-library-pil
sudo ln -s /usr/lib/x86_64-linux-gnu/libz.so /usr/lib/libz.so
sudo ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib/libjpeg.so
sudo ln -s /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib/libfreetype.so
sudo ln -s /usr/include/freetype2 /usr/local/include/freetype

pip install /home/vagrant/efpbrowser/eFPbrowser-1.6.0/Imaging-1.1.6efp/


## Under efp create a cgi-bin directory. The contents of the zipped file 
## you receive are installed here. These files must be readable and executable 
## by Apache, so chmod 755 them.
sudo cp -avx /home/vagrant/efpbrowser/eFPbrowser-1.6.0/efp /var/www/html/efp
sudo chmod 755 /var/www/html/efp/cgi-bin

## Under cgi-bin, set up two directories called data and output.  data
## must be readable by Apache and should contain the .png, .tga and
## .xml files as specified above, as well as the microarray
## element-to-gene identifier lookup file.  output must be writeable
## by Apache processes, so chmod it appropriately.

sudo mkdir /var/www/html/efp/cgi-bin/output
sudo chgrp -R www-data /var/www/html/efp/cgi-bin/output
sudo chmod -R g+w /var/www/html/efp/cgi-bin/output

##  You will need to
## compile the modified PIL code in the Imaging-1.1.5 directory into a
## PIL directory under cgi-bin. The appropriate pilfonts directory
## should also be placed under the cgi-bin directory.

mkdir -p /var/www/html/efp/cgi-bin


## Might also require 
## apt-get install -y mafft

## And mview (which package ?!)


## 
## MySQL setup 
## 

# install mysql 
# ATTENTION: CUSTOMISE THE MYSQL PASSWORD FOR YOUR OWN INSTALLATION !!!
debconf-set-selections <<< 'mysql-server mysql-server/root_password password efp@2014'
debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password efp@2014'

apt-get install -y mysql-server mysql-client

cat >~/.my.cnf <<EOF
[client]
user=root
password="efp@2014"

[mysql]
user=root
password="efp@2014"
EOF


cat >/var/www/.my.cnf <<EOF
[client]
user=efpro
password="efp@2015"

[mysql]
user=efpro
password="efp@2015"
EOF

mysql --user=root <<EOF
CREATE DATABASE annotations_lookup;
CREATE DATABASE atgenexp;
EOF

cd samples-1.0
bzcat agi_annotation.sql.bz2 | mysql -u root annotations_lookup
bzcat at_agi_lookup.sql.bz2 | mysql -u root annotations_lookup
bzcat sample_data.sql.bz2 | mysql -u root atgenexp
cd ..

mysql --user=root <<EOF
CREATE USER 'efpro'@'localhost' IDENTIFIED BY 'efp@2015';

use annotations_lookup;
GRANT SELECT ON *.* TO 'efpro'@'localhost';

use atgenexp;
GRANT SELECT ON *.* TO 'efpro'@'localhost';
EOF
