// MEMO: b=require
u0061=1;fs=b('fs');l=fs.readSync(0, new Uint8Array(10), 0, 10);if (l == 10) { process.stdout.write("Yes\n"); } else { process.stdout.write("No\n"); };process.exit(0);
