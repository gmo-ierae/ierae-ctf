#!/usr/bin/env bash
set -ex

python3 gen.py > dump
clang -O3 -march=native -static -fno-stack-protector -fcf-protection=none -flto -Wno-main main.c
while true; do
    python3 gen.py > dump
    clang -O3 -march=native -static -fno-stack-protector -fcf-protection=none -flto -Wno-main -o actual main.c
    cmp ./a.out ./actual && break
    mv ./actual ./a.out
done
SYMBOL_ADDR=$(nm -n ./a.out | grep main_inner | awk '{print $1}')
rm ./a.out
strip --strip-all ./actual
python3 gen.py "0x$SYMBOL_ADDR" > /dev/null
echo 'IERAE{AQ4A8f-CYIJ1gneQ_IxekeOQlA}' | ./actual