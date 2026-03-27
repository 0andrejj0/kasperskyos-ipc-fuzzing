# Kasperskyos IDL Test Generator

### Build and run:
##### 1. Install KasperskyOS SDK 1.4
```
# download deb package from https://os.kaspersky.ru/download-community-edition/
sudo dpkg-deb --extract KasperskyOS-Community-Edition-Qemu-1.4.0.102_ru.deb /
sudo chown -R $USER /opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102
```

##### 2. Install and build deps
```
make init
make deps
```

##### 3. Build and run tests
```
make coverage_mapper
make tests
cd .build/tests/base/einit # base is test name
/opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/toolchain/bin/qemu-system-aarch64 -m 2048 -machine vexpress-a15,secure=on -cpu cortex-a57 -nographic -monitor none -smp 4 -nic user -serial stdio -kernel kos-qemu-image
```
