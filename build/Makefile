include Makefile.variables

export TMP_BUILD_DIR := output

# -----------------------------------------------------------------------------
# Target to create packages
# -----------------------------------------------------------------------------
all: help
.PHONY: all

help:
	@echo "Usage: make [devel] <redhat|suse|deb>"
.PHONY: help

redhat: \
	setup \
	redhat_rpm \

suse: \
	setup \
	suse_rpm \

devel:
	$(eval VERSION := $(shell git describe | sed -r "s/-/./g"))

setup:
	mkdir -p $(TMP_BUILD_DIR)/etc/$(PROJECT_NAME)/
	(cd ../ && python setup.py install --prefix=/usr --root=build/$(TMP_BUILD_DIR))
	cp ../system/common/$(PROJECT_NAME).conf $(TMP_BUILD_DIR)/etc/$(PROJECT_NAME)

redhat_rpm:
	mkdir -p $(TMP_BUILD_DIR)/lib/systemd/system/ $(TMP_BUILD_DIR)/etc/init/
	cp ../system/systemd/$(PROJECT_NAME)d.service $(TMP_BUILD_DIR)/lib/systemd/system/
	cp ../system/upstart/redhat/$(PROJECT_NAME)d.conf $(TMP_BUILD_DIR)/etc/init/

	mkdir -p $(RPMBUILD_DIR)/SOURCES
	cd $(TMP_BUILD_DIR) && tar -czf $(RPMBUILD_DIR)/SOURCES/$(PROJECT_NAME).tar.gz .
	rpmbuild -bb --target noarch $(PROJECT_NAME).spec \
		--define 'custom_version $(VERSION)' \
		--define 'custom_release $(RELEASE)' \
		--define 'project_name $(PROJECT_NAME)' \
		--define '_topdir $(RPMBUILD_DIR)' \

suse_rpm:
	mkdir -p $(TMP_BUILD_DIR)/etc/init.d/
	cp ../system/sysvinit/$(PROJECT_NAME)d $(TMP_BUILD_DIR)/etc/init.d/
	mkdir -p $(RPMBUILD_DIR)/SOURCES $(RPMBUILD_DIR)/BUILD $(RPMBUILD_DIR)/RPMS
	cd $(TMP_BUILD_DIR) && tar -czf $(RPMBUILD_DIR)/SOURCES/$(PROJECT_NAME).tar.gz .
	rpmbuild -bb --target noarch $(PROJECT_NAME).spec \
		--define 'custom_version $(VERSION)' \
		--define 'custom_release $(RELEASE)' \
		--define 'project_name $(PROJECT_NAME)' \
		--define '_topdir $(RPMBUILD_DIR)' \

deb:
	mkdir -p $(TMP_BUILD_DIR)/etc/$(PROJECT_NAME)/ $(TMP_BUILD_DIR)/etc/init/
	(cd ../ && python setup.py install --install-layout=deb --root=build/$(TMP_BUILD_DIR))
	cp ../system/upstart/debian/$(PROJECT_NAME)d.conf $(TMP_BUILD_DIR)/etc/init/
	cp ../system/common/$(PROJECT_NAME).conf $(TMP_BUILD_DIR)/etc/$(PROJECT_NAME)/
	cp -r ../build/DEBIAN $(TMP_BUILD_DIR)
	dpkg-deb -b $(TMP_BUILD_DIR) $(PROJECT_NAME)-$(VERSION)-$(RELEASE).noarch.deb
