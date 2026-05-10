find_package(precompiled_vfs REQUIRED)

set(ENTITIES
    precompiled_vfs::VfsRamFs
    Fuzzer
    logrr_server::LogrrServer
    logrr_fs_output_channel::LogrrFsOutputChannel)

build_kos_qemu_image(kos-qemu-image
    EINIT_ENTITY EinitQemu
    CONNECTIONS_CFG init.yaml.in
    SECURITY_PSL security.psl.in
    IMAGE_FILES ${ENTITIES})

add_custom_target(AlwaysBuild ALL)
add_dependencies(AlwaysBuild kos-qemu-image)
