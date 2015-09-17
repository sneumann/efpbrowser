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

apt-get install -y python-imaging python-lxml python-mysqldb python-matplotlib

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


