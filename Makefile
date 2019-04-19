MAKEFILES = $(shell find . -maxdepth 3 -type f -name Makefile)
SUBDIRS   = $(filter-out ./,$(dir $(MAKEFILES)))

all:
	for dir in $(SUBDIRS); do \
			make -C $$dir all; \
	done