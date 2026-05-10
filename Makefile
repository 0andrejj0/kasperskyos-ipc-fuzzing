SDK_PREFIX := /opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102
SYSROOT := $(SDK_PREFIX)/sysroot-aarch64-kos
TOOLCHAIN_FILE := $(SDK_PREFIX)/toolchain/share/toolchain-aarch64-kos-clang.cmake
CMAKE := $(SDK_PREFIX)/toolchain/bin/cmake

# TESTS := base asan ubsan types_support handles logrr
TESTS := logrr
TESTS_BUILD_DIR := .build/tests

ARGS := -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
        -DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY \
        -DCMAKE_TOOLCHAIN_FILE=$(TOOLCHAIN_FILE) \
        -DCMAKE_INSTALL_PREFIX=$(SYSROOT) \
        -DCMAKE_SYSROOT=$(SYSROOT) \
        -DCMAKE_FIND_ROOT_PATH=$(SYSROOT) \
        -DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM=NEVER \
        -DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=BOTH \
        -DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=BOTH \
        -DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=BOTH \
        -DCMAKE_BUILD_TYPE=Release

.PHONY: init deps coverage_mapper runner tests $(TESTS) clean default

default:
	@echo "All targets:"
	@echo "  init"
	@echo "  deps"
	@echo "  coverage_mapper"
	@echo "  runner"
	@echo "  tests"
	@echo "  clean"

init:
	rm -rf deps/abseil-cpp
	rm -rf deps/fuzztest
	mkdir -p deps
	python3 -m venv .venv
	cd deps && git clone git@github.com:abseil/abseil-cpp.git && cd abseil-cpp && git checkout e72b94a2f257ba069ec0b99e557e9f1f6b9c1a3e && git apply ../patches/abseil-cpp.patch
	cd deps && git clone git@github.com:google/fuzztest.git && cd fuzztest && git checkout 170281ea00744c6075375b756fcfa4a1a5d9346a && git apply ../patches/fuzztest.patch

deps:
	mkdir -p .build/deps
	cd .build/deps && $(CMAKE) $(ARGS) ../../deps
	cd .build/deps && $(MAKE) && $(MAKE) install

coverage_mapper:
	mkdir -p .build/coverage_mapper
	cd .build/coverage_mapper && $(CMAKE) $(ARGS) ../../coverage_mapper
	cd .build/coverage_mapper && $(MAKE) && $(MAKE) install

runner:
	mkdir -p .build/runner
	cd .build/runner && $(CMAKE) $(ARGS) ../../runner
	cd .build/runner && $(MAKE) && $(MAKE) install

tests: $(TESTS)

$(TESTS):
	mkdir -p $(TESTS_BUILD_DIR)/$@
	cd $(TESTS_BUILD_DIR)/$@ && $(CMAKE) $(ARGS) -DSDK_PREFIX=$(SDK_PREFIX) -DSYSROOT=$(SYSROOT) $(CURDIR)/tests/$@
	cd $(TESTS_BUILD_DIR)/$@ && $(MAKE)

clean:
	@echo "Clean... .build"
	rm -rf .build
