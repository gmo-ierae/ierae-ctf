all:
	cargo build --release
	strip ./target/release/fortress --wildcard --strip-symbol '*fortress*'
	cp ./target/release/fortress ../challenge/fortress

clean:
	cargo clean

