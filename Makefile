.PHONY: init deps coverage_mapper generator tests clean

default:
	@echo "Доступные цели:"
	@echo "  init"
	@echo "  deps"
	@echo "  coverage_mapper"
	@echo "  generator"
	@echo "  tests"
	@echo "  clean"

init:
	rm -rf deps/abseil-cpp
	rm -rf deps/fuzztest
	mkdir -p deps
	cd deps && git clone git@github.com:abseil/abseil-cpp.git && cd abseil-cpp && git checkout e72b94a2f257ba069ec0b99e557e9f1f6b9c1a3e && git apply ../patches/abseil-cpp.patch
	cd deps && git clone git@github.com:google/fuzztest.git && cd fuzztest && git checkout 170281ea00744c6075375b756fcfa4a1a5d9346a && git apply ../patches/fuzztest.patch

deps:
	mkdir -p .build/deps
	cd .build/deps && /opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/toolchain/bin/cmake \
	    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
        -DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY \
        -DCMAKE_TOOLCHAIN_FILE=/opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/toolchain/share/toolchain-aarch64-kos-clang.cmake \
        -DCMAKE_INSTALL_PREFIX=/opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/sysroot-aarch64-kos \
        -DCMAKE_SYSROOT=/optKasperskyOS-Community-Edition-Qemu-1.4.0.102/sysroot-aarch64-kos \
        -DCMAKE_FIND_ROOT_PATH=/opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/sysroot-aarch64-kos \
        -DCMAKE_SYSROOT=/opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/sysroot-aarch64-kos \
        -DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM=NEVER \
        -DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=BOTH \
        -DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=BOTH \
        -DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=BOTH \
        -DCMAKE_BUILD_TYPE=Release \
		../../deps
	cd .build/deps && make && make install

coverage_mapper:
	mkdir -p .build/coverage_mapper
	cd .build/coverage_mapper && /opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/toolchain/bin/cmake \
	    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
        -DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY \
        -DCMAKE_TOOLCHAIN_FILE=/opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/toolchain/share/toolchain-aarch64-kos-clang.cmake \
        -DCMAKE_INSTALL_PREFIX=/opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/sysroot-aarch64-kos \
        -DCMAKE_SYSROOT=/optKasperskyOS-Community-Edition-Qemu-1.4.0.102/sysroot-aarch64-kos \
        -DCMAKE_FIND_ROOT_PATH=/opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/sysroot-aarch64-kos \
        -DCMAKE_SYSROOT=/opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/sysroot-aarch64-kos \
        -DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM=NEVER \
        -DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=BOTH \
        -DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=BOTH \
        -DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=BOTH \
        -DCMAKE_BUILD_TYPE=Release \
		../../coverage_mapper
	cd .build/coverage_mapper && make	&& make install

tests:
	mkdir -p .build/tests
	cd .build/tests && /opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/toolchain/bin/cmake \
	    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
        -DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY \
        -DCMAKE_TOOLCHAIN_FILE=/opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/toolchain/share/toolchain-aarch64-kos-clang.cmake \
        -DCMAKE_INSTALL_PREFIX=/opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/sysroot-aarch64-kos \
        -DCMAKE_SYSROOT=/optKasperskyOS-Community-Edition-Qemu-1.4.0.102/sysroot-aarch64-kos \
        -DCMAKE_FIND_ROOT_PATH=/opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/sysroot-aarch64-kos \
        -DCMAKE_SYSROOT=/opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/sysroot-aarch64-kos \
        -DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM=NEVER \
        -DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=BOTH \
        -DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=BOTH \
        -DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=BOTH \
        -DCMAKE_BUILD_TYPE=Release \
		../../tests
	cd .build/tests && make

generator:
	mkdir -p .build/generator
	cd .build/generator && cmake ../../generator && make

clean:
	@echo "Clean... .build"
	rm -rf .build
