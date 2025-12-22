
from https://ssb22.user.srcf.net/notes/pconnect.html (also [mirrored on GitLab Pages](https://ssb22.gitlab.io/notes/pconnect.html) just in case)

# Connecting to a Psion PDA

(see also [Large-print notes on EPOC or Symbian](psion.md))

Psion PDAs use serial ports, which are rare on modern PCs. If you are not able to add an internal serial port, and don’t have an old PC (with a suitably-old distribution of Linux that runs on the hardware and has `plptools`), then you could use a USB-to-Serial converter.

If using a USB-to-Serial converter, you might find `plptools` does not fully work on recent Linux kernels/distributions (see below re Debian bug #601612), and problems may also occur if you try to compile it on a Mac. So here’s a way to set it up in an older distribution running in VirtualBox.

## USB-to-Serial with plptools in VirtualBox

I got it to work on MacOS 10.7.5 by running VirtualBox 4.3.4 with Debian 3.1 Sarge and its 0.12 plptools package. It did *not* work after upgrading to VirtualBox 4.3.40—kernel panics on the guest OS (`usb-ohci.h:464` with interrupt handler disabled and consequent hard lock) prevented backups from completing—but downgrading back to VirtualBox 4.3.4 was straightforward.

Setup:
1. Create a new VirtualBox instance called “Debian 3.1 Sarge” with 32M RAM and an IDE hard disk (not SATA)
2. After installing Debian 3.1 (from an old CD or [ISO file](http://cdimage.debian.org/mirror/cdimage/archive/3.1_r8/i386/iso-cd/)), manually edit the `sources.list` to `http://archive.debian.org/debian sarge main` (unless you have a full CD set), and `apt-get install plptools`
3. In `/etc/plptools.conf`, set `NCPD_ARGS` to `-s /dev/ttyUSB0` (leave plpnfsd and plpprintd off; it seems more robust to just use plpftp)
4. Halt and power off the virtual machine, then from the real machine do:

   `VBoxManage modifyvm "Debian 3.1 Sarge" --usb on`

    then do `VBoxManage list usbhost` to find your USB-Serial controller, and add it with:

   `VBoxManage usbfilter add 0 --target "Debian 3.1 Sarge" --name "USB Serial" --vendorid 067B --productid 2303`

   (these numbers are correct for a Prolific Technologies product; others may vary—you’ll need to look at the list)
5. Set up a port forwarding rule so you can connect to the virtual machine via SSH (which is more flexible than using its console all the time, and you can use e.g. `sshfs` to access its filesystem from the real machine):

   `VBoxManage modifyvm "Debian 3.1 Sarge" --natpf1 "guestssh,tcp,,8022,,22"`
6. You can now start the machine in the background with:

   `VBoxManage startvm "Debian 3.1 Sarge" --type headless`

   and “hibernate” it with:

   `VBoxManage controlvm "Debian 3.1 Sarge" savestate`
   * Sarge’s kernel ships with ACPI disabled, so you can’t use `acpipowerbutton` without further setup. A clean shutdown can be effected via log in and `halt`, then use `VBoxManage controlvm "Debian 3.1 Sarge" poweroff` after a delay but that’s prone to error. However, if you gave the machine only 32M of RAM then always using “hibernate” instead of shutdown should rarely be an issue. If it is, you could try halving the RAM allocation (to 16M) once setup is complete, but less than 32M wasn’t officially supported by Sarge and may result in more swapping.
7. Do `ssh -p 8022 localhost` to connect to the machine (when it is not hibernated). You might want to set up `.ssh/authorized_keys` and an `sshfs` mount, e.g.:

   `sshfs -o IdentityFile=/path/to/keyfile -o sshfs_sync -o port=8022 localhost: $HOME/sarge`

   `ssh -i /path/to/keyfile -p 8022 localhost`

   You might want to put these commands in a script, wrapped by the above `startvm` and `savestate` commands, but **make sure to unmount the sshfs before hibernating the virtual machine** (especially if you’re on a Mac—some versions of Mac FUSE can crash the kernel if you try to access a mount whose virtual machine has stopped). Some delay might be needed after the `startvm`, especially if the state has not been saved.
8. You should now be able to SSH in and use `plpftp`. As is normal with plptools, you might need to do `/etc/init.d/plptools restart` a few times and/or wait a while for things to stabilise after connecting the Psion.

It did *not* work for me to run Sarge chroot or forward-port its version of plptools, so it seems the kernel is part of the issue. (Debian bug #601612 reported a forward-port working with a QinHeng adapter but I couldn’t do it with a Prolific.) It is therefore necessary to run a whole virtual machine if you need to connect a Psion to a modern computer, but at least by modern virtual machine standards it’s a lightweight one.

## Revo power connector size

If the Revo’s internal batteries have severely lost capacity (and you are unable to perform the delicate replacement operation) then you might want to charge while away from power.

I was not able to measure the connector exactly, but it fits one that’s specified as:

Inside diameter - 1.4mm

Outside diameter - 3.5mm

Length - 10.0mm

and the original seems slightly fatter so I’m suspecting IEC 60130-10:1971 Type C (3.8mm).

The Revo’s specs say 500mA 6V DC +/- 10% so 5.4-6.6V. Some companies marketted 4*AA “external battery packs” but these required alkalines (4 AA NiCd or NiMH rechargeables are likely to produce only 4.8V; NiZns are within the specs but need a special charger, otherwise you’d need 5*1.2V with suitable holder and a charger that can take an *odd* number of batteries). A Revo *might* accept 4.8V for running but not charging, but this isn’t in the specs and I don’t know if it varies from unit to unit.

The 5mx/MC218 is more likely to have *screen* problems than battery problems (the 5’s screen cable was better than the 5mx’s although still not brilliant; some people fit replacement cables from ‘flexi’ etc; not sure about the Oregon Osaris but it ran EPOC 4 so I don’t know if it would work with Macro5 and keybLayout).

Copyright and Trademarks:
All material © Silas S. Brown unless otherwise stated.
Debian is a trademark owned by Software in the Public Interest, Inc.
Linux is the registered trademark of Linus Torvalds in the U.S. and other countries.
Mac is a trademark of Apple Inc.
Symbian was a trademark of the Symbian Foundation until its insolvency in 2022 and I was unable to find what happened to the trademark after that.
VirtualBox is a trademark registered by Oracle in various countries.
Any other [trademarks](https://ssb22.user.srcf.net/trademarks.html) I mentioned without realising are trademarks of their respective holders.
