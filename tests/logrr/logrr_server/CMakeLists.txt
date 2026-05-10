find_package (logrr_server REQUIRED)
find_package (logrr_fs_output_channel REQUIRED)

include (logrr_server/configure)
include (logrr_fs_output_channel/configure)

create_logrr_server (ENTITY_NAME "LogrrServer"
                     OUTPUT_CHANNELS "logrr.LogrrFsOutputChannel"
                     LOG_LEVEL ${LOG_LEVEL}
                     RECV_CORE_LOGS
                     WRITE_TO_CORE ON)

create_logrr_fs_output_channel (ENTITY_NAME "LogrrFsOutputChannel"
                                SERVER_TARGET "logrr_server::LogrrServer"
                                VFS_CONN_ID "kl.VfsRamFs"
                                LOG_DIR "/var/log")
