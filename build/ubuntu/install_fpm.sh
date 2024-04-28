# install fpm
sudo apt install ruby
sudo apt-get install ruby-dev build-essential
gem sources --add https://mirrors.tuna.tsinghua.edu.cn/rubygems/ --remove https://rubygems.org/
gem sources -l
sudo gem install dotenv -v 2.8.1
sudo gem install fpm 

