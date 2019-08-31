# -*- mode: ruby -*-
# vi: set ft=ruby :

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
        man-pages \
        vim \
        make \
        kernel-devel \
        selinux-policy-devel \
        libselinux-python3 \
        >/dev/null

      # we set to permissive to allow loading and working with reference policy as opposed to fedora's fork
      echo "Setting SELinux to Permissive Mode..."
      setenforce 0
    SHELL
  end
end
