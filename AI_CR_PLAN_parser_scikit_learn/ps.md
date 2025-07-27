# 命令行前缀缩短
PS1='\W\$ '
PS1='\[\e[32m\]\u\[\e[0m\]@\[\e[34m\]\W\[\e[0m\]\$ '
# 恢复
PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '

# 启动ubuntu的ipv4网卡
sudo dhclient ens33