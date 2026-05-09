# Kasperskyos IDL Test Generator

### Build and run:
##### 1. Install KasperskyOS SDK 1.4
```
# download deb package for qemu from https://os.kaspersky.ru/download-community-edition/
sudo dpkg-deb --extract KasperskyOS-Community-Edition-Qemu-1.4.0.102_ru.deb /
sudo chown -R $USER /opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102
```

##### 2. Install and build deps
```
make init
make deps
```

##### 3. Build libraries and tests
```
source .venv/bin/activate
pip install -e idl_to_fuzztest

make coverage_mapper
make runner
make tests
```

##### 4. Run tests

```
cd .build/tests/base/einit # or another test
/opt/KasperskyOS-Community-Edition-Qemu-1.4.0.102/toolchain/bin/qemu-system-aarch64 -m 2048 -machine vexpress-a15,secure=on -cpu cortex-a57 -nographic -monitor none -smp 4 -nic user -serial stdio -kernel kos-qemu-image
```

##### 5. Develop your own test

