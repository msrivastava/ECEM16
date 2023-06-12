#!/usr/bin/env bash

apt-get update -y

apt-get install -y python3 python3-pip python3-dev
pip3 install -r /autograder/source/requirements.txt

#apt-get install -y wget

apt-get install -y iverilog

# JDK
wget https://download.java.net/java/GA/jdk14.0.1/664493ef4a6946b186ff29eb326336a2/7/GPL/openjdk-14.0.1_linux-x64_bin.tar.gz
tar xvf openjdk-14.0.1_linux-x64_bin.tar.gz 
mv jdk-14.0.1 /opt

tee /etc/profile.d/jdk14.sh <<EOF
export JAVA_HOME=/opt/jdk-14.0.1
export PATH=\$PATH:\$JAVA_HOME/bin
EOF

source /etc/profile.d/jdk14.sh

# JSON query
wget https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64
mv jq-linux64 /usr/local/bin/jq
chmod +x /usr/local/bin/jq