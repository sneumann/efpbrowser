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

# Compile and Copy MassBank components

# restart Apache
service apache2 restart

cd efpbrowser

## During development: change into temporary branch
# git checkout addSVNserver

bash ./install-ubuntu.sh
