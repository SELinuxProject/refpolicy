# -*- mode: ruby -*-
# vi: set ft=ruby :

# Provisioning script to install the reference policy
$install_refpolicy = <<-SHELL
  # fail as soon as a command failed
  set -e

  # we set to permissive to allow loading and working with reference policy as opposed to fedora's fork
  echo "Setting SELinux to Permissive Mode..."
  setenforce 0

  # build the reference policy
  sudo -su vagrant make -C /vagrant bare
  sudo -su vagrant make -C /vagrant conf
  sudo -su vagrant make -C /vagrant all
  sudo -su vagrant make -C /vagrant validate
  sudo -s make -C /vagrant install
  sudo -s make -C /vagrant install-headers
  sudo -s semodule -s refpolicy -i /usr/share/selinux/refpolicy/*.pp

  if ! (LANG=C sestatus -v | grep '^Loaded policy name:\s*refpolicy$' > /dev/null)
  then
      # Use the reference policy
      sed -i -e 's/^\\(SELINUXTYPE=\\).*/SELINUXTYPE=refpolicy/' /etc/selinux/config
  fi
  sudo -s semodule --reload

  # allow every domain to use /dev/urandom
  sudo -s semanage boolean --modify --on global_ssp

  # allow systemd-tmpfiles to manage every file
  sudo -s semanage boolean --modify --on systemd_tmpfiles_manage_all

  # make vagrant user use unconfined_u context
  if ! (sudo -s semanage login -l | grep '^vagrant' > /dev/null)
  then
      echo "Configuring SELinux context for vagrant user"
      sudo -s semanage login -a -s unconfined_u vagrant
  fi

  # label /vagrant as vagrant's home files
  if sudo -s semanage fcontext --list | grep '^/vagrant(/\.\*)?'
  then
      sudo -s semanage fcontext -m -s unconfined_u -t user_home_t '/vagrant(/.*)?'
  else
      sudo -s semanage fcontext -a -s unconfined_u -t user_home_t '/vagrant(/.*)?'
  fi

  # Update interface_info
  sudo -s sepolgen-ifgen -o /var/lib/sepolgen/interface_info -i /usr/share/selinux/refpolicy

  echo "Relabelling the system..."
  sudo -s restorecon -RF /

  echo "If this is a fresh install, you need to reboot in order to enable enforcing mode"
SHELL

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|
  # build a Fedora 30 VM
  config.vm.define "fedora" do |fedora|
    fedora.vm.box = "fedora/30-cloud-base"
    # assign a nice hostname
    fedora.vm.hostname = "selinux-fedora-devel"
    # give it a private internal IP address
    fedora.vm.network "private_network", type: "dhcp"

    # Customize the amount of memory on the VM
    fedora.vm.provider "virtualbox" do |vb|
      vb.memory = 1024
    end
    fedora.vm.provider "libvirt" do |lv|
      lv.memory = 1024
    end

    # Enable provisioning with a shell script. Additional provisioners such as
    # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
    # documentation for more information about their specific syntax and use.
    fedora.vm.provision "shell", run: "once", inline: <<-SHELL
      # get the man pages
      echo "Upgrading DNF and installing man pages..."
      dnf install -q -y man-pages >/dev/null
      dnf upgrade -q -y dnf >/dev/null

      # install a few packages to make this machine ready to go out of the box
      echo "Installing SELinux dev dependencies..."
      dnf install -q -y \
        bash-completion \
        gcc \
        man-pages \
        vim \
        make \
        kernel-devel \
        selinux-policy-devel \
        libselinux-python3 \
        >/dev/null

      # configure the reference policy for Fedora
      if ! grep '^DISTRO = fedora$' /vagrant/build.conf > /dev/null
      then
        echo 'DISTRO = fedora' >> /vagrant/build.conf
        echo 'SYSTEMD = y' >> /vagrant/build.conf
        echo 'UBAC = n' >> /vagrant/build.conf
      fi

      #{$install_refpolicy}
    SHELL
  end

  # build a Debian 10 VM
  config.vm.define "debian" do |debian|
    debian.vm.box = "debian/buster64"
    # assign a nice hostname
    debian.vm.hostname = "selinux-debian-devel"
    # give it a private internal IP address
    debian.vm.network "private_network", type: "dhcp"

    # Customize the amount of memory on the VM
    debian.vm.provider "virtualbox" do |vb|
      vb.memory = 1024
    end
    debian.vm.provider "libvirt" do |lv|
      lv.memory = 1024
    end

    # redefine the /vagrant as a synced folder (not an NFS share), in order to work cleanly on it
    config.vm.synced_folder ".", "/vagrant", disabled: true
    config.vm.synced_folder ".", "/vagrant", type: "rsync",
      rsync__exclude: ".vagrant/"

    debian.vm.provision "shell", run: "once", inline: <<-SHELL
      # install a few packages to make this machine ready to go out of the box
      echo "Installing SELinux dev dependencies..."
      export DEBIAN_FRONTEND=noninteractive
      apt-get -qq update
      apt-get install --no-install-recommends --no-install-suggests -qy \
        bash-completion \
        gcc \
        git \
        libc6-dev \
        vim \
        make \
        auditd \
        selinux-basics \
        selinux-policy-default \
        selinux-policy-dev \
        setools

      # If SELinux is not enabled, enable it with Debian's policy and ask for a reboot
      if ! selinuxenabled
      then
        echo "Enabling SELinux for Debian according to https://wiki.debian.org/SELinux/Setup"
        selinux-activate
        echo "Please reboot now in order to enable SELinux:"
        echo "vagrant reload debian && vagrant provision debian"
        exit
      fi

      # configure the reference policy for Debian
      if ! grep '^DISTRO = debian$' /vagrant/build.conf > /dev/null
      then
        echo 'DISTRO = debian' >> /vagrant/build.conf
        echo 'SYSTEMD = y' >> /vagrant/build.conf
        echo 'UBAC = n' >> /vagrant/build.conf
      fi

      #{$install_refpolicy}
    SHELL
  end
end
